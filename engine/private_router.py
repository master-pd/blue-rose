#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Private Router
Handle private chat messages and commands
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from config import Config
from core.permission_engine import PermissionEngine
from core.feature_switch import FeatureSwitch
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class PrivateRouter:
    """Private Chat Message Router"""
    
    def __init__(self):
        self.config = Config
        self.permission_engine = PermissionEngine()
        self.feature_switch = FeatureSwitch()
        
        # Private message handlers
        self.message_handlers = []
        
        # Private command handlers (override for private chat)
        self.command_handlers = {}
        
        # User session data
        self.user_sessions = {}
    
    async def route_private_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Route a private message"""
        try:
            chat_id = message.get('chat', {}).get('id')
            user_id = message.get('from', {}).get('id')
            
            if not chat_id or not user_id:
                logger.warning("Invalid private message")
                return None
            
            # Check if it's a private chat
            chat_type = message.get('chat', {}).get('type')
            if chat_type != 'private':
                logger.debug(f"Not a private chat: {chat_type}")
                return None
            
            # Get or create user session
            session = await self._get_user_session(user_id)
            
            # Check if user is in a conversation flow
            if session.get('in_conversation'):
                return await self._handle_conversation_flow(message, session)
            
            # Check if it's a command
            text = message.get('text', '')
            if text.startswith('/'):
                return await self._handle_private_command(text, message, session)
            
            # Handle regular message
            return await self._handle_private_message(message, session)
            
        except Exception as e:
            logger.error(f"Private routing failed: {e}")
            return None
    
    async def _get_user_session(self, user_id: int) -> Dict[str, Any]:
        """Get or create user session"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'user_id': user_id,
                'created_at': asyncio.get_event_loop().time(),
                'in_conversation': False,
                'conversation_state': {},
                'message_count': 0,
                'last_active': asyncio.get_event_loop().time(),
            }
        
        # Update last active
        self.user_sessions[user_id]['last_active'] = asyncio.get_event_loop().time()
        self.user_sessions[user_id]['message_count'] += 1
        
        return self.user_sessions[user_id].copy()
    
    async def _handle_conversation_flow(self, message: Dict[str, Any], 
                                      session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle conversation flow message"""
        # This would handle multi-step conversations
        # For now, just end the conversation
        
        user_id = session['user_id']
        
        # Clear conversation state
        self.user_sessions[user_id]['in_conversation'] = False
        self.user_sessions[user_id]['conversation_state'] = {}
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': 'Conversation ended. How can I help you?',
            'parse_mode': 'HTML',
        }
    
    async def _handle_private_command(self, command_text: str, 
                                    message: Dict[str, Any],
                                    session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle private command"""
        # Extract command name
        command_parts = command_text.split()
        command_name = command_parts[0][1:]  # Remove '/'
        
        # Remove bot username if present
        if '@' in command_name:
            command_name = command_name.split('@')[0]
        
        command_name = command_name.lower()
        
        # Check for registered private command handler
        if command_name in self.command_handlers:
            handler = self.command_handlers[command_name]
            
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(message, command_text, session)
                else:
                    result = handler(message, command_text, session)
                
                return result
                
            except Exception as e:
                logger.error(f"Private command handler failed: {e}")
                return await self._send_error(message, f"Command error: {e}")
        
        # Default command handling
        return await self._handle_default_command(command_name, message, session)
    
    async def _handle_default_command(self, command_name: str,
                                    message: Dict[str, Any],
                                    session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle default commands"""
        chat_id = message.get('chat', {}).get('id')
        
        default_commands = {
            'start': await self._handle_start_command(message, session),
            'help': await self._handle_help_command(message, session),
            'about': await self._handle_about_command(message, session),
            'support': await self._handle_support_command(message, session),
            'groups': await self._handle_groups_command(message, session),
            'plan': await self._handle_plan_command(message, session),
            'admin': await self._handle_admin_command(message, session),
        }
        
        if command_name in default_commands:
            result = default_commands[command_name]
            if result:
                return result
        
        # Unknown command
        return await self._send_unknown_command(message, command_name)
    
    async def _handle_start_command(self, message: Dict[str, Any],
                                  session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /start command"""
        user_id = message.get('from', {}).get('id')
        chat_id = message.get('chat', {}).get('id')
        
        # Check if user is bot owner
        is_owner = user_id == self.config.BOT_OWNER_ID
        
        # Check if user is bot admin
        bot_admins = JSONEngine.load_json(self.config.JSON_PATHS['bot_admins'], {})
        is_admin = user_id in bot_admins.get('admins', [])
        
        # Welcome message
        welcome_text = f"""
🌟 <b>Welcome to {self.config.BOT_NAME}!</b> 🌟

🤖 <i>Advanced Telegram Bot with AI capabilities</i>

👤 <b>Your ID:</b> <code>{user_id}</code>
{'👑 <b>Role:</b> Bot Owner' if is_owner else '🛡️ <b>Role:</b> Bot Admin' if is_admin else '👤 <b>Role:</b> User'}

<b>Available Commands:</b>
/help - Show help message
/about - About this bot
/groups - Your groups
/plan - Subscription plans
/support - Get support

{'/admin - Admin panel' if is_owner or is_admin else ''}

Use me in groups for automated replies, moderation, and more!
        """.strip()
        
        return {
            'action': 'send_message',
            'chat_id': chat_id,
            'text': welcome_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_help_command(self, message: Dict[str, Any],
                                 session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /help command"""
        help_text = f"""
<b>{self.config.BOT_NAME} Help</b>

🤖 <b>About:</b>
I'm an advanced Telegram bot with multiple features including:
• Auto-reply system
• Group moderation
• Payment plans
• AI responses
• Scheduled messages
• And much more!

<b>Basic Commands:</b>
/start - Start the bot
/help - This help message
/about - About the bot
/groups - List your groups
/plan - Subscription information
/support - Support channel

<b>Group Features:</b>
Add me to your group and use /settings to configure:
• Welcome/Goodbye messages
• Auto-moderation
• Prayer time alerts
• Night mode
• Custom auto-replies

<b>Need Help?</b>
Join our support channel: {self.config.DEVELOPER_CONTACT}
        """.strip()
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': help_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_about_command(self, message: Dict[str, Any],
                                  session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /about command"""
        about_text = f"""
<b>{self.config.BOT_NAME}</b>
Version: {self.config.BOT_VERSION}

<b>Developer:</b> {self.config.DEVELOPER}
<b>Contact:</b> {self.config.DEVELOPER_CONTACT}

<b>Features:</b>
• Advanced auto-reply system
• Multi-group management
• Payment and subscription system
• AI-powered responses
• Comprehensive moderation
• Scheduled messages
• Backup and restore
• And much more!

<b>Technology:</b>
• Python 3.12+
• Telegram Bot API v20+
• JSON-based storage
• Modular architecture

<b>Source Code:</b> Private
<b>License:</b> Proprietary

Thank you for using {self.config.BOT_NAME}! 🌹
        """.strip()
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': about_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_support_command(self, message: Dict[str, Any],
                                    session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /support command"""
        support_text = f"""
<b>Support & Contact</b>

If you need help or have questions:

<b>Developer:</b> {self.config.DEVELOPER}
<b>Telegram:</b> {self.config.DEVELOPER_CONTACT}
<b>Email:</b> ranaeditz333@gmail.com
<b>Phone:</b> 01847634486

<b>Support Channel:</b>
https://t.me/master_account_remover_channel

<b>Bot Issues:</b>
• Feature requests
• Bug reports
• Payment issues
• General inquiries

<b>Response Time:</b>
Usually within 24 hours
        """.strip()
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': support_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_groups_command(self, message: Dict[str, Any],
                                   session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /groups command"""
        user_id = message.get('from', {}).get('id')
        
        # Get user's groups
        groups_file = self.config.JSON_PATHS['groups']
        groups = JSONEngine.load_json(groups_file, {})
        
        user_groups = []
        for chat_id_str, group_data in groups.items():
            # Check if user is admin in group
            admins = group_data.get('admins', [])
            if user_id in admins or user_id == group_data.get('owner_id'):
                user_groups.append({
                    'chat_id': chat_id_str,
                    'title': group_data.get('title', 'Unknown Group'),
                    'plan': group_data.get('plan', 'free'),
                })
        
        if not user_groups:
            groups_text = "📭 <b>You don't have any groups yet.</b>\n\nAdd me to a group and make me admin to get started!"
        else:
            groups_text = "📋 <b>Your Groups:</b>\n\n"
            for i, group in enumerate(user_groups, 1):
                groups_text += f"{i}. <b>{group['title']}</b>\n"
                groups_text += f"   ID: <code>{group['chat_id']}</code>\n"
                groups_text += f"   Plan: {group['plan'].title()}\n\n"
            
            groups_text += "Use /settings in a group to configure it."
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': groups_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_plan_command(self, message: Dict[str, Any],
                                 session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /plan command"""
        plans_text = f"""
<b>Subscription Plans</b>

<b>Free Trial:</b>
• 30 days unlimited features
• All basic functionalities
• Auto-renewal not required

<b>Paid Plans:</b>
1. <b>30 Days</b> - 60৳
   • Unlimited features
   • Priority support
   
2. <b>90 Days</b> - 100৳
   • All features
   • Priority support
   • Better value
   
3. <b>8 Months</b> - 200৳
   • All features
   • Priority support
   • Best value
   • Special perks

<b>Payment Method:</b>
Manual approval via admin panel.
Contact {self.config.DEVELOPER_CONTACT} for payment.

<b>Features Included:</b>
• All auto-reply features
• Full moderation system
• AI responses
• Scheduled messages
• Group management
• Backup and restore
        """.strip()
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': plans_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_admin_command(self, message: Dict[str, Any],
                                  session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle /admin command"""
        user_id = message.get('from', {}).get('id')
        
        # Check permissions
        is_owner = user_id == self.config.BOT_OWNER_ID
        bot_admins = JSONEngine.load_json(self.config.JSON_PATHS['bot_admins'], {})
        is_admin = user_id in bot_admins.get('admins', [])
        
        if not (is_owner or is_admin):
            return await self._send_permission_denied(message, "admin")
        
        # Admin panel text
        admin_text = f"""
<b>Admin Panel</b>

👑 <b>Role:</b> {'Bot Owner' if is_owner else 'Bot Admin'}

<b>Available Actions:</b>
• View all groups
• Manage payment requests
• Force join/leave groups
• Override group settings
• View system analytics
• Manage bot admins (owners only)

<b>Bot Statistics:</b>
• Groups: [Loading...]
• Users: [Loading...]
• Payments: [Loading...]

<b>System Status:</b>
• Uptime: [Loading...]
• Memory: [Loading...]
• Storage: [Loading...]

Use the appropriate admin commands or panels for detailed management.
        """.strip()
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': admin_text,
            'parse_mode': 'HTML',
        }
    
    async def _handle_private_message(self, message: Dict[str, Any],
                                    session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle regular private message"""
        text = message.get('text', '')
        
        if not text:
            return None
        
        # Simple auto-response
        responses = {
            'hello': 'Hello! How can I help you today? 😊',
            'hi': 'Hi there! 👋',
            'how are you': 'I\'m doing great, thanks for asking! How about you?',
            'thank': 'You\'re welcome! Let me know if you need anything else.',
            'bye': 'Goodbye! Have a great day! 👋',
            'good night': 'Good night! Sleep well! 🌙',
        }
        
        text_lower = text.lower()
        
        for keyword, response in responses.items():
            if keyword in text_lower:
                return {
                    'action': 'send_message',
                    'chat_id': message.get('chat', {}).get('id'),
                    'text': response,
                    'parse_mode': 'HTML',
                }
        
        # Default response
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': 'I understand you said something. How can I assist you today? You can use /help to see available commands.',
            'parse_mode': 'HTML',
        }
    
    async def _send_permission_denied(self, message: Dict[str, Any], 
                                    command: str) -> Dict[str, Any]:
        """Send permission denied message"""
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': f"❌ Permission denied for command: /{command}",
            'parse_mode': 'HTML',
        }
    
    async def _send_unknown_command(self, message: Dict[str, Any], 
                                  command: str) -> Dict[str, Any]:
        """Send unknown command message"""
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': f"❓ Unknown command: /{command}\n\nUse /help to see available commands.",
            'parse_mode': 'HTML',
        }
    
    async def _send_error(self, message: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Send error message"""
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': f"⚠️ Error: {error_msg}",
            'parse_mode': 'HTML',
        }
    
    def register_command_handler(self, command: str, handler):
        """Register a private command handler"""
        self.command_handlers[command.lower()] = handler
        logger.debug(f"Registered private command handler: /{command}")
    
    def register_message_handler(self, handler):
        """Register a private message handler"""
        self.message_handlers.append(handler)
        logger.debug("Registered private message handler")
    
    async def start_conversation(self, user_id: int, conversation_type: str, 
                               initial_data: Dict[str, Any] = None):
        """Start a conversation with user"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id]['in_conversation'] = True
            self.user_sessions[user_id]['conversation_state'] = {
                'type': conversation_type,
                'step': 0,
                'data': initial_data or {},
            }
            logger.debug(f"Started conversation with user {user_id}: {conversation_type}")
            return True
        return False
    
    async def end_conversation(self, user_id: int):
        """End conversation with user"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id]['in_conversation'] = False
            self.user_sessions[user_id]['conversation_state'] = {}
            logger.debug(f"Ended conversation with user {user_id}")
            return True
        return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        active_sessions = sum(1 for s in self.user_sessions.values() 
                            if s.get('in_conversation'))
        
        return {
            'total_sessions': len(self.user_sessions),
            'active_conversations': active_sessions,
            'private_commands': len(self.command_handlers),
            'message_handlers': len(self.message_handlers),
        }