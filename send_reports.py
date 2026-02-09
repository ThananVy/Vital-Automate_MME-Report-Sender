#!/usr/bin/env python3
"""
MME Report Sender - UV Compatible
Drop files into SE_[Name]_[ID] folders → double-click run_sender.bat
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

def get_se_folders():
    folders = []
    for item in BASE_FOLDER.iterdir():
        if item.is_dir() and item.name.startswith("SE_"):
            parts = item.name.split("_", 2)
            if len(parts) == 3:
                folders.append({"path": item, "name": parts[1], "chat_id": parts[2]})
    return folders

def send_file(filepath, chat_id):
    for attempt in range(2):
        try:
            # FIXED: Removed extra spaces after /bot
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
    start_time = time.time()  # ⏱️ START TIMER
    print("="*60)
    print("🚀 MME REPORT SENDER")
    print("="*60 + "\n")
    
    se_folders = get_se_folders()
    if not se_folders:
        print("❌ No SE_* folders found!")
        print("   Create folders like: SE_Vanda_123456789")
        input("\nPress Enter to exit...")
        return
    
    print(f"📁 Found {len(se_folders)} SE folders:\n")
    for f in se_folders:
        files = [x for x in f["path"].iterdir() if x.is_file() and x.stat().st_size > 5000]
        print(f"   • {f['name']:15s} (ID: {f['chat_id']:12s}) → {len(files)} file(s)")
    print()
    
    results, total_sent, total_failed = [], 0, 0
    se_timings = []  # Track time per SE
    
    for folder in se_folders:
        se_start = time.time()
        sent, failed = [], []
        files = [x for x in folder["path"].iterdir() if x.is_file() and x.stat().st_size > 5000]
        
        if files:
            print(f"📤 Sending to {folder['name']} ({folder['chat_id']})...")
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
            print(f"⚠️  {folder['name']}: No valid files")
        
        se_duration = time.time() - se_start
        se_timings.append({"name": folder["name"], "duration": se_duration})
        results.append({"name": folder["name"], "chat_id": folder["chat_id"], "sent": sent, "failed": failed})
        print()
    
    # Generate report
    total_duration = time.time() - start_time  # ⏱️ END TIMER
    timestamp = datetime.now()
    report = [
        f"✅ MME REPORT DELIVERY - {timestamp:%Y-%m-%d %H:%M:%S}",
        "="*60,
        f"Total SEs processed: {len(se_folders)}",
        f"Files sent: {total_sent} | Failed: {total_failed}",
        f"Total execution time: {total_duration:.2f} seconds",
        "="*60,
        ""
    ]
    
    # Add per-SE timing details
    for timing in se_timings:
        report.append(f"⏱️  {timing['name']:15s}: {timing['duration']:.2f} sec")
    report.append("")
    
    for r in results:
        report.append(f"👤 {r['name']} (ID: {r['chat_id']})")
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
    
    # Save log
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