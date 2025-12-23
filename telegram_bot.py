#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Telegram Bot API Integration
Main Telegram bot handler with webhook/polling support
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot import types as telebot_types

from config import Config
from core.kernel import Kernel
from core.dispatcher import Dispatcher
from core.permission_engine import PermissionEngine
from engine.message_router import MessageRouter
from engine.command_router import CommandRouter
from engine.callback_router import CallbackRouter
from engine.group_router import GroupRouter
from engine.private_router import PrivateRouter
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class TelegramBot:
    """Main Telegram Bot Handler"""
    
    def __init__(self):
        self.config = Config
        self.bot_token = self.config.API_TOKEN
        
        # Initialize TeleBot
        self.bot = AsyncTeleBot(self.bot_token)
        
        # Initialize core systems
        self.kernel = Kernel()
        self.dispatcher = Dispatcher()
        self.permission_engine = PermissionEngine()
        
        # Initialize routers
        self.message_router = MessageRouter()
        self.command_router = CommandRouter()
        self.callback_router = CallbackRouter()
        self.group_router = GroupRouter()
        self.private_router = PrivateRouter()
        
        # Bot info
        self.bot_info = None
        self.webhook_url = None
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all Telegram bot handlers"""
        
        # Message handler
        @self.bot.message_handler(func=lambda message: True)
        async def handle_message(message: telebot_types.Message):
            await self._handle_message(message)
        
        # Callback query handler
        @self.bot.callback_query_handler(func=lambda call: True)
        async def handle_callback(call: telebot_types.CallbackQuery):
            await self._handle_callback(call)
        
        # Inline query handler
        @self.bot.inline_handler(func=lambda query: True)
        async def handle_inline(query: telebot_types.InlineQuery):
            await self._handle_inline(query)
        
        # Chat member updates
        @self.bot.chat_member_handler(func=lambda update: True)
        async def handle_chat_member(update: telebot_types.ChatMemberUpdated):
            await self._handle_chat_member(update)
        
        # My chat member updates (bot added/removed from chat)
        @self.bot.my_chat_member_handler(func=lambda update: True)
        async def handle_my_chat_member(update: telebot_types.ChatMemberUpdated):
            await self._handle_my_chat_member(update)
    
    async def _handle_message(self, message: telebot_types.Message):
        """Handle incoming message"""
        try:
            # Convert message to dict for processing
            message_dict = self._message_to_dict(message)
            
            # Log message
            await self._log_message(message_dict)
            
            # Determine message type and route accordingly
            chat_type = message.chat.type
            
            if chat_type == 'private':
                # Private message
                result = await self.private_router.route_private_message(message_dict)
            elif chat_type in ['group', 'supergroup']:
                # Group message
                result = await self.group_router.route_group_message(message_dict)
            else:
                # Channel or other chat type
                result = await self.message_router.route_message(message_dict)
            
            # Execute result if any
            if result:
                await self._execute_action(result, message.chat.id)
            
        except Exception as e:
            logger.error(f"Failed to handle message: {e}", exc_info=True)
    
    async def _handle_callback(self, call: telebot_types.CallbackQuery):
        """Handle callback query"""
        try:
            # Convert callback to dict
            callback_dict = {
                'id': call.id,
                'from': self._user_to_dict(call.from_user),
                'message': self._message_to_dict(call.message) if call.message else None,
                'chat_instance': call.chat_instance,
                'data': call.data,
                'inline_message_id': call.inline_message_id,
            }
            
            # Route callback
            result = await self.callback_router.route_callback(callback_dict)
            
            # Execute result
            if result:
                await self._execute_action(result, call.message.chat.id if call.message else None)
            
        except Exception as e:
            logger.error(f"Failed to handle callback: {e}")
    
    async def _handle_inline(self, query: telebot_types.InlineQuery):
        """Handle inline query"""
        try:
            # Convert inline query to dict
            query_dict = {
                'id': query.id,
                'from': self._user_to_dict(query.from_user),
                'query': query.query,
                'offset': query.offset,
                'chat_type': query.chat_type,
                'location': self._location_to_dict(query.location) if query.location else None,
            }
            
            # Handle inline query (simplified for now)
            results = []
            
            # Create simple result
            article = telebot_types.InlineQueryResultArticle(
                id='1',
                title='Blue Rose Bot',
                description='Advanced Telegram Bot',
                input_message_content=telebot_types.InputTextMessageContent(
                    message_text='Hello from Blue Rose Bot! 🌹'
                )
            )
            results.append(article)
            
            # Answer inline query
            await self.bot.answer_inline_query(query.id, results)
            
        except Exception as e:
            logger.error(f"Failed to handle inline query: {e}")
    
    async def _handle_chat_member(self, update: telebot_types.ChatMemberUpdated):
        """Handle chat member updates"""
        try:
            # Log member update
            logger.info(f"Chat member updated: {update.chat.id} - {update.from_user.id}")
            
            # Update group data if bot is admin
            if update.new_chat_member.status in ['administrator', 'creator']:
                await self._update_bot_admin_status(update.chat, True)
            elif update.new_chat_member.status == 'member':
                await self._update_bot_admin_status(update.chat, False)
            
        except Exception as e:
            logger.error(f"Failed to handle chat member update: {e}")
    
    async def _handle_my_chat_member(self, update: telebot_types.ChatMemberUpdated):
        """Handle bot's own chat member updates (bot added/removed)"""
        try:
            chat = update.chat
            new_status = update.new_chat_member.status
            old_status = update.old_chat_member.status
            
            logger.info(f"Bot status changed in {chat.id}: {old_status} -> {new_status}")
            
            if new_status == 'member':
                # Bot added to group
                await self._handle_bot_added(chat)
            elif new_status == 'left' or new_status == 'kicked':
                # Bot removed from group
                await self._handle_bot_removed(chat)
            
        except Exception as e:
            logger.error(f"Failed to handle my chat member update: {e}")
    
    async def _handle_bot_added(self, chat: telebot_types.Chat):
        """Handle bot added to group"""
        try:
            # Add group to database
            groups = JSONEngine.load_json(self.config.JSON_PATHS['groups'], {})
            group_key = str(chat.id)
            
            if group_key not in groups:
                groups[group_key] = {
                    'title': chat.title,
                    'type': chat.type,
                    'added_at': datetime.now().isoformat(),
                    'active': True,
                    'plan': 'free',
                    'plan_active': False,
                    'admins': [],
                    'settings': {},
                }
                
                JSONEngine.save_json(self.config.JSON_PATHS['groups'], groups)
                logger.info(f"Bot added to new group: {chat.title} ({chat.id})")
            
            # Send welcome message
            welcome_text = f"""
👋 <b>Hello! I'm {self.config.BOT_NAME}!</b>

Thank you for adding me to <b>{chat.title}</b>!

🤖 <i>Your intelligent group assistant</i>

<b>To get started:</b>
1. Make sure I have <b>admin privileges</b>
2. Use /settings to configure features
3. Set up payment plan if needed

<b>Features I offer:</b>
• 🤖 Smart auto-replies
• 🛡️ Automated moderation
• 📅 Scheduled messages
• 🕌 Prayer time alerts
• 👥 Welcome/goodbye messages

<b>Need help?</b> Use /help or contact my developer.
            """.strip()
            
            await self.bot.send_message(
                chat.id,
                welcome_text,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Failed to handle bot added: {e}")
    
    async def _handle_bot_removed(self, chat: telebot_types.Chat):
        """Handle bot removed from group"""
        try:
            # Update group status
            groups = JSONEngine.load_json(self.config.JSON_PATHS['groups'], {})
            group_key = str(chat.id)
            
            if group_key in groups:
                groups[group_key]['active'] = False
                groups[group_key]['removed_at'] = datetime.now().isoformat()
                
                JSONEngine.save_json(self.config.JSON_PATHS['groups'], groups)
                logger.info(f"Bot removed from group: {chat.title} ({chat.id})")
            
        except Exception as e:
            logger.error(f"Failed to handle bot removed: {e}")
    
    async def _update_bot_admin_status(self, chat: telebot_types.Chat, is_admin: bool):
        """Update bot's admin status in group"""
        try:
            groups = JSONEngine.load_json(self.config.JSON_PATHS['groups'], {})
            group_key = str(chat.id)
            
            if group_key in groups:
                groups[group_key]['bot_is_admin'] = is_admin
                groups[group_key]['admin_updated'] = datetime.now().isoformat()
                
                JSONEngine.save_json(self.config.JSON_PATHS['groups'], groups)
                
                status = "admin" if is_admin else "not admin"
                logger.info(f"Bot {status} in group: {chat.title} ({chat.id})")
            
        except Exception as e:
            logger.error(f"Failed to update bot admin status: {e}")
    
    def _message_to_dict(self, message: telebot_types.Message) -> Dict[str, Any]:
        """Convert TeleBot Message to dict"""
        if not message:
            return {}
        
        message_dict = {
            'message_id': message.message_id,
            'from': self._user_to_dict(message.from_user) if message.from_user else None,
            'date': message.date,
            'chat': self._chat_to_dict(message.chat) if message.chat else None,
            'forward_from': self._user_to_dict(message.forward_from) if message.forward_from else None,
            'forward_from_chat': self._chat_to_dict(message.forward_from_chat) if message.forward_from_chat else None,
            'forward_date': message.forward_date,
            'reply_to_message': self._message_to_dict(message.reply_to_message) if message.reply_to_message else None,
            'text': message.text,
            'caption': message.caption,
            'photo': self._photos_to_list(message.photo) if message.photo else None,
            'video': self._video_to_dict(message.video) if message.video else None,
            'document': self._document_to_dict(message.document) if message.document else None,
            'audio': self._audio_to_dict(message.audio) if message.audio else None,
            'voice': self._voice_to_dict(message.voice) if message.voice else None,
            'sticker': self._sticker_to_dict(message.sticker) if message.sticker else None,
            'location': self._location_to_dict(message.location) if message.location else None,
            'contact': self._contact_to_dict(message.contact) if message.contact else None,
            'new_chat_members': [self._user_to_dict(user) for user in message.new_chat_members] if message.new_chat_members else None,
            'left_chat_member': self._user_to_dict(message.left_chat_member) if message.left_chat_member else None,
            'new_chat_title': message.new_chat_title,
            'new_chat_photo': self._photos_to_list(message.new_chat_photo) if message.new_chat_photo else None,
            'delete_chat_photo': message.delete_chat_photo,
            'group_chat_created': message.group_chat_created,
            'supergroup_chat_created': message.supergroup_chat_created,
            'channel_chat_created': message.channel_chat_created,
            'migrate_to_chat_id': message.migrate_to_chat_id,
            'migrate_from_chat_id': message.migrate_from_chat_id,
            'pinned_message': self._message_to_dict(message.pinned_message) if message.pinned_message else None,
            'via_bot': self._user_to_dict(message.via_bot) if message.via_bot else None,
            'entities': [self._entity_to_dict(entity) for entity in message.entities] if message.entities else None,
        }
        
        return {k: v for k, v in message_dict.items() if v is not None}
    
    def _user_to_dict(self, user: telebot_types.User) -> Dict[str, Any]:
        """Convert User to dict"""
        if not user:
            return {}
        
        return {
            'id': user.id,
            'is_bot': user.is_bot,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'language_code': user.language_code,
            'is_premium': getattr(user, 'is_premium', None),
        }
    
    def _chat_to_dict(self, chat: telebot_types.Chat) -> Dict[str, Any]:
        """Convert Chat to dict"""
        if not chat:
            return {}
        
        return {
            'id': chat.id,
            'type': chat.type,
            'title': chat.title,
            'username': chat.username,
            'first_name': chat.first_name,
            'last_name': chat.last_name,
        }
    
    def _photos_to_list(self, photos: list) -> list:
        """Convert photo sizes to list"""
        if not photos:
            return []
        
        return [
            {
                'file_id': photo.file_id,
                'file_unique_id': photo.file_unique_id,
                'width': photo.width,
                'height': photo.height,
                'file_size': photo.file_size,
            }
            for photo in photos
        ]
    
    def _video_to_dict(self, video: telebot_types.Video) -> Dict[str, Any]:
        """Convert Video to dict"""
        if not video:
            return {}
        
        return {
            'file_id': video.file_id,
            'file_unique_id': video.file_unique_id,
            'width': video.width,
            'height': video.height,
            'duration': video.duration,
            'thumb': self._photo_to_dict(video.thumb) if video.thumb else None,
            'file_name': video.file_name,
            'mime_type': video.mime_type,
            'file_size': video.file_size,
        }
    
    def _document_to_dict(self, document: telebot_types.Document) -> Dict[str, Any]:
        """Convert Document to dict"""
        if not document:
            return {}
        
        return {
            'file_id': document.file_id,
            'file_unique_id': document.file_unique_id,
            'thumb': self._photo_to_dict(document.thumb) if document.thumb else None,
            'file_name': document.file_name,
            'mime_type': document.mime_type,
            'file_size': document.file_size,
        }
    
    def _audio_to_dict(self, audio: telebot_types.Audio) -> Dict[str, Any]:
        """Convert Audio to dict"""
        if not audio:
            return {}
        
        return {
            'file_id': audio.file_id,
            'file_unique_id': audio.file_unique_id,
            'duration': audio.duration,
            'performer': audio.performer,
            'title': audio.title,
            'file_name': audio.file_name,
            'mime_type': audio.mime_type,
            'file_size': audio.file_size,
            'thumb': self._photo_to_dict(audio.thumb) if audio.thumb else None,
        }
    
    def _voice_to_dict(self, voice: telebot_types.Voice) -> Dict[str, Any]:
        """Convert Voice to dict"""
        if not voice:
            return {}
        
        return {
            'file_id': voice.file_id,
            'file_unique_id': voice.file_unique_id,
            'duration': voice.duration,
            'mime_type': voice.mime_type,
            'file_size': voice.file_size,
        }
    
    def _sticker_to_dict(self, sticker: telebot_types.Sticker) -> Dict[str, Any]:
        """Convert Sticker to dict"""
        if not sticker:
            return {}
        
        return {
            'file_id': sticker.file_id,
            'file_unique_id': sticker.file_unique_id,
            'width': sticker.width,
            'height': sticker.height,
            'is_animated': sticker.is_animated,
            'is_video': sticker.is_video,
            'thumb': self._photo_to_dict(sticker.thumb) if sticker.thumb else None,
            'emoji': sticker.emoji,
            'set_name': sticker.set_name,
            'file_size': sticker.file_size,
        }
    
    def _location_to_dict(self, location: telebot_types.Location) -> Dict[str, Any]:
        """Convert Location to dict"""
        if not location:
            return {}
        
        return {
            'longitude': location.longitude,
            'latitude': location.latitude,
        }
    
    def _contact_to_dict(self, contact: telebot_types.Contact) -> Dict[str, Any]:
        """Convert Contact to dict"""
        if not contact:
            return {}
        
        return {
            'phone_number': contact.phone_number,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'user_id': contact.user_id,
        }
    
    def _entity_to_dict(self, entity: telebot_types.MessageEntity) -> Dict[str, Any]:
        """Convert MessageEntity to dict"""
        if not entity:
            return {}
        
        return {
            'type': entity.type,
            'offset': entity.offset,
            'length': entity.length,
            'url': entity.url,
            'user': self._user_to_dict(entity.user) if entity.user else None,
            'language': entity.language,
        }
    
    def _photo_to_dict(self, photo: telebot_types.PhotoSize) -> Dict[str, Any]:
        """Convert PhotoSize to dict"""
        if not photo:
            return {}
        
        return {
            'file_id': photo.file_id,
            'file_unique_id': photo.file_unique_id,
            'width': photo.width,
            'height': photo.height,
            'file_size': photo.file_size,
        }
    
    async def _log_message(self, message: Dict[str, Any]):
        """Log incoming message"""
        try:
            chat_id = message.get('chat', {}).get('id')
            user_id = message.get('from', {}).get('id')
            text = message.get('text', '')[:100]  # First 100 chars
            
            logger.debug(f"Message from {user_id} in {chat_id}: {text}")
            
        except Exception as e:
            logger.error(f"Failed to log message: {e}")
    
    async def _execute_action(self, action: Dict[str, Any], chat_id: Optional[int] = None):
        """Execute bot action"""
        try:
            action_type = action.get('action')
            
            if action_type == 'send_message':
                await self._execute_send_message(action, chat_id)
            elif action_type == 'edit_message_text':
                await self._execute_edit_message_text(action)
            elif action_type == 'answer_callback':
                await self._execute_answer_callback(action)
            elif action_type == 'delete_message':
                await self._execute_delete_message(action, chat_id)
            elif action_type == 'restrict_user':
                await self._execute_restrict_user(action, chat_id)
            elif action_type == 'kick_user':
                await self._execute_kick_user(action, chat_id)
            elif action_type == 'ban_user':
                await self._execute_ban_user(action, chat_id)
            
        except Exception as e:
            logger.error(f"Failed to execute action {action.get('action')}: {e}")
    
    async def _execute_send_message(self, action: Dict[str, Any], default_chat_id: Optional[int] = None):
        """Execute send_message action"""
        chat_id = action.get('chat_id', default_chat_id)
        text = action.get('text', '')
        parse_mode = action.get('parse_mode', 'HTML')
        reply_markup = action.get('reply_markup')
        reply_to_message_id = action.get('reply_to_message_id')
        
        if not chat_id or not text:
            return
        
        # Convert reply_markup if it's a dict
        if isinstance(reply_markup, dict):
            if 'inline_keyboard' in reply_markup:
                markup = telebot_types.InlineKeyboardMarkup()
                for row in reply_markup['inline_keyboard']:
                    keyboard_row = []
                    for button in row:
                        keyboard_row.append(
                            telebot_types.InlineKeyboardButton(
                                text=button['text'],
                                callback_data=button['callback_data']
                            )
                        )
                    markup.row(*keyboard_row)
                reply_markup = markup
        
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            reply_to_message_id=reply_to_message_id,
        )
    
    async def _execute_edit_message_text(self, action: Dict[str, Any]):
        """Execute edit_message_text action"""
        chat_id = action.get('chat_id')
        message_id = action.get('message_id')
        text = action.get('text', '')
        parse_mode = action.get('parse_mode', 'HTML')
        reply_markup = action.get('reply_markup')
        
        if not chat_id or not message_id or not text:
            return
        
        await self.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    
    async def _execute_answer_callback(self, action: Dict[str, Any]):
        """Execute answer_callback_query action"""
        callback_query_id = action.get('callback_query_id')
        text = action.get('text')
        show_alert = action.get('show_alert', False)
        
        if not callback_query_id:
            return
        
        await self.bot.answer_callback_query(
            callback_query_id=callback_query_id,
            text=text,
            show_alert=show_alert,
        )
    
    async def _execute_delete_message(self, action: Dict[str, Any], chat_id: Optional[int]):
        """Execute delete_message action"""
        target_chat_id = action.get('chat_id', chat_id)
        message_id = action.get('message_id')
        
        if not target_chat_id or not message_id:
            return
        
        await self.bot.delete_message(target_chat_id, message_id)
    
    async def _execute_restrict_user(self, action: Dict[str, Any], chat_id: Optional[int]):
        """Execute restrict_user action"""
        target_chat_id = action.get('chat_id', chat_id)
        user_id = action.get('user_id')
        until_date = action.get('until_date')
        permissions = action.get('permissions', {})
        
        if not target_chat_id or not user_id:
            return
        
        # Convert permissions dict to ChatPermissions object
        chat_permissions = telebot_types.ChatPermissions(
            can_send_messages=permissions.get('can_send_messages', False),
            can_send_media_messages=permissions.get('can_send_media_messages', False),
            can_send_polls=permissions.get('can_send_polls', False),
            can_send_other_messages=permissions.get('can_send_other_messages', False),
            can_add_web_page_previews=permissions.get('can_add_web_page_previews', False),
            can_change_info=permissions.get('can_change_info', False),
            can_invite_users=permissions.get('can_invite_users', False),
            can_pin_messages=permissions.get('can_pin_messages', False),
        )
        
        await self.bot.restrict_chat_member(
            chat_id=target_chat_id,
            user_id=user_id,
            until_date=until_date,
            permissions=chat_permissions,
        )
    
    async def _execute_kick_user(self, action: Dict[str, Any], chat_id: Optional[int]):
        """Execute kick_user action"""
        target_chat_id = action.get('chat_id', chat_id)
        user_id = action.get('user_id')
        until_date = action.get('until_date')
        
        if not target_chat_id or not user_id:
            return
        
        await self.bot.ban_chat_member(
            chat_id=target_chat_id,
            user_id=user_id,
            until_date=until_date,
            revoke_messages=action.get('revoke_messages', True),
        )
    
    async def _execute_ban_user(self, action: Dict[str, Any], chat_id: Optional[int]):
        """Execute ban_user action"""
        target_chat_id = action.get('chat_id', chat_id)
        user_id = action.get('user_id')
        until_date = action.get('until_date')
        
        if not target_chat_id or not user_id:
            return
        
        await self.bot.ban_chat_member(
            chat_id=target_chat_id,
            user_id=user_id,
            until_date=until_date,
            revoke_messages=action.get('revoke_messages', True),
        )
    
    async def start_polling(self):
        """Start bot with polling"""
        try:
            # Get bot info
            self.bot_info = await self.bot.get_me()
            logger.info(f"Starting {self.config.BOT_NAME} ({self.bot_info.username})...")
            
            # Start polling
            await self.bot.polling(non_stop=True, timeout=60)
            
        except Exception as e:
            logger.error(f"Polling failed: {e}")
            raise
    
    async def set_webhook(self, webhook_url: str, secret_token: Optional[str] = None):
        """Set webhook for bot"""
        try:
            self.webhook_url = webhook_url
            
            await self.bot.remove_webhook()
            await self.bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token,
                max_connections=40,
            )
            
            logger.info(f"Webhook set: {webhook_url}")
            
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            raise
    
    async def remove_webhook(self):
        """Remove webhook"""
        try:
            await self.bot.remove_webhook()
            logger.info("Webhook removed")
            
        except Exception as e:
            logger.error(f"Failed to remove webhook: {e}")
    
    async def get_updates(self, offset: Optional[int] = None, limit: int = 100):
        """Get updates manually (for webhook)"""
        try:
            updates = await self.bot.get_updates(offset=offset, limit=limit)
            return updates
            
        except Exception as e:
            logger.error(f"Failed to get updates: {e}")
            return []
    
    async def close(self):
        """Close bot connection"""
        try:
            await self.bot.close()
            logger.info("Bot connection closed")
            
        except Exception as e:
            logger.error(f"Failed to close bot: {e}")