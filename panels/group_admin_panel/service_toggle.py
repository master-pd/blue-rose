#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Service Toggle Panel
Group admin service toggle controls
"""

import logging
from typing import Dict, Any

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class ServiceTogglePanel:
    """Service Toggle Panel for Group Admin"""
    
    def __init__(self):
        self.config = Config
        
    async def get_available_services(self) -> Dict[str, Any]:
        """Get all available services"""
        try:
            group_services_path = self.config.DATA_DIR / "groups" / "group_services.json"
            group_services = JSONEngine.load_json(group_services_path, {})
            
            return group_services.get('services', {})
        
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return {}
    
    async def get_group_services(self, group_id: int) -> Dict[str, Any]:
        """Get current service status for a group"""
        try:
            group_services_path = self.config.DATA_DIR / "groups" / "group_services.json"
            group_services = JSONEngine.load_json(group_services_path, {})
            
            group_key = str(group_id)
            
            # Get group-specific services if exists
            group_services_data = group_services.get('group_services', {}).get(group_key, {})
            
            # Merge with default services
            default_services = group_services.get('services', {})
            result = {}
            
            for service, config in default_services.items():
                if service in group_services_data:
                    # Use group override
                    result[service] = group_services_data[service]
                else:
                    # Use default
                    result[service] = {
                        'enabled': config.get('enabled', False),
                        'description': config.get('description', ''),
                        'overridden': False
                    }
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to get group services: {e}")
            return {}
    
    async def toggle_service(self, group_id: int, 
                           service: str, 
                           enabled: bool,
                           admin_id: int) -> bool:
        """Toggle a service for a group"""
        try:
            # Check if service exists
            services = await self.get_available_services()
            if service not in services:
                logger.error(f"Service {service} not found")
                return False
            
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            group_services_path = self.config.DATA_DIR / "groups" / "group_services.json"
            group_services = JSONEngine.load_json(group_services_path, {})
            
            group_key = str(group_id)
            
            # Initialize structures if not exists
            if 'group_services' not in group_services:
                group_services['group_services'] = {}
            
            if group_key not in group_services['group_services']:
                group_services['group_services'][group_key] = {}
            
            # Update service
            group_services['group_services'][group_key][service] = {
                'enabled': enabled,
                'description': services[service].get('description', ''),
                'overridden': True,
                'updated_by': admin_id,
                'updated_at': self._get_timestamp()
            }
            
            # Save changes
            JSONEngine.save_json(group_services_path, group_services)
            
            logger.info(
                f"Service {service} {'enabled' if enabled else 'disabled'} "
                f"for group {group_id} by admin {admin_id}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to toggle service: {e}")
            return False
    
    async def toggle_all_services(self, group_id: int, 
                                enabled: bool,
                                admin_id: int) -> bool:
        """Toggle all services for a group"""
        try:
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            services = await self.get_available_services()
            results = []
            
            for service in services:
                result = await self.toggle_service(group_id, service, enabled, admin_id)
                results.append(result)
            
            return all(results)
        
        except Exception as e:
            logger.error(f"Failed to toggle all services: {e}")
            return False
    
    async def reset_all_services(self, group_id: int, admin_id: int) -> bool:
        """Reset all services to defaults"""
        try:
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            group_services_path = self.config.DATA_DIR / "groups" / "group_services.json"
            group_services = JSONEngine.load_json(group_services_path, {})
            
            group_key = str(group_id)
            
            # Remove group from overrides
            if group_key in group_services.get('group_services', {}):
                del group_services['group_services'][group_key]
                
                # Save changes
                JSONEngine.save_json(group_services_path, group_services)
                
                logger.info(
                    f"All services reset to defaults "
                    f"for group {group_id} by admin {admin_id}"
                )
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to reset services: {e}")
            return False
    
    async def _validate_group_admin(self, group_id: int, user_id: int) -> bool:
        """Validate group admin permissions"""
        try:
            # Bot owner and admins can always toggle
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
    
    async def create_service_status_report(self, group_id: int) -> str:
        """Create service status report for group"""
        try:
            services = await self.get_group_services(group_id)
            
            if not services:
                return "No services configured for this group."
            
            report_lines = ["🛠️ **Service Status Report**\n"]
            report_lines.append(f"**Group ID:** `{group_id}`\n")
            
            enabled_count = 0
            disabled_count = 0
            
            for service, config in services.items():
                status = "✅" if config.get('enabled') else "❌"
                overridden = " (Overridden)" if config.get('overridden') else ""
                description = config.get('description', '')
                
                report_lines.append(
                    f"{status} **{service}**{overridden}\n"
                    f"   {description}\n"
                )
                
                if config.get('enabled'):
                    enabled_count += 1
                else:
                    disabled_count += 1
            
            report_lines.append(f"\n**Summary:** {enabled_count} enabled, {disabled_count} disabled")
            
            return "\n".join(report_lines)
        
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            return f"Error generating report: {e}"