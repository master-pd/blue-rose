#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Group Router
Handle group-specific messages and events
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List

from config import Config
from core.permission_engine import PermissionEngine, Permission
from core.feature_switch import FeatureSwitch
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class GroupRouter:
    """Group Message and Event Router"""
    
    def __init__(self):
        self.config = Config
        self.permission_engine = PermissionEngine()
        self.feature_switch = FeatureSwitch()
        
        # Group event handlers
        self.event_handlers = {
            'new_member': [],
            'left_member': [],
            'pinned_message': [],
            'new_chat_title': [],
            'new_chat_photo': [],
            'delete_chat_photo': [],
            'group_created': [],
            'supergroup_created': [],
            'channel_created': [],
            'migrate_to_chat': [],
            'migrate_from_chat': [],
        }
        
        # Group message filters
        self.message_filters = []
    
    async def route_group_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Route a group message"""
        try:
            chat_id = message.get('chat', {}).get('id')
            
            if not chat_id:
                logger.warning("No chat ID in message")
                return None
            
            # Check if bot is in group
            if not await self._is_bot_in_group(chat_id):
                logger.debug(f"Bot not in group {chat_id}, ignoring message")
                return None
            
            # Check group status
            group_status = await self._get_group_status(chat_id)
            
            if not group_status.get('active', True):
                logger.debug(f"Group {chat_id} is inactive")
                return None
            
            # Apply message filters
            filtered_message = message.copy()
            for filter_func in self.message_filters:
                if asyncio.iscoroutinefunction(filter_func):
                    result = await filter_func(filtered_message, chat_id)
                else:
                    result = filter_func(filtered_message, chat_id)
                
                if result is None:
                    logger.debug(f"Message filtered out in group {chat_id}")
                    return None
                filtered_message = result
            
            # Handle special events
            event_type = self._get_group_event_type(filtered_message)
            
            if event_type:
                return await self._handle_group_event(event_type, filtered_message, chat_id)
            
            # Regular group message
            return await self._handle_group_message(filtered_message, chat_id)
            
        except Exception as e:
            logger.error(f"Group routing failed: {e}")
            return None
    
    async def _is_bot_in_group(self, chat_id: int) -> bool:
        """Check if bot is a member of the group"""
        # In a real implementation, this would check Telegram API
        # For now, check our groups.json
        groups_file = self.config.JSON_PATHS['groups']
        
        if groups_file.exists():
            groups = JSONEngine.load_json(groups_file, {})
            return str(chat_id) in groups
        
        return False
    
    async def _get_group_status(self, chat_id: int) -> Dict[str, Any]:
        """Get group status and settings"""
        groups_file = self.config.JSON_PATHS['groups']
        
        if groups_file.exists():
            groups = JSONEngine.load_json(groups_file, {})
            group_data = groups.get(str(chat_id), {})
            
            return {
                'active': group_data.get('active', True),
                'plan': group_data.get('plan', 'free'),
                'expiry': group_data.get('expiry'),
                'services': group_data.get('services', {}),
            }
        
        return {'active': False}
    
    def _get_group_event_type(self, message: Dict[str, Any]) -> Optional[str]:
        """Detect group event type"""
        if 'new_chat_members' in message:
            return 'new_member'
        elif 'left_chat_member' in message:
            return 'left_member'
        elif 'pinned_message' in message:
            return 'pinned_message'
        elif 'new_chat_title' in message:
            return 'new_chat_title'
        elif 'new_chat_photo' in message:
            return 'new_chat_photo'
        elif 'delete_chat_photo' in message:
            return 'delete_chat_photo'
        elif 'group_chat_created' in message:
            return 'group_created'
        elif 'supergroup_chat_created' in message:
            return 'supergroup_created'
        elif 'channel_chat_created' in message:
            return 'channel_created'
        elif 'migrate_to_chat_id' in message:
            return 'migrate_to_chat'
        elif 'migrate_from_chat_id' in message:
            return 'migrate_from_chat'
        
        return None
    
    async def _handle_group_event(self, event_type: str, message: Dict[str, Any], 
                                chat_id: int) -> Optional[Dict[str, Any]]:
        """Handle group event"""
        handlers = self.event_handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for group event: {event_type}")
            return None
        
        # Execute handlers
        results = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(message, chat_id)
                else:
                    result = handler(message, chat_id)
                
                if result:
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Group event handler failed: {e}")
        
        # Return first non-None result
        for result in results:
            if result is not None:
                return result
        
        return None
    
    async def _handle_group_message(self, message: Dict[str, Any], 
                                  chat_id: int) -> Optional[Dict[str, Any]]:
        """Handle regular group message"""
        # Check if message should trigger auto-reply
        if await self._should_auto_reply(message, chat_id):
            return await self._generate_auto_reply(message, chat_id)
        
        # Check if message should be moderated
        if await self._should_moderate(message, chat_id):
            return await self._apply_moderation(message, chat_id)
        
        return None
    
    async def _should_auto_reply(self, message: Dict[str, Any], chat_id: int) -> bool:
        """Check if message should trigger auto-reply"""
        # Check feature
        if not await self.feature_switch.is_enabled('auto_reply', chat_id):
            return False
        
        # Check if message has text
        if 'text' not in message:
            return False
        
        # Check if user has permission
        user_id = message.get('from', {}).get('id')
        if user_id:
            has_permission = await self.permission_engine.has_permission(
                user_id, Permission.USE_AUTO_REPLIES, chat_id
            )
            if not has_permission:
                return False
        
        # Additional checks would go here
        # (e.g., check for questions, keywords, etc.)
        
        return True
    
    async def _generate_auto_reply(self, message: Dict[str, Any], 
                                 chat_id: int) -> Optional[Dict[str, Any]]:
        """Generate auto-reply for message"""
        # This would connect to the intelligence system
        # For now, return a simple response
        
        text = message.get('text', '')
        
        # Simple keyword matching
        responses = {
            'hello': 'Hello there! 👋',
            'hi': 'Hi! How can I help?',
            'help': 'I can help with various tasks! Use /help for commands.',
            'thank': 'You\'re welcome! 😊',
        }
        
        for keyword, response in responses.items():
            if keyword.lower() in text.lower():
                return {
                    'action': 'send_message',
                    'chat_id': chat_id,
                    'text': response,
                    'reply_to_message_id': message.get('message_id'),
                }
        
        return None
    
    async def _should_moderate(self, message: Dict[str, Any], chat_id: int) -> bool:
        """Check if message should be moderated"""
        # Check feature
        if not await self.feature_switch.is_enabled('moderation', chat_id):
            return False
        
        # Check message content
        text = message.get('text', '')
        
        # Simple spam detection (in real implementation, use proper moderation)
        spam_keywords = ['spam', 'advertisement', 'http://', 'https://', 'www.']
        
        for keyword in spam_keywords:
            if keyword in text.lower():
                return True
        
        return False
    
    async def _apply_moderation(self, message: Dict[str, Any], 
                              chat_id: int) -> Optional[Dict[str, Any]]:
        """Apply moderation to message"""
        # This would connect to the moderation system
        # For now, just log
        
        user_id = message.get('from', {}).get('id')
        text = message.get('text', '')[:50]  # First 50 chars
        
        logger.info(f"Moderation triggered in group {chat_id} - User {user_id}: {text}")
        
        # In real implementation, would delete message, warn user, etc.
        return None
    
    def register_event_handler(self, event_type: str, handler):
        """Register a group event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
            logger.debug(f"Registered group event handler: {event_type}")
        else:
            logger.warning(f"Unknown group event type: {event_type}")
    
    def add_message_filter(self, filter_func):
        """Add a group message filter"""
        self.message_filters.append(filter_func)
        logger.debug("Added group message filter")
    
    async def get_group_info(self, chat_id: int) -> Dict[str, Any]:
        """Get information about a group"""
        groups_file = self.config.JSON_PATHS['groups']
        
        if groups_file.exists():
            groups = JSONEngine.load_json(groups_file, {})
            return groups.get(str(chat_id), {})
        
        return {}
    
    async def update_group_info(self, chat_id: int, updates: Dict[str, Any]) -> bool:
        """Update group information"""
        try:
            groups_file = self.config.JSON_PATHS['groups']
            
            # Load existing groups
            groups = JSONEngine.load_json(groups_file, {})
            
            # Update group data
            group_key = str(chat_id)
            if group_key not in groups:
                groups[group_key] = {}
            
            # Deep update
            import copy
            current = groups[group_key]
            for key, value in updates.items():
                if isinstance(value, dict) and isinstance(current.get(key), dict):
                    # Recursive update for dicts
                    current.setdefault(key, {}).update(value)
                else:
                    current[key] = value
            
            # Save updated groups
            return JSONEngine.save_json(groups_file, groups)
            
        except Exception as e:
            logger.error(f"Failed to update group info: {e}")
            return False
    
    def get_group_stats(self) -> Dict[str, Any]:
        """Get group router statistics"""
        return {
            'event_handlers': {k: len(v) for k, v in self.event_handlers.items()},
            'message_filters': len(self.message_filters),
        }