#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Message Editor Panel
Group admin message template editing
"""

import logging
from typing import Dict, Any, List, Optional

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class MessageEditor:
    """Message Editor for Group Admin"""
    
    def __init__(self):
        self.config = Config
        
    async def get_message_templates(self, message_type: str) -> Dict[str, Any]:
        """Get message templates by type"""
        try:
            if message_type not in ['welcome', 'goodbye', 'default', 'alerts', 'admin_only']:
                return {}
            
            file_path = self.config.DATA_DIR / "messages" / f"{message_type}.json"
            
            if not file_path.exists():
                # Return empty structure
                return {'templates': {}}
            
            templates = JSONEngine.load_json(file_path, {})
            return templates
        
        except Exception as e:
            logger.error(f"Failed to get message templates: {e}")
            return {'templates': {}}
    
    async def get_group_templates(self, group_id: int, 
                                message_type: str) -> Dict[str, Any]:
        """Get group-specific message templates"""
        try:
            # First get default templates
            default_templates = await self.get_message_templates(message_type)
            
            # Check for group overrides
            group_templates_path = self.config.DATA_DIR / "messages" / "group_templates.json"
            
            if not group_templates_path.exists():
                return default_templates
            
            group_templates = JSONEngine.load_json(group_templates_path, {})
            group_key = str(group_id)
            
            if (group_key in group_templates and 
                message_type in group_templates[group_key]):
                # Merge defaults with group overrides
                result = default_templates.copy()
                result['templates'].update(group_templates[group_key][message_type])
                result['group_override'] = True
                return result
            
            return default_templates
        
        except Exception as e:
            logger.error(f"Failed to get group templates: {e}")
            return {'templates': {}}
    
    async def update_template(self, group_id: int,
                            message_type: str,
                            template_name: str,
                            text: str,
                            parse_mode: str = "HTML",
                            variables: Optional[Dict] = None,
                            admin_id: int) -> bool:
        """Update a message template"""
        try:
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            # Validate parse mode
            if parse_mode not in ['HTML', 'Markdown', 'MarkdownV2']:
                parse_mode = "HTML"
            
            group_templates_path = self.config.DATA_DIR / "messages" / "group_templates.json"
            
            # Load or create group templates
            if group_templates_path.exists():
                group_templates = JSONEngine.load_json(group_templates_path, {})
            else:
                group_templates = {}
            
            group_key = str(group_id)
            
            # Initialize structures if not exists
            if group_key not in group_templates:
                group_templates[group_key] = {}
            
            if message_type not in group_templates[group_key]:
                group_templates[group_key][message_type] = {}
            
            # Update template
            group_templates[group_key][message_type][template_name] = {
                'text': text,
                'parse_mode': parse_mode,
                'variables': variables or {},
                'updated_by': admin_id,
                'updated_at': self._get_timestamp()
            }
            
            # Save changes
            JSONEngine.save_json(group_templates_path, group_templates)
            
            logger.info(
                f"Template {template_name} ({message_type}) updated "
                f"for group {group_id} by admin {admin_id}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            return False
    
    async def delete_template(self, group_id: int,
                            message_type: str,
                            template_name: str,
                            admin_id: int) -> bool:
        """Delete a group-specific template"""
        try:
            # Check admin permissions
            if not await self._validate_group_admin(group_id, admin_id):
                return False
            
            group_templates_path = self.config.DATA_DIR / "messages" / "group_templates.json"
            
            if not group_templates_path.exists():
                return False
            
            group_templates = JSONEngine.load_json(group_templates_path, {})
            group_key = str(group_id)
            
            # Check if template exists
            if (group_key in group_templates and 
                message_type in group_templates[group_key] and 
                template_name in group_templates[group_key][message_type]):
                
                # Delete template
                del group_templates[group_key][message_type][template_name]
                
                # Clean up empty structures
                if not group_templates[group_key][message_type]:
                    del group_templates[group_key][message_type]
                
                if not group_templates[group_key]:
                    del group_templates[group_key]
                
                # Save changes
                JSONEngine.save_json(group_templates_path, group_templates)
                
                logger.info(
                    f"Template {template_name} ({message_type}) deleted "
                    f"for group {group_id} by admin {admin_id}"
                )
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False
    
    async def reset_template(self, group_id: int,
                           message_type: str,
                           template_name: str,
                           admin_id: int) -> bool:
        """Reset template to default"""
        return await self.delete_template(group_id, message_type, template_name, admin_id)
    
    async def create_custom_template(self, group_id: int,
                                   message_type: str,
                                   template_name: str,
                                   text: str,
                                   parse_mode: str = "HTML",
                                   variables: Optional[Dict] = None,
                                   admin_id: int) -> bool:
        """Create a custom template"""
        try:
            # Check if template already exists in defaults
            default_templates = await self.get_message_templates(message_type)
            if template_name in default_templates.get('templates', {}):
                logger.error(f"Template {template_name} already exists in defaults")
                return False
            
            return await self.update_template(
                group_id, message_type, template_name, text, parse_mode, variables, admin_id
            )
        
        except Exception as e:
            logger.error(f"Failed to create custom template: {e}")
            return False
    
    async def render_template(self, group_id: int,
                            message_type: str,
                            template_name: str,
                            context: Dict[str, Any]) -> Optional[str]:
        """Render a template with context"""
        try:
            templates = await self.get_group_templates(group_id, message_type)
            
            if template_name not in templates.get('templates', {}):
                logger.error(f"Template {template_name} not found")
                return None
            
            template = templates['templates'][template_name]
            text = template.get('text', '')
            
            # Replace variables
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                text = text.replace(placeholder, str(value))
            
            return text
        
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            return None
    
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
    
    async def get_available_variables(self, message_type: str) -> List[str]:
        """Get available variables for a message type"""
        variable_map = {
            'welcome': ['user_name', 'user_full_name', 'group_name', 'member_count'],
            'goodbye': ['user_name', 'user_full_name', 'group_name'],
            'admin_only': ['user_name', 'reason', 'duration', 'admin_name'],
            'alerts': ['days', 'issue', 'admin_name', 'action']
        }
        
        return variable_map.get(message_type, [])
    
    async def create_templates_report(self, group_id: int) -> str:
        """Create templates report for group"""
        try:
            message_types = ['welcome', 'goodbye', 'default', 'alerts', 'admin_only']
            
            report_lines = ["📝 **Message Templates Report**\n"]
            report_lines.append(f"**Group ID:** `{group_id}`\n")
            
            total_templates = 0
            custom_templates = 0
            
            for msg_type in message_types:
                templates = await self.get_group_templates(group_id, msg_type)
                template_count = len(templates.get('templates', {}))
                
                if template_count > 0:
                    report_lines.append(f"**{msg_type.title()}:** {template_count} templates")
                    
                    if templates.get('group_override'):
                        custom_templates += template_count
                        report_lines.append("  (Customized for this group)")
                    
                    total_templates += template_count
            
            report_lines.append(f"\n**Summary:** {total_templates} total templates ({custom_templates} customized)")
            
            return "\n".join(report_lines)
        
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            return f"Error generating report: {e}"