#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Callback Router
Route callback queries to appropriate handlers
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable

from config import Config
from core.permission_engine import PermissionEngine

logger = logging.getLogger(__name__)

class CallbackRouter:
    """Callback Query Routing System"""
    
    def __init__(self):
        self.config = Config
        self.permission_engine = PermissionEngine()
        
        # Callback handlers by pattern
        self.handlers = {}
        
        # Callback data parsers
        self.parsers = {}
        
        # Callback data generators
        self.generators = {}
    
    async def route_callback(self, callback_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Route a callback query to appropriate handler"""
        try:
            # Extract callback info
            data = callback_query.get('data')
            chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
            user_id = callback_query.get('from', {}).get('id')
            
            if not data or not user_id:
                logger.warning(f"Invalid callback query: {callback_query}")
                return None
            
            # Parse callback data
            parsed_data = await self._parse_callback_data(data)
            
            if not parsed_data:
                logger.warning(f"Failed to parse callback data: {data}")
                return None
            
            # Check permissions
            if not await self._check_callback_permissions(parsed_data, user_id, chat_id):
                logger.warning(f"Permission denied for callback: {data}")
                return await self._send_permission_denied(callback_query, data)
            
            # Find handler
            handler = self._find_handler(parsed_data)
            
            if handler:
                # Execute handler
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(callback_query, parsed_data)
                    else:
                        result = handler(callback_query, parsed_data)
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Callback handler failed: {e}")
                    return await self._send_error(callback_query, data, e)
            else:
                # No handler found
                logger.debug(f"No handler for callback: {data}")
                return await self._send_unknown_callback(callback_query, data)
            
        except Exception as e:
            logger.error(f"Callback routing failed: {e}")
            return None
    
    async def _parse_callback_data(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse callback data string"""
        try:
            # Simple key-value parsing
            # Format: action:value|param1:value1|param2:value2
            
            parsed = {
                'raw': data,
                'action': None,
                'params': {},
            }
            
            parts = data.split('|')
            
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    
                    if key == 'action':
                        parsed['action'] = value
                    else:
                        parsed['params'][key] = value
            
            # If no action found, try to extract from first part
            if not parsed['action'] and parts:
                parsed['action'] = parts[0]
            
            # Apply custom parser if exists
            if parsed['action'] in self.parsers:
                parser = self.parsers[parsed['action']]
                if asyncio.iscoroutinefunction(parser):
                    parsed = await parser(parsed)
                else:
                    parsed = parser(parsed)
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse callback data: {data} - {e}")
            return None
    
    def _find_handler(self, parsed_data: Dict[str, Any]) -> Optional[Callable]:
        """Find handler for parsed callback data"""
        action = parsed_data.get('action')
        
        if not action:
            return None
        
        # Check for exact match
        if action in self.handlers:
            return self.handlers[action]
        
        # Check for pattern match
        for pattern, handler in self.handlers.items():
            if '*' in pattern:
                # Simple wildcard matching
                pattern_parts = pattern.split('*')
                if all(part in action for part in pattern_parts if part):
                    return handler
        
        return None
    
    async def _check_callback_permissions(self, parsed_data: Dict[str, Any], 
                                        user_id: int, chat_id: Optional[int]) -> bool:
        """Check if user has permission for this callback"""
        action = parsed_data.get('action', '')
        
        # Map actions to permissions
        action_permissions = {
            'admin_': 'access_admin_panel',
            'group_': 'access_group_panel',
            'payment_': 'request_payment',
            'mod_': 'access_group_panel',
        }
        
        # Find matching permission
        for prefix, permission_name in action_permissions.items():
            if action.startswith(prefix):
                from core.permission_engine import Permission
                try:
                    permission = Permission(permission_name)
                    return await self.permission_engine.has_permission(user_id, permission, chat_id)
                except ValueError:
                    logger.warning(f"Unknown permission: {permission_name}")
                    break
        
        # Default allow for other callbacks
        return True
    
    async def _send_permission_denied(self, callback_query: Dict[str, Any], 
                                    data: str) -> Dict[str, Any]:
        """Send permission denied response"""
        return {
            'action': 'answer_callback',
            'callback_query_id': callback_query.get('id'),
            'text': '❌ Permission denied',
            'show_alert': True,
        }
    
    async def _send_error(self, callback_query: Dict[str, Any], data: str, 
                        error: Exception) -> Dict[str, Any]:
        """Send error response"""
        logger.error(f"Callback error: {data} - {error}")
        
        return {
            'action': 'answer_callback',
            'callback_query_id': callback_query.get('id'),
            'text': '⚠️ An error occurred',
            'show_alert': True,
        }
    
    async def _send_unknown_callback(self, callback_query: Dict[str, Any], 
                                   data: str) -> Dict[str, Any]:
        """Send unknown callback response"""
        return {
            'action': 'answer_callback',
            'callback_query_id': callback_query.get('id'),
            'text': '❓ Unknown callback',
            'show_alert': False,
        }
    
    def register_handler(self, action: str, handler: Callable):
        """Register a callback handler"""
        self.handlers[action] = handler
        logger.debug(f"Registered callback handler: {action}")
    
    def register_parser(self, action: str, parser: Callable):
        """Register a callback data parser"""
        self.parsers[action] = parser
        logger.debug(f"Registered callback parser: {action}")
    
    def register_generator(self, action: str, generator: Callable):
        """Register a callback data generator"""
        self.generators[action] = generator
        logger.debug(f"Registered callback generator: {action}")
    
    async def generate_callback_data(self, action: str, **kwargs) -> str:
        """Generate callback data string"""
        try:
            # Use generator if exists
            if action in self.generators:
                generator = self.generators[action]
                if asyncio.iscoroutinefunction(generator):
                    return await generator(**kwargs)
                else:
                    return generator(**kwargs)
            
            # Default generation
            parts = [f"action:{action}"]
            
            for key, value in kwargs.items():
                if value is not None:
                    parts.append(f"{key}:{value}")
            
            return '|'.join(parts)
            
        except Exception as e:
            logger.error(f"Failed to generate callback data: {e}")
            return f"action:{action}"
    
    def get_callback_stats(self) -> Dict[str, Any]:
        """Get callback router statistics"""
        return {
            'total_handlers': len(self.handlers),
            'total_parsers': len(self.parsers),
            'total_generators': len(self.generators),
            'handlers': list(self.handlers.keys()),
        }