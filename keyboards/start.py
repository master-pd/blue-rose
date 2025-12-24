#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Start Keyboard
Start menu keyboard generator
"""

import logging
from typing import Dict, Any, Optional
import telebot.types as types

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class StartKeyboard:
    """Start Menu Keyboard Generator"""
    
    def __init__(self):
        self.config = Config
    
    async def get_private_keyboard(self, user_id: int, role) -> types.InlineKeyboardMarkup:
        """Get keyboard for private chat"""
        is_owner = user_id == self.config.BOT_OWNER_ID
        bot_admins = JSONEngine.load_json(self.config.JSON_PATHS['bot_admins'], {})
        is_admin = user_id in bot_admins.get('admins', [])

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("📦 Add to Group", callback_data="start_add_group"),
            types.InlineKeyboardButton("📋 All Groups", callback_data="start_all_groups"),
            types.InlineKeyboardButton("💰 Plan", callback_data="start_plan"),
            types.InlineKeyboardButton("🆘 Help", callback_data="start_help"),
            types.InlineKeyboardButton("📞 Support", callback_data="start_support"),
            types.InlineKeyboardButton("👑 Master", callback_data="start_master"),
            types.InlineKeyboardButton("🤖 Bot Info", callback_data="start_bot_info"),
            types.InlineKeyboardButton("❌ End", callback_data="start_end"),
        ]

        # Add admin button if user is owner/admin
        if is_owner or is_admin:
            buttons.insert(6, types.InlineKeyboardButton("👑 Admin Panel", callback_data="start_admin"))

        # Add buttons to keyboard in rows of 2
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard
    
    async def get_group_keyboard(self, user_id: int, role, chat_id: int) -> types.InlineKeyboardMarkup:
        """Get keyboard for group chat"""
        from core.permission_engine import PermissionEngine
        permission_engine = PermissionEngine()
        is_group_admin = await permission_engine.can_perform_action(
            user_id, 'access_group_panel', chat_id
        )

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("🆘 Help", callback_data="start_help"),
            types.InlineKeyboardButton("📞 Support", callback_data="start_support"),
            types.InlineKeyboardButton("🤖 Bot Info", callback_data="start_bot_info"),
            types.InlineKeyboardButton("❌ End", callback_data="start_end"),
        ]

        # Add settings button if user is group admin
        if is_group_admin:
            buttons.insert(0, types.InlineKeyboardButton("⚙️ Group Settings", callback_data="start_group_settings"))

        # Add buttons to keyboard in rows of 2
        keyboard_rows = []
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard
