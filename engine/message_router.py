#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Message Router
Route messages to appropriate handlers
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List

from config import Config
from core.permission_engine import PermissionEngine, Permission
from core.feature_switch import FeatureSwitch
from intelligence.message_collector import MessageCollector

logger = logging.getLogger(__name__)

class MessageRouter:
    """Message Routing System"""
    
    def __init__(self):
        self.config = Config
        self.permission_engine = PermissionEngine()
        self.feature_switch = FeatureSwitch()
        self.message_collector = MessageCollector()
        
        # Message handlers by type
        self.handlers = {
            'text': [],
            'photo': [],
            'video': [],
            'document': [],
            'audio': [],
            'voice': [],
            'sticker': [],
            'location': [],
            'contact': [],
            'new_chat_members': [],
            'left_chat_member': [],
        }
        
        # Middleware chain
        self.middleware = []
    
    async def route_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Route a message to appropriate handlers"""
        try:
            # Extract message info
            message_type = self._get_message_type(message)
            chat_id = message.get('chat', {}).get('id')
            user_id = message.get('from', {}).get('id')
            
            if not message_type or not chat_id or not user_id:
                logger.warning(f"Invalid message: {message}")
                return None
            
            # Apply middleware
            processed_message = message.copy()
            for middleware in self.middleware:
                if asyncio.iscoroutinefunction(middleware):
                    result = await middleware(processed_message)
                else:
                    result = middleware(processed_message)
                
                if result is None:
                    logger.debug("Message filtered by middleware")
                    return None
                processed_message = result
            
            # Check permissions
            if not await self._check_message_permissions(processed_message, message_type):
                logger.debug(f"Permission denied for message type: {message_type}")
                return None
            
            # Check feature flags
            if not await self._check_feature_flags(processed_message, message_type):
                logger.debug(f"Feature not enabled for message type: {message_type}")
                return None
            
            # Collect message for intelligence
            await self.message_collector.collect(processed_message)
            
            # Route to appropriate handlers
            handlers = self.handlers.get(message_type, [])
            
            if not handlers:
                # No specific handler, use default
                return await self._handle_default(processed_message, message_type)
            
            # Execute handlers
            results = []
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(processed_message)
                    else:
                        result = handler(processed_message)
                    
                    if result:
                        results.append(result)
                        
                except Exception as e:
                    logger.error(f"Handler failed: {e}")
            
            # Return first non-None result
            for result in results:
                if result is not None:
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Message routing failed: {e}")
            return None
    
    def _get_message_type(self, message: Dict[str, Any]) -> Optional[str]:
        """Determine message type"""
        if 'text' in message:
            return 'text'
        elif 'photo' in message:
            return 'photo'
        elif 'video' in message:
            return 'video'
        elif 'document' in message:
            return 'document'
        elif 'audio' in message:
            return 'audio'
        elif 'voice' in message:
            return 'voice'
        elif 'sticker' in message:
            return 'sticker'
        elif 'location' in message:
            return 'location'
        elif 'contact' in message:
            return 'contact'
        elif 'new_chat_members' in message:
            return 'new_chat_members'
        elif 'left_chat_member' in message:
            return 'left_chat_member'
        
        return None
    
    async def _check_message_permissions(self, message: Dict[str, Any], 
                                       message_type: str) -> bool:
        """Check if user has permission to send this message type"""
        chat_id = message.get('chat', {}).get('id')
        user_id = message.get('from', {}).get('id')
        
        if not chat_id or not user_id:
            return False
        
        # Check basic permissions
        if message_type == 'text':
            return await self.permission_engine.has_permission(
                user_id, Permission.USE_AUTO_REPLIES, chat_id
            )
        elif message_type in ['photo', 'video', 'document']:
            # Media permissions
            return await self.permission_engine.has_permission(
                user_id, Permission.USE_AI_RESPONSES, chat_id
            )
        elif message_type == 'new_chat_members':
            # Welcome message permission check
            return await self.permission_engine.has_permission(
                user_id, Permission.USE_AUTO_REPLIES, chat_id
            )
        
        # Default allow for other message types
        return True
    
    async def _check_feature_flags(self, message: Dict[str, Any], 
                                 message_type: str) -> bool:
        """Check if features are enabled for this message"""
        chat_id = message.get('chat', {}).get('id')
        user_id = message.get('from', {}).get('id')
        
        if not chat_id:
            return True  # Private chat, no group features
        
        # Check auto-reply feature for text messages
        if message_type == 'text':
            return await self.feature_switch.is_enabled('auto_reply', chat_id)
        
        # Check welcome message feature
        if message_type == 'new_chat_members':
            return await self.feature_switch.is_enabled('welcome_message', chat_id)
        
        # Check goodbye message feature
        if message_type == 'left_chat_member':
            return await self.feature_switch.is_enabled('goodbye_message', chat_id)
        
        return True
    
    async def _handle_default(self, message: Dict[str, Any], 
                            message_type: str) -> Optional[Dict[str, Any]]:
        """Default message handler"""
        # This would trigger AI responses or other default behavior
        # For now, just log
        logger.debug(f"No handler for {message_type} message")
        return None
    
    def register_handler(self, message_type: str, handler):
        """Register a message handler"""
        if message_type in self.handlers:
            self.handlers[message_type].append(handler)
            logger.debug(f"Registered {message_type} handler: {handler.__name__}")
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    def add_middleware(self, middleware):
        """Add middleware to the chain"""
        self.middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__name__}")
    
    async def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        stats = {
            'total_handlers': sum(len(handlers) for handlers in self.handlers.values()),
            'handler_types': {},
            'middleware_count': len(self.middleware),
        }
        
        for msg_type, handlers in self.handlers.items():
            stats['handler_types'][msg_type] = len(handlers)
        
        return stats