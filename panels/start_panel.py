#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Start Panel
Start command handler and main menu
"""

import logging
from typing import Dict, Any, Optional

from config import Config
from keyboards.start import StartKeyboard
from core.permission_engine import PermissionEngine

logger = logging.getLogger(__name__)

class StartPanel:
    """Start Command Panel"""
    
    def __init__(self):
        self.config = Config
        self.keyboard = StartKeyboard()
        self.permission_engine = PermissionEngine()
    
    async def show_start_menu(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Show start menu based on user role"""
        user_id = message.get('from', {}).get('id')
        chat_id = message.get('chat', {}).get('id')
        chat_type = message.get('chat', {}).get('type')
        
        # Get user role
        role = await self.permission_engine.get_user_role(user_id, chat_id)
        
        # Prepare welcome message
        if chat_type == 'private':
            welcome_text = await self._get_private_welcome(user_id, role)
            keyboard = await self.keyboard.get_private_keyboard(user_id, role)
        else:
            welcome_text = await self._get_group_welcome(user_id, role, chat_id)
            keyboard = await self.keyboard.get_group_keyboard(user_id, role, chat_id)
        
        return {
            'action': 'send_message',
            'chat_id': chat_id,
            'text': welcome_text,
            'parse_mode': 'HTML',
            'reply_markup': keyboard,
        }
    
    async def _get_private_welcome(self, user_id: int, role) -> str:
        """Get welcome message for private chat"""
        # Check if user is bot owner
        is_owner = user_id == self.config.BOT_OWNER_ID
        
        # Check if user is bot admin
        from storage.json_engine import JSONEngine
        bot_admins = JSONEngine.load_json(self.config.JSON_PATHS['bot_admins'], {})
        is_admin = user_id in bot_admins.get('admins', [])
        
        welcome = f"""
🌟 <b>Welcome to {self.config.BOT_NAME}!</b> 🌟

🤖 <i>Advanced Telegram Bot with AI capabilities</i>

👤 <b>Your ID:</b> <code>{user_id}</code>
{'👑 <b>Role:</b> Bot Owner' if is_owner else '🛡️ <b>Role:</b> Bot Admin' if is_admin else '👤 <b>Role:</b> User'}

<b>I can help you with:</b>
• 🤖 Auto-replies to messages
• 🛡️ Group moderation
• 📅 Scheduled messages
• 🕌 Prayer time alerts
• 💰 Payment plans
• 📊 Analytics & reports

<b>Add me to your group</b> and make me admin to unlock all features!

<b>Developed by:</b> {self.config.DEVELOPER}
<b>Contact:</b> {self.config.DEVELOPER_CONTACT}
        """.strip()
        
        return welcome
    
    async def _get_group_welcome(self, user_id: int, role, chat_id: int) -> str:
        """Get welcome message for group chat"""
        welcome = f"""
👋 <b>Hello! I'm {self.config.BOT_NAME}!</b>

🤖 <i>Your intelligent group assistant</i>

I'm here to help manage this group with:

• 🤖 Smart auto-replies
• 🛡️ Automated moderation
• 📅 Scheduled messages
• 🕌 Prayer time alerts
• 👥 Welcome/goodbye messages

<b>Commands:</b>
/start - Show this menu
/help - Get help
/settings - Group settings (admins only)

<b>Need help?</b> Contact my developer: {self.config.DEVELOPER_CONTACT}
        """.strip()
        
        return welcome
    
    async def handle_start_callback(self, callback_query: Dict[str, Any],
                                  data: str) -> Optional[Dict[str, Any]]:
        """Handle start menu callbacks"""
        action = data.replace('start_', '')
        
        actions = {
            'add_group': await self._handle_add_group,
            'all_groups': await self._handle_all_groups,
            'plan': await self._handle_plan,
            'help': await self._handle_help,
            'support': await self._handle_support,
            'master': await self._handle_master,
            'bot_info': await self._handle_bot_info,
            'end': await self._handle_end,
        }
        
        if action in actions:
            return await actions[action](callback_query)
        
        return None
    
    async def _handle_add_group(self, callback_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add group button"""
        return {
            'action': 'edit_message_text',
            'chat_id': callback_query['message']['chat']['id'],
            'message_id': callback_query['message']['message_id'],
            'text': "📦 <b>Add me to your group:</b>\n\n1. Add @blue_rose_bot to your group\n2. Make me administrator\n3. Use /settings to configure",
            'parse_mode': 'HTML',
        }
    
    async def _handle_all_groups(self, callback_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle all groups button"""
        # This would show user's groups
        return {
            'action': 'edit_message_text',
            'chat_id': callback_query['message']['chat']['id'],
            'message_id': callback_query['message']['message_id'],
            'text': "📋 <b>Your Groups:</b>\n\n(Feature coming soon)",
            'parse_mode': 'HTML',
        }
    
    async def _handle_plan(self, callback_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle plan button"""
        plan_text = """
💰 <b>Subscription Plans:</b>

1. <b>Free Trial</b> - 30 days
   • Basic auto-replies
   • Welcome messages

2. <b>30 Days</b> - 60৳
   • All auto-reply features
   • Moderation system
   • Scheduled messages

3. <b>90 Days</b> - 100৳
   • All features
   • Priority support

4. <b>8 Months</b> - 200৳
   • All features
   • Highest priority
   • Customization

<b>Contact:</b> @rana_editz_00
        """.strip()
        
        return {
            'action': 'edit_message_text',
            'chat_id': callback_query['message']['chat']['id'],
            'message_id': callback_query['message']['message_id'],
            'text': plan_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_help(self, callback_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle help button"""
        from panels.help_panel import HelpPanel
        help_panel = HelpPanel()
        return await help_panel.show_help(callback_query['message'])
    
    async def _handle_support(self, callback_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle support button"""
        from panels.support_panel import SupportPanel
        support_panel = SupportPanel()
        return await support_panel.show_support(callback_query['message'])
    
    async def _handle_master(self, callback_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle master info button"""
        master_text = f"""
👑 <b>Developer Information:</b>

<b>Name:</b> RANA
<b>Social Name:</b> MASTER 🪓
<b>Age:</b> 20 years
<b>Status:</b> Single
<b>Education:</b> SSC Batch 2022
<b>Location:</b> Faridpur, Dhaka, Bangladesh

<b>Profession:</b> Security Field
<b>Work Type:</b> Experiment / Technical Operations

<b>Skills:</b>
• Video Editing
• Photo Editing
• Mobile Technology
• Online Operations
• Cyber Security (Learning)

<b>Contact:</b>
• Email: ranaeditz333@gmail.com
• Telegram: @rana_editz_00
• Phone: 01847634486

<b>Dream:</b> Become a Professional Developer
<b>Project:</b> Website (Coming Soon)
        """.strip()
        
        return {
            'action': 'edit_message_text',
            'chat_id': callback_query['message']['chat']['id'],
            'message_id': callback_query['message']['message_id'],
            'text': master_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_bot_info(self, callback_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle bot info button"""
        bot_info_text = f"""
🤖 <b>Bot Information:</b>

<b>Name:</b> {self.config.BOT_NAME}
<b>Username:</b> @{self.config.BOT_USERNAME}
<b>Version:</b> {self.config.BOT_VERSION}
<b>Developer:</b> {self.config.DEVELOPER}
<b>Contact:</b> {self.config.DEVELOPER_CONTACT}

<b>Features:</b>
• Advanced auto-reply system
• Multi-group management
• Payment system
• AI-powered responses
• Comprehensive moderation
• Scheduled messages
• Backup and restore

<b>Technology:</b>
• Python 3.12+
• Telegram Bot API v20+
• JSON-based storage
• Modular architecture

Thank you for using {self.config.BOT_NAME}! 🌹
        """.strip()
        
        return {
            'action': 'edit_message_text',
            'chat_id': callback_query['message']['chat']['id'],
            'message_id': callback_query['message']['message_id'],
            'text': bot_info_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_end(self, callback_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle end button"""
        return {
            'action': 'answer_callback_query',
            'callback_query_id': callback_query['id'],
            'text': '👋 Goodbye!',
            'show_alert': False,
        }