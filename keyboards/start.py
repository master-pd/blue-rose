#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Start Keyboard
Start menu keyboard generator
"""

import logging
from typing import Dict, Any, Optional

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class StartKeyboard:
    """Start Menu Keyboard Generator"""
    
    def __init__(self):
        self.config = Config
    
    async def get_private_keyboard(self, user_id: int, role) -> Optional[Dict[str, Any]]:
        """Get keyboard for private chat"""
        # Check if user is bot owner
        is_owner = user_id == self.config.BOT_OWNER_ID
        
        # Check if user is bot admin
        bot_admins = JSONEngine.load_json(self.config.JSON_PATHS['bot_admins'], {})
        is_admin = user_id in bot_admins.get('admins', [])
        
        keyboard = {
            'inline_keyboard': [
                # First row
                [
                    {'text': '📦 Add to Group', 'callback_data': 'start_add_group'},
                    {'text': '📋 All Groups', 'callback_data': 'start_all_groups'},
                ],
                # Second row
                [
                    {'text': '💰 Plan', 'callback_data': 'start_plan'},
                    {'text': '🆘 Help', 'callback_data': 'start_help'},
                ],
                # Third row
                [
                    {'text': '📞 Support', 'callback_data': 'start_support'},
                    {'text': '👑 Master', 'callback_data': 'start_master'},
                ],
                # Fourth row
                [
                    {'text': '🤖 Bot Info', 'callback_data': 'start_bot_info'},
                    {'text': '❌ End', 'callback_data': 'start_end'},
                ],
            ]
        }
        
        # Add admin button if user is owner/admin
        if is_owner or is_admin:
            keyboard['inline_keyboard'].insert(3, [
                {'text': '👑 Admin Panel', 'callback_data': 'start_admin'}
            ])
        
        return keyboard
    
    async def get_group_keyboard(self, user_id: int, role, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get keyboard for group chat"""
        from core.permission_engine import PermissionEngine
        permission_engine = PermissionEngine()
        
        # Check if user is admin in this group
        is_group_admin = await permission_engine.can_perform_action(
            user_id, 'access_group_panel', chat_id
        )
        
        keyboard = {
            'inline_keyboard': [
                [
                    {'text': '🆘 Help', 'callback_data': 'start_help'},
                    {'text': '📞 Support', 'callback_data': 'start_support'},
                ],
                [
                    {'text': '🤖 Bot Info', 'callback_data': 'start_bot_info'},
                    {'text': '❌ End', 'callback_data': 'start_end'},
                ],
            ]
        }
        
        # Add settings button if user is group admin
        if is_group_admin:
            keyboard['inline_keyboard'].insert(0, [
                {'text': '⚙️ Group Settings', 'callback_data': 'start_group_settings'}
            ])
        
        return keyboard