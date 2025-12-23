#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Configuration File
Centralized configuration for all modules
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# ============================================================================
# BOT CONFIGURATION
# ============================================================================
class Config:
    """Main Configuration Class"""
    
    # Bot Information
    BOT_NAME = "Blue Rose"
    BOT_USERNAME = "blue_rose_bot"  # Change this to your bot's username
    BOT_VERSION = "1.0.0"
    DEVELOPER = "RANA (MASTER)"
    DEVELOPER_CONTACT = "@rana_editz_00"
    
    # Telegram API Configuration
    API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # ⚠️ Replace with your actual token
    API_URL = "https://api.telegram.org/bot"
    
    # Bot Settings
    BOT_OWNER_ID = 123456789  # ⚠️ Replace with your Telegram ID
    BOT_ADMIN_IDS = []  # Additional global admin IDs
    
    # Path Configuration
    BASE_DIR = Path(__file__).parent.absolute()
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Create necessary directories
    for directory in [DATA_DIR, LOGS_DIR]:
        directory.mkdir(exist_ok=True)
    
    # Database Configuration
    USE_SQLITE = True
    SQLITE_DB_PATH = DATA_DIR / "blue_rose.db"
    
    # JSON Storage Paths
    JSON_PATHS = {
        'bot_info': DATA_DIR / "bot" / "bot_info.json",
        'bot_admins': DATA_DIR / "bot" / "bot_admins.json",
        'bot_settings': DATA_DIR / "bot" / "bot_settings.json",
        'groups': DATA_DIR / "groups" / "groups.json",
        'group_status': DATA_DIR / "groups" / "group_status.json",
        'users': DATA_DIR / "users" / "users.json",
        'plans': DATA_DIR / "payments" / "plans.json",
        'payment_requests': DATA_DIR / "payments" / "payment_requests.json",
        'memory_store': BASE_DIR / "intelligence" / "memory_store.json",
    }
    
    # Create subdirectories
    SUBDIRS = [
        DATA_DIR / "bot",
        DATA_DIR / "groups",
        DATA_DIR / "users",
        DATA_DIR / "payments",
        DATA_DIR / "messages",
        DATA_DIR / "schedules",
        BASE_DIR / "intelligence",
        BASE_DIR / "supremacy",
    ]
    
    for subdir in SUBDIRS:
        subdir.mkdir(exist_ok=True)
    
    # Feature Flags
    FEATURES = {
        'auto_reply': True,
        'moderation': True,
        'payments': True,
        'analytics': True,
        'intelligence': True,
        'supremacy': True,
    }
    
    # Payment Plans (in BDT)
    PAYMENT_PLANS = {
        'free': {'days': 30, 'price': 0, 'name': 'Free Trial'},
        'basic': {'days': 30, 'price': 60, 'name': '30 Days'},
        'standard': {'days': 90, 'price': 100, 'name': '90 Days'},
        'premium': {'days': 240, 'price': 200, 'name': '8 Months'},
    }
    
    # Rate Limiting
    RATE_LIMITS = {
        'messages_per_second': 20,
        'commands_per_minute': 30,
        'api_calls_per_minute': 50,
    }
    
    # Moderation Defaults
    MODERATION = {
        'max_warnings': 3,
        'mute_duration': 3600,  # 1 hour in seconds
        'ban_duration': 86400,  # 24 hours in seconds
        'anti_spam_threshold': 5,
        'anti_flood_threshold': 10,
    }
    
    # Language Settings
    LANGUAGES = ['bn', 'en', 'ar', 'fr', 'ur', 'hi']
    DEFAULT_LANGUAGE = 'bn'
    
    # Logging Configuration
    LOGGING = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': LOGS_DIR / 'blue_rose.log',
        'max_size': 10485760,  # 10MB
        'backup_count': 5,
    }
    
    # Security Settings
    SECURITY = {
        'max_file_size': 5242880,  # 5MB
        'allowed_extensions': ['.json', '.txt', '.log'],
        'encryption_key': 'your-secret-key-here',  # ⚠️ Change this
    }
    
    # Time Settings
    TIMEZONE = 'Asia/Dhaka'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Cache Settings
    CACHE_TTL = 300  # 5 minutes in seconds
    
    # Bot Behavior
    HUMANIZE_DELAY = True
    MIN_DELAY = 0.5  # seconds
    MAX_DELAY = 2.0  # seconds
    
    # Emergency Settings
    EMERGENCY_LOCKDOWN = False
    READ_ONLY_MODE = False
    
    @classmethod
    def get_bot_info(cls) -> Dict[str, Any]:
        """Get bot information dictionary"""
        return {
            'name': cls.BOT_NAME,
            'username': cls.BOT_USERNAME,
            'version': cls.BOT_VERSION,
            'developer': cls.DEVELOPER,
            'contact': cls.DEVELOPER_CONTACT,
            'owner_id': cls.BOT_OWNER_ID,
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        if cls.API_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            issues.append("API_TOKEN is not set. Please update config.py")
        
        if cls.BOT_OWNER_ID == 123456789:
            issues.append("BOT_OWNER_ID is not set. Please update config.py")
        
        if not cls.DATA_DIR.exists():
            issues.append(f"DATA_DIR does not exist: {cls.DATA_DIR}")
        
        return issues
    
    @classmethod
    def initialize_defaults(cls):
        """Initialize default JSON files if they don't exist"""
        from storage.json_engine import JSONEngine
        
        # Initialize bot info
        bot_info_path = cls.JSON_PATHS['bot_info']
        if not bot_info_path.exists():
            default_bot_info = cls.get_bot_info()
            JSONEngine.save_json(bot_info_path, default_bot_info)
        
        # Initialize bot admins
        bot_admins_path = cls.JSON_PATHS['bot_admins']
        if not bot_admins_path.exists():
            default_admins = {
                'owner_id': cls.BOT_OWNER_ID,
                'admins': cls.BOT_ADMIN_IDS,
                'added_by': cls.BOT_OWNER_ID,
                'added_at': datetime.now().isoformat()
            }
            JSONEngine.save_json(bot_admins_path, default_admins)
        
        # Initialize bot settings
        bot_settings_path = cls.JSON_PATHS['bot_settings']
        if not bot_settings_path.exists():
            default_settings = {
                'features': cls.FEATURES,
                'rate_limits': cls.RATE_LIMITS,
                'moderation': cls.MODERATION,
                'security': cls.SECURITY,
                'last_updated': datetime.now().isoformat()
            }
            JSONEngine.save_json(bot_settings_path, default_settings)
        
        # Initialize other JSON files with empty structures
        empty_files = [
            cls.JSON_PATHS['groups'],
            cls.JSON_PATHS['group_status'],
            cls.JSON_PATHS['users'],
            cls.JSON_PATHS['plans'],
            cls.JSON_PATHS['payment_requests'],
        ]
        
        for file_path in empty_files:
            if not file_path.exists():
                JSONEngine.save_json(file_path, {})

# Global config instance
config = Config()

# Import datetime for initialization
from datetime import datetime

# Initialize on import
config.initialize_defaults()

if __name__ == "__main__":
    # Validate configuration when run directly
    issues = config.validate_config()
    if issues:
        print("Configuration Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid!")