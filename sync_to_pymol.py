"""
Sync pymol-ai-assistant to PyMOL installation directory
"""

import shutil
import sys
from pathlib import Path

def find_pymol_plugin_dir():
    """Find PyMOL plugin directory"""
    # Common installation paths
    possible_paths = [
        Path.home() / "AppData" / "Local" / "Schrodinger" / "PyMOL2" / "lib" / "site-packages" / "pmg_tk" / "startup" / "pymol-ai-assistant",
        Path("C:/Program Files/Schrodinger/PyMOL2/lib/site-packages/pmg_tk/startup/pymol-ai-assistant"),
        Path("C:/ProgramData/Schrodinger/PyMOL2/lib/site-packages/pmg_tk/startup/pymol-ai-assistant"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def sync_files():
    """Sync files to PyMOL directory"""
    pymol_dir = find_pymol_plugin_dir()
    
    if not pymol_dir:
        print("[ERROR] PyMOL installation directory not found")
        print("Please manually specify the path, for example:")
        print("  python sync_to_pymol.py C:/Users/xxx/AppData/Local/Schrodinger/PyMOL2/...")
        return False
    
    print(f"[OK] Found PyMOL plugin directory: {pymol_dir}")
    
    # Current directory (development directory)
    src_dir = Path(__file__).parent
    
    # Files to sync
    files_to_sync = [
        "ai_chat_gui.py",
        "log_manager.py", 
        "config_manager.py",
        "pymol_tools.py",
        "__init__.py",
    ]
    
    print(f"\nStarting file sync...")
    for filename in files_to_sync:
        src = src_dir / filename
        dst = pymol_dir / filename
        
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  [OK] {filename}")
        else:
            print(f"  [WARN] {filename} not found")
    
    print(f"\n[OK] Sync complete! Please restart PyMOL to apply changes.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Manual path specified
        custom_path = Path(sys.argv[1])
        if custom_path.exists():
            print(f"Using specified path: {custom_path}")
        else:
            print(f"Path does not exist: {custom_path}")
    else:
        sync_files()
