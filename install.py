#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Installation Script
Setup and installation helper
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd: str, check: bool = True):
    """Run shell command"""
    print(f"🛠️  Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0 and check:
        print(f"❌ Command failed: {result.stderr}")
        sys.exit(1)
    
    return result

def main():
    """Main installation function"""
    print("""
    🌹 Blue Rose Bot Installation
    ============================
    """)
    
    # Check Python version
    print("🔍 Checking Python version...")
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 12):
        print(f"❌ Python 3.12+ required. Current: {python_version.major}.{python_version.minor}")
        sys.exit(1)
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if os.path.exists("requirements.txt"):
        run_command("pip install -r requirements.txt")
        print("✅ Dependencies installed")
    else:
        print("❌ requirements.txt not found")
        sys.exit(1)
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    directories = [
        "data",
        "data/bot",
        "data/groups",
        "data/users",
        "data/payments",
        "data/messages",
        "data/schedules",
        "logs",
        "backups",
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  📂 Created: {directory}")
    
    # Create __init__.py files
    print("\n📄 Creating package files...")
    packages = [
        "core",
        "engine",
        "storage",
        "intelligence",
        "moderation",
        "supremacy",
        "payments",
        "panels",
        "keyboards",
        "analytics",
        "failsafe",
        "database",
    ]
    
    for package in packages:
        init_file = Path(package) / "__init__.py"
        init_file.parent.mkdir(exist_ok=True)
        
        if not init_file.exists():
            with open(init_file, "w") as f:
                f.write(f'"""\nBlue Rose Bot - {package.title()} Module\n"""\n\n__version__ = "1.0.0"\n')
            print(f"  📄 Created: {init_file}")
    
    # Setup config
    print("\n⚙️  Setting up configuration...")
    config_file = Path("config.py")
    if config_file.exists():
        print("⚠️  config.py already exists. Please edit it manually.")
        print("\n📝 Please edit config.py and set:")
        print("   1. API_TOKEN = 'YOUR_BOT_TOKEN_HERE'")
        print("   2. BOT_OWNER_ID = YOUR_TELEGRAM_ID")
    else:
        print("❌ config.py not found. Please create it from config.example.py")
    
    # Test import
    print("\n🔧 Testing imports...")
    try:
        import config
        print("✅ config.py imports successfully")
    except Exception as e:
        print(f"❌ Import test failed: {e}")
    
    print("""
    
    🎉 Installation Complete!
    ========================
    
    Next steps:
    1. Get bot token from @BotFather
    2. Edit config.py with your token and ID
    3. Run the bot: python main.py
    
    For help:
    • Read README.md
    • Contact developer: @rana_editz_00
    
    🌹 Thank you for using Blue Rose Bot!
    """)

if __name__ == "__main__":
    main()