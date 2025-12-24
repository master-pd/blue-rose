#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Message Dispatcher
Routes messages to appropriate handlers with middleware, filters, and full update coverage
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable

from config import Config

logger = logging.getLogger(__name__)

class Dispatcher:
    """Message Dispatcher"""
    
    def __init__(self):
        self.config = Config
        self.handlers: Dict[str, List[Dict[str, Any]]] = {}
        self.middleware: List[Callable] = []
        self.filter_functions: List[Callable] = []
    
    # ---------------------- Handler Registration ----------------------
    def register_handler(
        self, handler_type: str, handler: Callable, filters: Optional[List[Callable]] = None
    ):
        """Register a message handler"""
        if handler_type not in self.handlers:
            self.handlers[handler_type] = []
        
        handler_info = {
            'handler': handler,
            'filters': filters or [],
            'enabled': True,
        }
        
        self.handlers[handler_type].append(handler_info)
        logger.debug(f"Registered {handler_type} handler: {handler.__name__}")
    
    def unregister_handler(self, handler_type: str, handler: Callable) -> bool:
        """Unregister a handler"""
        if handler_type in self.handlers:
            for i, handler_info in enumerate(self.handlers[handler_type]):
                if handler_info['handler'] == handler:
                    self.handlers[handler_type].pop(i)
                    logger.debug(f"Unregistered {handler_type} handler: {handler.__name__}")
                    return True
        return False
    
    # ---------------------- Middleware & Filters ----------------------
    def add_middleware(self, middleware: Callable):
        """Add middleware to dispatcher"""
        self.middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__name__}")
    
    def add_filter(self, filter_func: Callable):
        """Add a global filter"""
        self.filter_functions.append(filter_func)
        logger.debug(f"Added filter: {filter_func.__name__}")
    
    # ---------------------- Dispatching ----------------------
    async def dispatch(self, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Dispatch an update to appropriate handlers"""
        try:
            update_type = self._get_update_type(update)
            if not update_type:
                logger.debug(f"Unknown update type: {update}")
                return None
            
            # Apply global filters
            if not await self._apply_filters(update, update_type):
                logger.debug(f"Update filtered out: {update_type}")
                return None
            
            # Apply middleware
            processed_update = update.copy()
            for middleware in self.middleware:
                if asyncio.iscoroutinefunction(middleware):
                    processed_update = await middleware(processed_update)
                else:
                    processed_update = middleware(processed_update)
                
                if processed_update is None:
                    logger.debug("Update filtered by middleware")
                    return None
            
            # Find matching handlers
            handlers = self.handlers.get(update_type, [])
            matching_handlers = []
            for handler_info in handlers:
                if not handler_info['enabled']:
                    continue
                if await self._check_handler_filters(processed_update, handler_info['filters']):
                    matching_handlers.append(handler_info['handler'])
            
            # Execute handlers
            results = []
            for handler in matching_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(processed_update)
                    else:
                        result = handler(processed_update)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Handler {handler.__name__} failed: {e}")
            
            for result in results:
                if result is not None:
                    return result
            
            # No matching handlers fallback
            if not matching_handlers:
                return await self._handle_no_match(processed_update, update_type)
            
            return None
        
        except Exception as e:
            logger.error(f"Dispatch failed: {e}", exc_info=True)
            return None
    
    # ---------------------- Update Type Detection ----------------------
    def _get_update_type(self, update: Dict[str, Any]) -> Optional[str]:
        """Determine the type of update"""
        if 'message' in update:
            message = update['message']
            if 'text' in message:
                text = message['text']
                if text.startswith('/'):
                    command = text.split()[0].split('@')[0]
                    return f'command:{command}'
                else:
                    return 'text_message'
            elif 'photo' in message:
                return 'photo_message'
            elif 'video' in message:
                return 'video_message'
            elif 'document' in message:
                return 'document_message'
            elif 'audio' in message:
                return 'audio_message'
            elif 'voice' in message:
                return 'voice_message'
            elif 'sticker' in message:
                return 'sticker_message'
            elif 'location' in message:
                return 'location_message'
            elif 'contact' in message:
                return 'contact_message'
            elif 'new_chat_members' in message:
                return 'new_chat_members'
            elif 'left_chat_member' in message:
                return 'left_chat_member'
            elif 'migrate_to_chat_id' in message:
                return 'chat_migration'
        elif 'callback_query' in update:
            return 'callback_query'
        elif 'inline_query' in update:
            return 'inline_query'
        elif 'chosen_inline_result' in update:
            return 'chosen_inline_result'
        elif 'chat_member' in update:
            return 'chat_member_update'
        elif 'my_chat_member' in update:
            return 'my_chat_member_update'
        elif 'poll' in update:
            return 'poll_update'
        elif 'poll_answer' in update:
            return 'poll_answer'
        return None
    
    # ---------------------- Filters ----------------------
    async def _apply_filters(self, update: Dict[str, Any], update_type: str) -> bool:
        """Apply global filters"""
        if not self.filter_functions:
            return True
        for filter_func in self.filter_functions:
            try:
                if asyncio.iscoroutinefunction(filter_func):
                    result = await filter_func(update, update_type)
                else:
                    result = filter_func(update, update_type)
                if not result:
                    return False
            except Exception as e:
                logger.error(f"Filter {filter_func.__name__} failed: {e}")
        return True
    
    async def _check_handler_filters(self, update: Dict[str, Any], filters: List[Callable]) -> bool:
        """Check if update passes all handler filters"""
        if not filters:
            return True
        for filter_func in filters:
            try:
                if asyncio.iscoroutinefunction(filter_func):
                    result = await filter_func(update)
                else:
                    result = filter_func(update)
                if not result:
                    return False
            except Exception as e:
                logger.error(f"Handler filter failed: {e}")
                return False
        return True
    
    # ---------------------- Fallback ----------------------
    async def _handle_no_match(self, update: Dict[str, Any], update_type: str) -> Optional[Dict[str, Any]]:
        """Handle updates with no matching handlers"""
        logger.debug(f"No handler for update type: {update_type}")
        # Default handling (optional AI reply, logging, etc.)
        return None
    
    # ---------------------- Enable / Disable ----------------------
    def enable_handler_type(self, handler_type: str, enable: bool = True):
        """Enable or disable all handlers of a type"""
        if handler_type in self.handlers:
            for handler_info in self.handlers[handler_type]:
                handler_info['enabled'] = enable
            status = "enabled" if enable else "disabled"
            logger.info(f"{status.capitalize()} all {handler_type} handlers")
    
    def enable_handler(self, handler_type: str, handler: Callable, enable: bool = True):
        """Enable or disable specific handler"""
        if handler_type in self.handlers:
            for handler_info in self.handlers[handler_type]:
                if handler_info['handler'] == handler:
                    handler_info['enabled'] = enable
                    status = "enabled" if enable else "disabled"
                    logger.info(f"{status.capitalize()} handler: {handler.__name__}")
                    return True
        return False
    
    # ---------------------- Stats ----------------------
    def get_handler_stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        stats = {
            'total_handler_types': len(self.handlers),
            'total_handlers': sum(len(handlers) for handlers in self.handlers.values()),
            'enabled_handlers': 0,
            'disabled_handlers': 0,
            'middleware_count': len(self.middleware),
            'filter_count': len(self.filter_functions),
        }
        for handlers in self.handlers.values():
            for handler_info in handlers:
                if handler_info['enabled']:
                    stats['enabled_handlers'] += 1
                else:
                    stats['disabled_handlers'] += 1
        return stats
