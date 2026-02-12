#!/usr/bin/env python3
"""
MME Report Sender - UV Compatible (Updated for Date Subfolders)
Scans SE Folder/*/YYYYMMDD/ → sends files to Telegram
"""
import sys
import time
from pathlib import Path
from datetime import datetime
import requests

# Load token
try:
    from config import BOT_TOKEN
except ImportError:
    print("❌ config.py missing")
    input("\nPress Enter to exit...")
    sys.exit(1)

if not BOT_TOKEN or " " in BOT_TOKEN:
    print(f"❌ Invalid BOT_TOKEN: '{BOT_TOKEN}'")
    print("   → Must be format: 123456789:ABCxyz (NO spaces)")
    input("\nPress Enter to exit...")
    sys.exit(1)

BASE_FOLDER = Path(__file__).parent
SE_FOLDER_PARENT = BASE_FOLDER / "SE Folder"
TODAY = datetime.now().strftime("%Y%m%d")  # Auto-detect today's date subfolder

def parse_folder_name(folder_name):
    """
    Parse folder name: "A04_SE_8130874985_Uy Naro"
    Returns: (area, role, chat_id, name) or None if invalid
    """
    parts = folder_name.strip().split('_')
    if len(parts) < 4:
        return None
    
    area, role, chat_id, *name_parts = parts
    
    if not chat_id.isdigit():
        return None
    
    name = ' '.join(name_parts)
    return {
        "area": area,
        "role": role,
        "chat_id": chat_id,
        "name": name,
        "display_name": f"{name} ({role})"
    }

def get_se_folders_with_date_subfolders():
    """
    Scan SE Folder/ for valid folders → then look INSIDE for TODAY's date subfolder
    Returns list of {path, name, chat_id, role, date_subfolder}
    """
    if not SE_FOLDER_PARENT.exists():
        print(f"❌ Missing folder: {SE_FOLDER_PARENT.name}")
        print("   Run create_se_folders.py first to generate SE folders")
        return []
    
    folders = []
    for item in SE_FOLDER_PARENT.iterdir():
        if not item.is_dir():
            continue
        
        parsed = parse_folder_name(item.name)
        if not parsed:
            continue
        
        # Look for today's date subfolder INSIDE the SE folder
        date_subfolder = item / TODAY
        if not date_subfolder.exists() or not any(date_subfolder.iterdir()):
            continue  # Skip if no date subfolder or it's empty
        
        folders.append({
            "path": item,
            "date_subfolder": date_subfolder,
            "name": parsed["display_name"],
            "chat_id": parsed["chat_id"],
            "role": parsed["role"],
            "area": parsed["area"]
        })
    
    return folders

def send_file(filepath, chat_id):
    """Send file to Telegram chat with retry logic"""
    for attempt in range(2):
        try:
            # CRITICAL FIX: Removed extra spaces after /bot
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
            with open(filepath, 'rb') as f:
                files = {'document': (filepath.name, f)}
                data = {
                    'chat_id': chat_id,
                    'caption': f"📄 {filepath.name}\n📅 {datetime.now():%Y-%m-%d %H:%M}"
                }
                resp = requests.post(url, files=files, data=data, timeout=30)
            
            if resp.status_code == 200 and resp.json().get('ok'):
                return True, None
            
            error = resp.json().get('description', 'Unknown error')
            if attempt == 0:
                time.sleep(2)
            else:
                return False, error
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
            else:
                return False, str(e)
    return False, "Max retries exceeded"

def main():
    start_time = time.time()
    print("="*60)
    print("🚀 MME REPORT SENDER (WITH DATE SUBFOLDERS)")
    print("="*60)
    print(f"\n📅 Sending reports for date: {TODAY}")
    print(f"📁 Scanning: {SE_FOLDER_PARENT.name}/*/ {TODAY} /\n")
    
    se_folders = get_se_folders_with_date_subfolders()
    if not se_folders:
        print(f"❌ No folders found with '{TODAY}' subfolder!")
        print(f"   → Run sort_reports.py first to organize files")
        print(f"   → Or check if today's date is {TODAY}")
        input("\nPress Enter to exit...")
        return
    
    print(f"✅ Found {len(se_folders)} folders with reports:\n")
    for f in se_folders:
        files = [x for x in f["date_subfolder"].iterdir() 
                 if x.is_file() and x.stat().st_size > 5000]
        role_icon = "👤" if f["role"] == "SE" else "⚕️" if f["role"] == "DR" else "❓"
        print(f"   {role_icon} {f['name']:30s} (ID: {f['chat_id']:12s}) → {len(files)} file(s)")
    print()
    
    results, total_sent, total_failed = [], 0, 0
    se_timings = []
    
    for folder in se_folders:
        se_start = time.time()
        sent, failed = [], []
        files = [x for x in folder["date_subfolder"].iterdir() 
                 if x.is_file() and x.stat().st_size > 5000]
        
        if files:
            print(f"📤 Sending to {folder['name']} (ID: {folder['chat_id']})...")
            for file in files:
                success, error = send_file(file, folder["chat_id"])
                if success:
                    sent.append(file.name)
                    total_sent += 1
                    print(f"   ✓ {file.name}")
                else:
                    failed.append({"name": file.name, "error": error})
                    total_failed += 1
                    print(f"   ✗ {file.name} → {error}")
        else:
            print(f"⚠️  {folder['name']}: No valid files (>5KB) in {TODAY} folder")
        
        se_duration = time.time() - se_start
        se_timings.append({"name": folder["name"], "duration": se_duration})
        results.append({
            "name": folder["name"],
            "chat_id": folder["chat_id"],
            "role": folder["role"],
            "sent": sent,
            "failed": failed
        })
        print()
    
    # Generate report
    total_duration = time.time() - start_time
    timestamp = datetime.now()
    report = [
        f"✅ MME REPORT DELIVERY - {timestamp:%Y-%m-%d %H:%M:%S}",
        "="*60,
        f"Date processed  : {TODAY}",
        f"Folders scanned : {len(se_folders)}",
        f"Files sent      : {total_sent} | Failed: {total_failed}",
        f"Total time      : {total_duration:.2f} seconds",
        "="*60,
        ""
    ]
    
    for timing in se_timings:
        report.append(f"⏱️  {timing['name']:30s}: {timing['duration']:.2f} sec")
    report.append("")
    
    for r in results:
        role_icon = "👤" if r["role"] == "SE" else "⚕️" if r["role"] == "DR" else "❓"
        report.append(f"{role_icon} {r['name']} (ID: {r['chat_id']})")
        if r["sent"]:
            report.append(f"   ✓ Sent ({len(r['sent'])}):")
            for f in r["sent"]:
                report.append(f"      • {f}")
        if r["failed"]:
            report.append(f"   ✗ Failed ({len(r['failed'])}):")
            for f in r["failed"]:
                report.append(f"      • {f['name']} → {f['error']}")
        report.append("")
    
    report.append("="*60)
    report.append(f"📊 SUMMARY: {total_sent} sent | {total_failed} failed | {total_duration:.2f}s total")
    report_text = "\n".join(report)
    print(report_text)
    
    log_path = BASE_FOLDER / f"LOG_{timestamp:%Y%m%d_%H%M%S}.txt"
    log_path.write_text(report_text, encoding="utf-8")
    print(f"\n📄 Log saved: {log_path.name}")
    
    if total_failed:
        print(f"\n⚠️  {total_failed} failure(s) — check log above")
    else:
        print("\n✨ All files delivered successfully!")
    
    input("\n✅ Done! Press Enter to close...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")