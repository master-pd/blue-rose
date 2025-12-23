#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Feature Override Panel
Bot admin feature override controls
"""

import logging
from typing import Dict, Any, Optional

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class FeatureOverridePanel:
    """Feature Override Panel for Bot Admin"""
    
    def __init__(self):
        self.config = Config
        
    async def get_group_features(self, group_id: int) -> Dict[str, Any]:
        """Get current feature status for a group"""
        try:
            group_services_path = self.config.DATA_DIR / "groups" / "group_services.json"
            group_services = JSONEngine.load_json(group_services_path, {})
            
            group_key = str(group_id)
            if group_key in group_services.get('group_services', {}):
                return group_services['group_services'][group_key]
            
            # Return default services
            return group_services.get('services', {})
        
        except Exception as e:
            logger.error(f"Failed to get group features: {e}")
            return {}
    
    async def override_feature(self, group_id: int, 
                             feature: str, 
                             enabled: bool,
                             admin_id: int) -> bool:
        """Override a feature for a group"""
        try:
            # Check admin permissions
            if not await self._validate_admin(admin_id):
                return False
            
            group_services_path = self.config.DATA_DIR / "groups" / "group_services.json"
            group_services = JSONEngine.load_json(group_services_path, {})
            
            group_key = str(group_id)
            
            # Initialize group services if not exists
            if 'group_services' not in group_services:
                group_services['group_services'] = {}
            
            if group_key not in group_services['group_services']:
                group_services['group_services'][group_key] = {}
            
            # Set feature override
            group_services['group_services'][group_key][feature] = {
                'enabled': enabled,
                'overridden': True,
                'overridden_by': admin_id,
                'overridden_at': self._get_timestamp(),
                'original_value': await self._get_original_value(feature)
            }
            
            # Save changes
            JSONEngine.save_json(group_services_path, group_services)
            
            logger.info(
                f"Feature {feature} {'enabled' if enabled else 'disabled'} "
                f"for group {group_id} by admin {admin_id}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to override feature: {e}")
            return False
    
    async def reset_feature(self, group_id: int, 
                          feature: str,
                          admin_id: int) -> bool:
        """Reset feature to default"""
        try:
            # Check admin permissions
            if not await self._validate_admin(admin_id):
                return False
            
            group_services_path = self.config.DATA_DIR / "groups" / "group_services.json"
            group_services = JSONEngine.load_json(group_services_path, {})
            
            group_key = str(group_id)
            
            # Check if override exists
            if (group_key in group_services.get('group_services', {}) and 
                feature in group_services['group_services'][group_key]):
                
                # Remove override
                del group_services['group_services'][group_key][feature]
                
                # If no overrides left, remove group entry
                if not group_services['group_services'][group_key]:
                    del group_services['group_services'][group_key]
                
                # Save changes
                JSONEngine.save_json(group_services_path, group_services)
                
                logger.info(
                    f"Feature {feature} reset to default "
                    f"for group {group_id} by admin {admin_id}"
                )
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to reset feature: {e}")
            return False
    
    async def get_all_overrides(self) -> Dict[str, Any]:
        """Get all feature overrides"""
        try:
            group_services_path = self.config.DATA_DIR / "groups" / "group_services.json"
            group_services = JSONEngine.load_json(group_services_path, {})
            
            return group_services.get('group_services', {})
        
        except Exception as e:
            logger.error(f"Failed to get overrides: {e}")
            return {}
    
    async def _validate_admin(self, admin_id: int) -> bool:
        """Validate admin permissions"""
        try:
            # Bot owner always has permission
            if admin_id == self.config.BOT_OWNER_ID:
                return True
            
            # Check if in bot admin list
            bot_admins_path = self.config.JSON_PATHS['bot_admins']
            bot_admins = JSONEngine.load_json(bot_admins_path, {})
            
            admin_ids = bot_admins.get('admins', [])
            return admin_id in admin_ids
        
        except Exception as e:
            logger.error(f"Failed to validate admin: {e}")
            return False
    
    async def _get_original_value(self, feature: str) -> bool:
        """Get original/default value for a feature"""
        try:
            group_services_path = self.config.DATA_DIR / "groups" / "group_services.json"
            group_services = JSONEngine.load_json(group_services_path, {})
            
            services = group_services.get('services', {})
            if feature in services:
                return services[feature].get('enabled', False)
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to get original value: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def create_override_report(self) -> str:
        """Create override report"""
        try:
            overrides = await self.get_all_overrides()
            
            if not overrides:
                return "No feature overrides found."
            
            report_lines = ["📋 **Feature Override Report**\n"]
            
            for group_id, features in overrides.items():
                report_lines.append(f"\n**Group ID:** `{group_id}`")
                
                for feature, config in features.items():
                    status = "✅ Enabled" if config.get('enabled') else "❌ Disabled"
                    admin = config.get('overridden_by', 'Unknown')
                    timestamp = config.get('overridden_at', 'Unknown')
                    
                    report_lines.append(
                        f"  • {feature}: {status} (by {admin} at {timestamp})"
                    )
            
            return "\n".join(report_lines)
        
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            return f"Error generating report: {e}"