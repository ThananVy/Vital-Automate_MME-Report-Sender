#!/usr/bin/env python3
"""
Diagnostic Analyzer - SAFE PREVIEW ONLY
Scans Incoming Reports → shows where files WOULD be sorted (no actual copying)
"""
import sys
from pathlib import Path
from datetime import datetime

BASE_FOLDER = Path(__file__).parent
INCOMING_FOLDER = BASE_FOLDER / "Incoming Reports"
SE_FOLDER_PARENT = BASE_FOLDER / "SE Folder"
TODAY = datetime.now().strftime("%Y%m%d")

def extract_name_from_filename(filename):
    """Extract SE name from filename like 'A04_Uy Naro.xlsx' → 'Uy Naro'"""
    stem = Path(filename).stem
    parts = stem.split('_', 1)
    if len(parts) == 2:
        return parts[1].strip()
    return stem.strip()

def find_best_match(se_name, se_folders):
    """
    Find best folder match using substring search.
    Returns (folder_name, confidence_score) where:
      confidence_score = 100 (exact name match)
                       = 80  (case-insensitive substring)
                       = 50  (partial word match)
                       = 0   (no match)
    """
    se_lower = se_name.lower()
    
    # Exact name match (highest confidence)
    for folder in se_folders:
        folder_parts = folder.split('_')
        if len(folder_parts) >= 4:
            folder_name = ' '.join(folder_parts[3:]).lower()
            if se_lower == folder_name:
                return folder, 100
    
    # Substring match (medium confidence)
    for folder in se_folders:
        if se_lower in folder.lower():
            return folder, 80
    
    # Partial word match (low confidence - risky!)
    for folder in se_folders:
        folder_lower = folder.lower()
        if any(word in folder_lower for word in se_lower.split()):
            return folder, 50
    
    return None, 0

def main():
    print("="*70)
    print("🔍 REPORT SORTING DIAGNOSTIC (PREVIEW ONLY - NO FILES MODIFIED)")
    print("="*70)
    print(f"\n📅 Today's date: {TODAY}")
    print(f"📥 Scanning: {INCOMING_FOLDER}")
    print(f"👥 Matching against: {SE_FOLDER_PARENT}\n")
    
    # Check folders exist
    if not INCOMING_FOLDER.exists():
        print(f"❌ ERROR: Folder missing → {INCOMING_FOLDER}")
        print("   → Create it and drop your report files inside first")
        input("\nPress Enter to exit...")
        return
    
    if not SE_FOLDER_PARENT.exists():
        print(f"⚠️  WARNING: SE Folder missing → {SE_FOLDER_PARENT}")
        print("   → Run create_se_folders.py first to generate SE folders")
        se_folders = []
    else:
        se_folders = [f.name for f in SE_FOLDER_PARENT.iterdir() if f.is_dir()]
        print(f"✅ Found {len(se_folders)} SE/DR folders in SE Folder/")
        if len(se_folders) <= 5:
            for f in se_folders:
                print(f"   • {f}")
        else:
            for f in se_folders[:3]:
                print(f"   • {f}")
            print(f"   • ... (+{len(se_folders)-3} more)")
        print()
    
    # Find report files
    report_files = list(INCOMING_FOLDER.glob("*.xlsx")) + list(INCOMING_FOLDER.glob("*.xls"))
    report_files = [f for f in report_files if f.stat().st_size > 1000]  # Skip tiny files
    
    if not report_files:
        print("⚠️  NO REPORT FILES FOUND in Incoming Reports/")
        print("   → Drop your pre-split .xlsx files there first")
        input("\nPress Enter to exit...")
        return
    
    print(f"📄 Found {len(report_files)} report file(s):\n")
    
    # Analyze each file
    analysis = []
    stats = {"matched": 0, "risky": 0, "unknown": 0}
    
    for filepath in sorted(report_files):
        se_name = extract_name_from_filename(filepath.name)
        best_match, confidence = find_best_match(se_name, se_folders) if se_folders else (None, 0)
        
        analysis.append({
            "filename": filepath.name,
            "size_kb": filepath.stat().st_size / 1024,
            "extracted_name": se_name,
            "matched_folder": best_match,
            "confidence": confidence
        })
        
        if confidence >= 80:
            stats["matched"] += 1
        elif confidence > 0:
            stats["risky"] += 1
        else:
            stats["unknown"] += 1
    
    # Show detailed preview
    print(f"{'FILE NAME':<35} {'EXTRACTED NAME':<25} {'MATCH RESULT'}")
    print("-"*70)
    
    for item in analysis:
        size_str = f"{item['size_kb']:.1f}KB"
        name_str = item['extracted_name']
        
        if item['confidence'] == 100:
            match_str = f"✅ EXACT → {item['matched_folder']}"
        elif item['confidence'] >= 80:
            match_str = f"✓ GOOD  → {item['matched_folder']}"
        elif item['confidence'] > 0:
            match_str = f"⚠️  RISKY → {item['matched_folder']} (partial match)"
        else:
            match_str = "❌ UNKNOWN (no match found)"
        
        print(f"{item['filename']:<35} {name_str:<25} {match_str}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*70)
    print(f"Total files analyzed : {len(analysis)}")
    print(f"✅ Good matches       : {stats['matched']}")
    print(f"⚠️  Risky matches      : {stats['risky']}  ← May need manual review")
    print(f"❌ Unknown SEs        : {stats['unknown']}")
    
    if stats["risky"] > 0 or stats["unknown"] > 0:
        print("\n⚠️  ACTION REQUIRED:")
        if stats["unknown"] > 0:
            print(f"   • {stats['unknown']} file(s) have NO matching SE folder")
            print(f"     → Check if SE exists in SE_List.xlsx Column J")
        if stats["risky"] > 0:
            print(f"   • {stats['risky']} file(s) have partial/risky matches")
            print(f"     → Verify folder names match SE names exactly")
    else:
        print("\n✅ All files matched cleanly — safe to run sort_reports.py")
    
    print("\n💡 NEXT STEPS:")
    print("   1. If UNKNOWN/RISKY counts > 0 → fix Excel SE_List.xlsx first")
    print("   2. Run: uv run .\\create_se_folders.py  (to sync folders)")
    print("   3. Then run: uv run .\\sort_reports.py")
    input("\n✅ Diagnostic complete. Press Enter to exit...")

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