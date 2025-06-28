#!/usr/bin/env python3
"""
Administrator privileges helper for Windows.
"""

import sys
import os
import ctypes
import subprocess

def is_admin():
    """Check if the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin_restart():
    """Restart the current script with administrator privileges."""
    if is_admin():
        print("✅ Already running as administrator")
        return True
    else:
        print("🔒 Administrator privileges required for global hotkeys")
        print("🚀 Attempting to restart with admin privileges...")
        
        try:
            # Get the current script path
            script_path = os.path.abspath(sys.argv[0])
            
            # Use UAC to restart with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                f'"{script_path}"', 
                None, 
                1
            )
            return True
        except Exception as e:
            print(f"❌ Failed to restart as administrator: {e}")
            return False

def print_admin_instructions():
    """Print instructions for running as administrator."""
    print("=" * 60)
    print("🔒 ADMINISTRATOR PRIVILEGES REQUIRED")
    print("=" * 60)
    print("Global hotkeys on Windows require administrator privileges.")
    print()
    print("📋 SOLUTIONS:")
    print("1. Close this app and restart as administrator:")
    print("   - Right-click on PowerShell/Command Prompt")
    print("   - Select 'Run as administrator'")
    print("   - Navigate to your project folder")
    print("   - Run the app again")
    print()
    print("2. In VS Code:")
    print("   - Close VS Code")
    print("   - Right-click on VS Code icon")
    print("   - Select 'Run as administrator'")
    print("   - Open your project and run the app")
    print()
    print("3. Alternative: Use the app without global hotkeys")
    print("   - The text display window will still work")
    print("   - Use Win+Space to open it manually")
    print("=" * 60)

def check_and_handle_admin():
    """Check admin privileges and handle accordingly."""
    if is_admin():
        print("✅ Running with administrator privileges - hotkeys should work")
        return True
    else:
        print("⚠️ Running without administrator privileges")
        print("🔑 Global hotkeys (Ctrl+1, Ctrl+2, etc.) will NOT work")
        print()
        
        # Ask user what they want to do
        print("Choose an option:")
        print("1. Continue anyway (hotkeys disabled)")
        print("2. Show admin instructions")
        print("3. Try auto-restart as admin")
        
        try:
            choice = input("Enter choice (1-3): ").strip()
            
            if choice == "1":
                print("⚠️ Continuing with disabled hotkeys...")
                return False
            elif choice == "2":
                print_admin_instructions()
                return False
            elif choice == "3":
                if request_admin_restart():
                    print("🚀 Restarting as administrator...")
                    sys.exit(0)  # Exit current process
                else:
                    print("❌ Auto-restart failed")
                    print_admin_instructions()
                    return False
            else:
                print("❌ Invalid choice, continuing with disabled hotkeys")
                return False
                
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Cancelled by user")
            return False

def test_admin_functionality():
    """Test if we can actually use admin features."""
    if not is_admin():
        return False
        
    try:
        # Test if we can register a simple hotkey
        import keyboard
        
        def test_callback():
            pass
            
        # Try to register a hotkey
        hotkey_id = keyboard.add_hotkey('ctrl+shift+f12', test_callback)
        keyboard.remove_hotkey(hotkey_id)
        
        print("✅ Admin hotkey test successful")
        return True
        
    except Exception as e:
        print(f"❌ Admin hotkey test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Administrator Privileges Test")
    print("=" * 40)
    
    admin_status = is_admin()
    print(f"👤 Administrator: {admin_status}")
    
    if admin_status:
        print("✅ You have admin privileges")
        if test_admin_functionality():
            print("✅ Hotkey functionality should work")
        else:
            print("❌ Hotkey functionality test failed")
    else:
        print("⚠️ No admin privileges")
        print_admin_instructions() 