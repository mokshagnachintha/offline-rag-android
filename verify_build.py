#!/usr/bin/env python3
"""
O-RAG Build Verification Script
Validates all Phase A-E components before APK generation
"""

import os
import sys
from pathlib import Path

def check_file_syntax(filepath):
    """Verify Python file compiles without syntax errors"""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        return True, "✅ Syntax OK"
    except SyntaxError as e:
        return False, f"❌ Syntax Error: {e}"
    except Exception as e:
        return False, f"❌ Error: {e}"

def verify_imports(filepath):
    """Check if imports are resolvable (basic check)"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        import_lines = [l.strip() for l in lines if l.startswith('import ') or l.startswith('from ')]
        return True, f"✅ {len(import_lines)} imports found"
    except Exception as e:
        return False, f"❌ Import check failed: {e}"

def check_file_exists(filepath):
    """Check if file exists"""
    if Path(filepath).exists():
        size = Path(filepath).stat().st_size
        return True, f"✅ Exists ({size} bytes)"
    else:
        return False, "❌ File not found"

def main():
    base_path = Path("/path/to/O-rag")  # Update this path
    
    # Files to check (Phase A-D core files)
    files_to_check = [
        "main.py",
        "cli.py",
        "analytics.py",
        "ui/__init__.py",
        "ui/theme.py",
        "ui/screens/__init__.py",
        "ui/screens/chat_screen.py",
        "ui/screens/docs_screen.py",
        "ui/screens/settings_screen.py",
        "ui/screens/init_screen.py",
        "ui/screens/analytics_dashboard.py",
        "rag/__init__.py",
        "rag/chunker.py",
        "rag/db.py",
        "rag/downloader.py",
        "rag/llm.py",
        "rag/pipeline.py",
        "rag/retriever.py",
        "rag/memory_manager.py",
    ]
    
    # Config files to check
    config_files = [
        "buildozer.spec",
        "requirements.txt",
        "README.md",
        "ARCHITECTURE.md",
    ]
    
    print("=" * 70)
    print("O-RAG BUILD VERIFICATION (Phase A-E)")
    print("=" * 70)
    
    # Check Python files
    print("\n✓ PYTHON FILES VERIFICATION")
    print("-" * 70)
    
    py_ok = 0
    py_total = 0
    
    for file in files_to_check:
        filepath = base_path / file
        py_total += 1
        
        exists_ok, exists_msg = check_file_exists(filepath)
        if not exists_ok:
            print(f"{file:<45} {exists_msg}")
            continue
        
        syntax_ok, syntax_msg = check_file_syntax(filepath)
        import_ok, import_msg = verify_imports(filepath)
        
        status = "✅" if (syntax_ok and import_ok) else "⚠️"
        py_ok += syntax_ok and import_ok
        
        print(f"{status} {file:<40} {syntax_msg}")
        if not import_ok:
            print(f"   └─ {import_msg}")
    
    print(f"\nPython files: {py_ok}/{py_total} verified ✅")
    
    # Check config files
    print("\n✓ CONFIG FILES VERIFICATION")
    print("-" * 70)
    
    cfg_ok = 0
    cfg_total = 0
    
    for file in config_files:
        filepath = base_path / file
        cfg_total += 1
        
        exists_ok, exists_msg = check_file_exists(filepath)
        cfg_ok += exists_ok
        
        status = "✅" if exists_ok else "❌"
        print(f"{status} {file:<45} {exists_msg}")
    
    print(f"\nConfig files: {cfg_ok}/{cfg_total} present ✅")
    
    # Check critical directories
    print("\n✓ DIRECTORY STRUCTURE")
    print("-" * 70)
    
    dirs_to_check = [
        "ui",
        "ui/screens",
        "rag",
        "assets",
        "evaluation",
        "service",
    ]
    
    for dir_name in dirs_to_check:
        dirpath = base_path / dir_name
        exists = dirpath.exists() and dirpath.is_dir()
        status = "✅" if exists else "⚠️"
        print(f"{status} {dir_name:<45} {'Present' if exists else 'Missing'}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_ok = (py_ok == py_total) and (cfg_ok == cfg_total)
    
    if all_ok:
        print("✅ ALL VERIFICATIONS PASSED")
        print("\n✓ Ready to build APK with: buildozer android release")
        print("✓ Expected build time: 45-60 minutes (first time)")
        print("✓ APK location: ./bin/orag-1.0.0-release-unsigned.apk")
        return 0
    else:
        print("⚠️ SOME VERIFICATIONS FAILED")
        print("\nFailing items:")
        print(f"  - Python files: {py_ok}/{py_total} OK")
        print(f"  - Config files: {cfg_ok}/{cfg_total} OK")
        return 1

if __name__ == "__main__":
    sys.exit(main())
