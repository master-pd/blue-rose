#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Moderation Settings Panel
Group admin moderation configuration
"""

import logging
from typing import Dict, Any, Optional

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class ModerationSettings:
    """Moderation Settings for Group Admin"""
    
    def __init__(self):
        self.config = Config
        
    async def get_moderation_settings(self, group_id: int) -> Dict[str, Any]:
        """Get moderation settings for a group"""
        try:
            settings_path = self.config.DATA_DIR / "groups" / "moderation_settings.json"
            
            if not settings_path.exists():
                # Return default settings
                return self._get_default_settings()
            
            settings = JSONEngine.load_json(settings_path, {})
            group_key = str(group_id)
            
            # Get group-specific settings if exists
            group_settings = settings.get('groups', {}).get(group_key, {})
            
            if group_settings:
                # Merge with defaults
                default_settings = self._get_default_settings()
                return {**default_settings, **group_settings}
            
            # Return default settings
            return self._get_default_settings()
        
        except Exception as e:
            logger.error(f"Failed to get moderation settings: {e}")
            return self._get_default_settings()
    
    async def update_setting(self, group_id: int,
                           setting_key: str,
                           value: Any,
                           admin_id: int) -> bool:
        """Update a moderation setting"""
        try:
            # Validate setting key
            default_settings = self._get_default_settings()
            if setting_key not in default_settings:
                logger.error(f"Invalid setting key: {setting_key}")
                return False
            
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            settings_path = self.config.DATA_DIR / "groups" / "moderation_settings.json"
            
            # Load or create settings
            if settings_path.exists():
                settings = JSONEngine.load_json(settings_path, {})
            else:
                settings = {'groups': {}}
            
            group_key = str(group_id)
            
            # Initialize structures if not exists
            if 'groups' not in settings:
                settings['groups'] = {}
            
            if group_key not in settings['groups']:
                settings['groups'][group_key] = {}
            
            # Update setting
            settings['groups'][group_key][setting_key] = {
                'value': value,
                'updated_by': admin_id,
                'updated_at': self._get_timestamp()
            }
            
            # Save changes
            JSONEngine.save_json(settings_path, settings)
            
            logger.info(
                f"Moderation setting {setting_key} updated to {value} "
                f"for group {group_id} by admin {admin_id}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to update setting: {e}")
            return False
    
    async def reset_setting(self, group_id: int,
                          setting_key: str,
                          admin_id: int) -> bool:
        """Reset a setting to default"""
        try:
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            settings_path = self.config.DATA_DIR / "groups" / "moderation_settings.json"
            
            if not settings_path.exists():
                return False
            
            settings = JSONEngine.load_json(settings_path, {})
            group_key = str(group_id)
            
            # Check if setting exists
            if (group_key in settings.get('groups', {}) and 
                setting_key in settings['groups'][group_key]):
                
                # Delete setting
                del settings['groups'][group_key][setting_key]
                
                # Clean up empty structures
                if not settings['groups'][group_key]:
                    del settings['groups'][group_key]
                
                # Save changes
                JSONEngine.save_json(settings_path, settings)
                
                logger.info(
                    f"Moderation setting {setting_key} reset to default "
                    f"for group {group_id} by admin {admin_id}"
                )
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to reset setting: {e}")
            return False
    
    async def reset_all_settings(self, group_id: int, admin_id: int) -> bool:
        """Reset all settings to defaults"""
        try:
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            settings_path = self.config.DATA_DIR / "groups" / "moderation_settings.json"
            
            if not settings_path.exists():
                return False
            
            settings = JSONEngine.load_json(settings_path, {})
            group_key = str(group_id)
            
            # Remove group from settings
            if group_key in settings.get('groups', {}):
                del settings['groups'][group_key]
                
                # Save changes
                JSONEngine.save_json(settings_path, settings)
                
                logger.info(
                    f"All moderation settings reset to defaults "
                    f"for group {group_id} by admin {admin_id}"
                )
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to reset all settings: {e}")
            return False
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default moderation settings"""
        return {
            'max_warnings': 3,
            'mute_duration': 3600,  # 1 hour in seconds
            'ban_duration': 86400,  # 24 hours in seconds
            'anti_spam_threshold': 5,
            'anti_flood_threshold': 10,
            'anti_link_enabled': True,
            'anti_forward_enabled': False,
            'anti_bot_enabled': True,
            'warn_on_links': True,
            'mute_on_spam': True,
            'ban_on_flood': False,
            'delete_spam_messages': True,
            'delete_flood_messages': True,
            'notify_admins': True,
            'log_moderation': True,
            'allow_admin_bypass': False,
            'raid_protection': True,
            'raid_threshold': 5,
            'raid_time_window': 10,  # seconds
            'require_captcha': False,
            'captcha_timeout': 300,  # 5 minutes
            'welcome_message_enabled': True,
            'goodbye_message_enabled': True,
            'rules_enforced': True,
            'rules_message': "Please follow group rules.",
            'emergency_lock_enabled': True
        }
    
    async def _validate_group_admin(self, group_id: int, user_id: int) -> bool:
        """Validate group admin permissions"""
        try:
            # Bot owner and admins can always edit
            if (user_id == self.config.BOT_OWNER_ID or 
                user_id in self.config.BOT_ADMIN_IDS):
                return True
            
            # Check group admins
            group_admins_path = self.config.DATA_DIR / "groups" / "group_admins.json"
            group_admins = JSONEngine.load_json(group_admins_path, {})
            
            group_key = str(group_id)
            admins = group_admins.get('groups', {}).get(group_key, {}).get('admins', [])
            
            return user_id in admins
        
        except Exception as e:
            logger.error(f"Failed to validate group admin: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def get_setting_description(self, setting_key: str) -> str:
        """Get description for a setting"""
        descriptions = {
            'max_warnings': 'Maximum warnings before action',
            'mute_duration': 'Mute duration in seconds',
            'ban_duration': 'Ban duration in seconds',
            'anti_spam_threshold': 'Messages per minute for spam detection',
            'anti_flood_threshold': 'Messages per second for flood detection',
            'anti_link_enabled': 'Enable anti-link protection',
            'anti_forward_enabled': 'Enable anti-forward protection',
            'anti_bot_enabled': 'Enable anti-bot protection',
            'warn_on_links': 'Warn users posting links',
            'mute_on_spam': 'Mute users for spam',
            'ban_on_flood': 'Ban users for flooding',
            'delete_spam_messages': 'Delete spam messages automatically',
            'delete_flood_messages': 'Delete flood messages automatically',
            'notify_admins': 'Notify admins of moderation actions',
            'log_moderation': 'Log all moderation actions',
            'allow_admin_bypass': 'Allow admins to bypass restrictions',
            'raid_protection': 'Enable raid protection',
            'raid_threshold': 'New members per second for raid detection',
            'raid_time_window': 'Time window for raid detection (seconds)',
            'require_captcha': 'Require captcha for new members',
            'captcha_timeout': 'Captcha timeout in seconds',
            'welcome_message_enabled': 'Enable welcome messages',
            'goodbye_message_enabled': 'Enable goodbye messages',
            'rules_enforced': 'Enforce group rules',
            'rules_message': 'Rules message to display',
            'emergency_lock_enabled': 'Enable emergency lockdown'
        }
        
        return descriptions.get(setting_key, "No description available")
    
    async def create_settings_report(self, group_id: int) -> str:
        """Create moderation settings report for group"""
        try:
            settings = await self.get_moderation_settings(group_id)
            
            report_lines = ["🛡️ **Moderation Settings Report**\n"]
            report_lines.append(f"**Group ID:** `{group_id}`\n")
            
            # Group settings by category
            categories = {
                'Warnings & Actions': [
                    'max_warnings', 'mute_duration', 'ban_duration',
                    'warn_on_links', 'mute_on_spam', 'ban_on_flood'
                ],
                'Spam & Flood Protection': [
                    'anti_spam_threshold', 'anti_flood_threshold',
                    'delete_spam_messages', 'delete_flood_messages'
                ],
                'Content Filtering': [
                    'anti_link_enabled', 'anti_forward_enabled', 'anti_bot_enabled'
                ],
                'Security & Protection': [
                    'raid_protection', 'raid_threshold', 'raid_time_window',
                    'require_captcha', 'captcha_timeout', 'emergency_lock_enabled'
                ],
                'Notifications & Logging': [
                    'notify_admins', 'log_moderation'
                ],
                'Messages & Rules': [
                    'welcome_message_enabled', 'goodbye_message_enabled',
                    'rules_enforced', 'rules_message'
                ],
                'Permissions': [
                    'allow_admin_bypass'
                ]
            }
            
            for category, setting_keys in categories.items():
                report_lines.append(f"**{category}:**")
                
                for key in setting_keys:
                    if key in settings:
                        value = settings[key]
                        description = await self.get_setting_description(key)
                        
                        # Format value nicely
                        if isinstance(value, bool):
                            display_value = "✅ Enabled" if value else "❌ Disabled"
                        elif isinstance(value, int) and key.endswith('_duration'):
                            hours = value // 3600
                            minutes = (value % 3600) // 60
                            display_value = f"{hours}h {minutes}m"
                        elif key == 'rules_message':
                            display_value = value[:50] + "..." if len(value) > 50 else value
                        else:
                            display_value = str(value)
                        
                        report_lines.append(f"  • {key}: {display_value}")
                
                report_lines.append("")
            
            return "\n".join(report_lines)
        
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            return f"Error generating report: {e}"