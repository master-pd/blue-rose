#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Command Router
Route commands to appropriate handlers
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List, Callable

from config import Config
from core.permission_engine import PermissionEngine
from core.feature_switch import FeatureSwitch

logger = logging.getLogger(__name__)

class CommandRouter:
    """Command Routing System"""
    
    def __init__(self):
        self.config = Config
        self.permission_engine = PermissionEngine()
        self.feature_switch = FeatureSwitch()
        
        # Command handlers
        self.command_handlers = {}
        self.fallback_handler = None
        
        # Command aliases
        self.command_aliases = {}
        
        # Command categories
        self.command_categories = {
            'start': ['start', 'help', 'about'],
            'admin': ['admin', 'mod', 'settings'],
            'group': ['group', 'chat', 'settings'],
            'user': ['me', 'profile', 'stats'],
            'payment': ['pay', 'plan', 'subscription'],
            'moderation': ['warn', 'mute', 'ban', 'kick'],
            'fun': ['joke', 'quote', 'fact'],
        }
    
    async def route_command(self, command: str, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Route a command to appropriate handler"""
        try:
            # Extract command info
            command_name = self._extract_command_name(command)
            chat_id = message.get('chat', {}).get('id')
            user_id = message.get('from', {}).get('id')
            
            if not command_name or not chat_id or not user_id:
                logger.warning(f"Invalid command: {command}")
                return None
            
            # Check aliases
            actual_command = self.command_aliases.get(command_name, command_name)
            
            # Check permissions
            if not await self._check_command_permissions(actual_command, user_id, chat_id):
                logger.warning(f"Permission denied for command: {actual_command} (user: {user_id})")
                return await self._send_permission_denied(message, actual_command)
            
            # Check feature flags
            if not await self._check_command_features(actual_command, chat_id):
                logger.debug(f"Feature not enabled for command: {actual_command}")
                return await self._send_feature_disabled(message, actual_command)
            
            # Find handler
            handler = self.command_handlers.get(actual_command)
            
            if handler:
                # Execute handler
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(message, command)
                    else:
                        result = handler(message, command)
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Command handler failed for {actual_command}: {e}")
                    return await self._send_error(message, actual_command, e)
            else:
                # No handler found
                logger.debug(f"No handler for command: {actual_command}")
                
                # Try fallback handler
                if self.fallback_handler:
                    try:
                        if asyncio.iscoroutinefunction(self.fallback_handler):
                            return await self.fallback_handler(message, command)
                        else:
                            return self.fallback_handler(message, command)
                    except Exception as e:
                        logger.error(f"Fallback handler failed: {e}")
                
                # Send unknown command message
                return await self._send_unknown_command(message, actual_command)
            
        except Exception as e:
            logger.error(f"Command routing failed: {e}")
            return None
    
    def _extract_command_name(self, command_text: str) -> Optional[str]:
        """Extract command name from command text"""
        if not command_text.startswith('/'):
            return None
        
        # Remove leading slash and any parameters
        command_parts = command_text.split()
        command_name = command_parts[0][1:]  # Remove '/'
        
        # Remove bot username if present
        if '@' in command_name:
            command_name = command_name.split('@')[0]
        
        return command_name.lower()
    
    async def _check_command_permissions(self, command: str, user_id: int, 
                                       chat_id: int) -> bool:
        """Check if user has permission to use this command"""
        # Map commands to permissions
        command_permissions = {
            # Admin commands
            'admin': 'access_admin_panel',
            'settings': 'manage_group_settings',
            'mod': 'access_group_panel',
            'warn': 'warn_users',
            'mute': 'mute_users',
            'ban': 'ban_users',
            'kick': 'ban_users',
            
            # Group commands
            'group': 'access_group_panel',
            'chat': 'access_group_panel',
            
            # Payment commands
            'pay': 'request_payment',
            'plan': 'request_payment',
            'subscription': 'request_payment',
        }
        
        # Get permission name for command
        permission_name = command_permissions.get(command)
        
        if permission_name:
            # Check specific permission
            from core.permission_engine import Permission
            try:
                permission = Permission(permission_name)
                return await self.permission_engine.has_permission(user_id, permission, chat_id)
            except ValueError:
                # Permission not found in enum
                logger.warning(f"Unknown permission: {permission_name}")
                return True  # Default allow
        
        # Default allow for other commands
        return True
    
    async def _check_command_features(self, command: str, chat_id: int) -> bool:
        """Check if features required for command are enabled"""
        # Map commands to features
        command_features = {
            # Moderation commands require moderation feature
            'warn': 'moderation',
            'mute': 'moderation',
            'ban': 'moderation',
            'kick': 'moderation',
            
            # Payment commands require payments feature
            'pay': 'payments',
            'plan': 'payments',
            'subscription': 'payments',
        }
        
        feature_name = command_features.get(command)
        
        if feature_name:
            return await self.feature_switch.is_enabled(feature_name, chat_id)
        
        return True
    
    async def _send_permission_denied(self, message: Dict[str, Any], 
                                    command: str) -> Dict[str, Any]:
        """Send permission denied message"""
        # This would send a Telegram message
        # For now, just return a response dict
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': f"❌ Permission denied for command: /{command}",
            'parse_mode': 'HTML',
        }
    
    async def _send_feature_disabled(self, message: Dict[str, Any], 
                                   command: str) -> Dict[str, Any]:
        """Send feature disabled message"""
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': f"🔧 Feature disabled for command: /{command}",
            'parse_mode': 'HTML',
        }
    
    async def _send_error(self, message: Dict[str, Any], command: str, 
                        error: Exception) -> Dict[str, Any]:
        """Send error message"""
        logger.error(f"Command error: {command} - {error}")
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': f"⚠️ Error executing command: /{command}\n\n<code>{str(error)}</code>",
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
    
    def register_command(self, command: str, handler: Callable, 
                        aliases: List[str] = None):
        """Register a command handler"""
        # Register main command
        self.command_handlers[command.lower()] = handler
        logger.debug(f"Registered command handler: /{command}")
        
        # Register aliases
        if aliases:
            for alias in aliases:
                alias_lower = alias.lower()
                self.command_aliases[alias_lower] = command.lower()
                logger.debug(f"Registered command alias: /{alias} -> /{command}")
    
    def register_fallback(self, handler: Callable):
        """Register fallback handler for unknown commands"""
        self.fallback_handler = handler
        logger.debug("Registered fallback handler")
    
    def get_command_info(self, command: str) -> Dict[str, Any]:
        """Get information about a command"""
        command_lower = command.lower()
        actual_command = self.command_aliases.get(command_lower, command_lower)
        
        handler = self.command_handlers.get(actual_command)
        
        info = {
            'command': actual_command,
            'has_handler': handler is not None,
            'handler_name': handler.__name__ if handler else None,
            'aliases': [],
        }
        
        # Find aliases for this command
        for alias, target in self.command_aliases.items():
            if target == actual_command:
                info['aliases'].append(alias)
        
        return info
    
    async def get_available_commands(self, user_id: int, chat_id: int) -> List[Dict[str, Any]]:
        """Get list of available commands for user"""
        available_commands = []
        
        for command, handler in self.command_handlers.items():
            # Check permissions
            if await self._check_command_permissions(command, user_id, chat_id):
                # Check features
                if await self._check_command_features(command, chat_id):
                    available_commands.append({
                        'command': command,
                        'handler': handler.__name__,
                    })
        
        return available_commands
    
    def get_command_stats(self) -> Dict[str, Any]:
        """Get command router statistics"""
        return {
            'total_commands': len(self.command_handlers),
            'total_aliases': len(self.command_aliases),
            'has_fallback': self.fallback_handler is not None,
            'command_list': list(self.command_handlers.keys()),
        }