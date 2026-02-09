#!/usr/bin/env python3
"""
SE Report Sender - Manual Trigger
Workflow:
  1. Drop files into SE_[Name]_[ID] folders
  2. Double-click run_sender.bat (or run this script)
  3. Get delivery report saved as LOG_YYYYMMDD_HHMMSS.txt
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import requests

# Load bot token from config.py
try:
    from config import BOT_TOKEN
except ImportError:
    print("❌ ERROR: config.py not found in this folder")
    input("\nPress Enter to exit...")
    sys.exit(1)

if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("❌ ERROR: BOT_TOKEN missing or invalid in config.py")
    print(f"   Current value: '{BOT_TOKEN}'")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Base folder = where this script lives
BASE_FOLDER = Path(__file__).parent

def get_se_folders():
    """Find all SE_Name_ID folders in base folder"""
    folders = []
    for item in BASE_FOLDER.iterdir():
        if item.is_dir() and item.name.startswith("SE_"):
            # Split: SE_Vanda_123456789 → ['SE', 'Vanda', '123456789']
            parts = item.name.split("_", 2)
            if len(parts) == 3:
                folders.append({
                    "path": item,
                    "name": parts[1],
                    "chat_id": parts[2]
                })
    return folders

def is_valid_file(filepath):
    """Skip temp/blank files"""
    if filepath.name.startswith("~") or filepath.name.startswith("."):
        return False
    if filepath.stat().st_size < 5000:  # Skip files under 5KB (likely blank)
        return False
    return True

def send_file(filepath, chat_id):
    """Send single file with retry logic"""
    for attempt in range(2):  # Retry once
        try:
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
                time.sleep(2)  # Wait before retry
            else:
                return False, error
                
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
            else:
                return False, str(e)
    return False, "Max retries exceeded"

def main():
    print("="*60)
    print("🚀 MME REPORT SENDER - MANUAL TRIGGER")
    print("="*60 + "\n")
    
    # Find SE folders
    se_folders = get_se_folders()
    if not se_folders:
        print("❌ No SE folders found!")
        print("   → Create folders like: SE_Vanda_123456789")
        print("   → Format: SE_[Name]_[TelegramID]")
        input("\nPress Enter to exit...")
        return False
    
    print(f"📁 Found {len(se_folders)} SE folders:\n")
    for f in se_folders:
        files = [x for x in f['path'].iterdir() if x.is_file() and is_valid_file(x)]
        print(f"   • {f['name']:15s} (ID: {f['chat_id']:12s}) → {len(files)} file(s)")
    print()
    
    # Process each SE
    results = []
    total_sent, total_failed = 0, 0
    
    for folder in se_folders:
        sent_files, failed_files = [], []
        valid_files = [x for x in folder['path'].iterdir() 
                      if x.is_file() and is_valid_file(x)]
        
        if valid_files:
            print(f"📤 Sending to {folder['name']} ({folder['chat_id']})...")
            for file in valid_files:
                success, error = send_file(file, folder['chat_id'])
                if success:
                    sent_files.append(file.name)
                    total_sent += 1
                    print(f"   ✓ {file.name}")
                else:
                    failed_files.append({"name": file.name, "error": error})
                    total_failed += 1
                    print(f"   ✗ {file.name} → {error}")
        else:
            print(f"⚠️  {folder['name']}: No valid files to send")
        
        results.append({
            "name": folder['name'],
            "chat_id": folder['chat_id'],
            "sent": sent_files,
            "failed": failed_files
        })
        print()
    
    # Generate report
    timestamp = datetime.now()
    report = [
        f"✅ MME REPORT DELIVERY - {timestamp:%Y-%m-%d %H:%M:%S}",
        "="*60,
        f"Total SEs processed: {len(se_folders)}",
        f"Files sent: {total_sent}",
        f"Files failed: {total_failed}",
        "="*60,
        ""
    ]
    
    for r in results:
        report.append(f"👤 {r['name']} (ID: {r['chat_id']})")
        if r['sent']:
            report.append(f"   ✓ Sent ({len(r['sent'])}):")
            for f in r['sent']:
                report.append(f"      • {f}")
        if r['failed']:
            report.append(f"   ✗ Failed ({len(r['failed'])}):")
            for f in r['failed']:
                report.append(f"      • {f['name']} → {f['error']}")
        report.append("")
    
    report.append("="*60)
    report.append(f"📊 SUMMARY: {total_sent} sent | {total_failed} failed")
    report_text = "\n".join(report)
    
    # Save log file in same folder
    log_name = f"LOG_{timestamp:%Y%m%d_%H%M%S}.txt"
    log_path = BASE_FOLDER / log_name
    log_path.write_text(report_text, encoding='utf-8')
    
    # Show report
    print(report_text)
    print(f"\n📄 Delivery log saved: {log_path}")
    
    if total_failed > 0:
        print(f"\n⚠️  {total_failed} file(s) failed — check log above for details")
    else:
        print("\n✨ All files delivered successfully!")
    
    input("\n✅ Done! Press Enter to close...")
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")