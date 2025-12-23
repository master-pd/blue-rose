#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Kernel System
Central brain of the bot
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class Kernel:
    """Central Kernel System"""
    
    def __init__(self):
        self.config = Config
        self.modules = {}
        self.handlers = {}
        self.middleware = []
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the kernel"""
        try:
            logger.info("⚙️ Initializing Kernel...")
            
            # Load bot info
            self.bot_info = JSONEngine.load_json(
                self.config.JSON_PATHS['bot_info']
            )
            
            # Load bot settings
            self.bot_settings = JSONEngine.load_json(
                self.config.JSON_PATHS['bot_settings']
            )
            
            # Initialize modules registry
            self.modules = {
                'core': {},
                'engine': {},
                'storage': {},
                'intelligence': {},
                'moderation': {},
                'supremacy': {},
                'payments': {},
                'panels': {},
                'keyboards': {},
                'analytics': {},
                'failsafe': {},
            }
            
            # Register system events
            self._register_system_events()
            
            self.is_initialized = True
            logger.info("✅ Kernel initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize kernel: {e}")
            return False
    
    def _register_system_events(self):
        """Register system events"""
        self.events = {
            'startup': [],
            'shutdown': [],
            'message_received': [],
            'command_received': [],
            'error_occurred': [],
            'module_loaded': [],
            'module_unloaded': [],
        }
    
    async def start(self):
        """Start the kernel"""
        if not self.is_initialized:
            logger.error("Kernel not initialized!")
            return False
        
        try:
            logger.info("🚀 Starting Kernel...")
            
            # Trigger startup events
            await self._trigger_event('startup')
            
            # Start all registered modules
            for module_type, modules in self.modules.items():
                for module_name, module in modules.items():
                    if hasattr(module, 'start'):
                        await module.start()
                        logger.debug(f"Started module: {module_type}.{module_name}")
            
            logger.info("✅ Kernel started successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start kernel: {e}")
            await self._trigger_event('error_occurred', error=e)
            return False
    
    async def stop(self):
        """Stop the kernel"""
        try:
            logger.info("🛑 Stopping Kernel...")
            
            # Stop all registered modules in reverse order
            for module_type, modules in reversed(list(self.modules.items())):
                for module_name, module in modules.items():
                    if hasattr(module, 'stop'):
                        await module.stop()
                        logger.debug(f"Stopped module: {module_type}.{module_name}")
            
            # Trigger shutdown events
            await self._trigger_event('shutdown')
            
            logger.info("✅ Kernel stopped successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping kernel: {e}")
            return False
    
    def register_module(self, module_type: str, module_name: str, module):
        """Register a module"""
        if module_type not in self.modules:
            self.modules[module_type] = {}
        
        self.modules[module_type][module_name] = module
        logger.info(f"Registered module: {module_type}.{module_name}")
        
        # Trigger module loaded event
        asyncio.create_task(self._trigger_event('module_loaded', 
            module_type=module_type, module_name=module_name))
    
    def unregister_module(self, module_type: str, module_name: str):
        """Unregister a module"""
        if module_type in self.modules and module_name in self.modules[module_type]:
            del self.modules[module_type][module_name]
            logger.info(f"Unregistered module: {module_type}.{module_name}")
            
            # Trigger module unloaded event
            asyncio.create_task(self._trigger_event('module_unloaded',
                module_type=module_type, module_name=module_name))
            return True
        return False
    
    def get_module(self, module_type: str, module_name: str):
        """Get a registered module"""
        if module_type in self.modules:
            return self.modules[module_type].get(module_name)
        return None
    
    def register_handler(self, handler_type: str, handler):
        """Register a message/command handler"""
        if handler_type not in self.handlers:
            self.handlers[handler_type] = []
        
        self.handlers[handler_type].append(handler)
        logger.debug(f"Registered {handler_type} handler")
    
    def get_handlers(self, handler_type: str) -> List:
        """Get handlers for a specific type"""
        return self.handlers.get(handler_type, [])
    
    def add_middleware(self, middleware):
        """Add middleware to the chain"""
        self.middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__class__.__name__}")
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a message through the kernel"""
        try:
            # Apply middleware
            processed_message = message.copy()
            
            for middleware in self.middleware:
                if hasattr(middleware, 'process'):
                    processed_message = await middleware.process(processed_message)
                    if processed_message is None:
                        logger.debug("Message filtered by middleware")
                        return None
            
            # Get message type
            msg_type = self._get_message_type(processed_message)
            
            # Get appropriate handlers
            handlers = self.get_handlers(msg_type)
            
            # Process through handlers
            for handler in handlers:
                if hasattr(handler, 'handle'):
                    result = await handler.handle(processed_message)
                    if result:
                        return result
            
            # Log unhandled message
            logger.debug(f"Unhandled message type: {msg_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._trigger_event('error_occurred', error=e)
            return None
    
    def _get_message_type(self, message: Dict[str, Any]) -> str:
        """Determine message type"""
        if 'text' in message and message['text'].startswith('/'):
            return 'command'
        elif 'chat' in message and message['chat']['type'] == 'private':
            return 'private_message'
        elif 'chat' in message and message['chat']['type'] in ['group', 'supergroup']:
            return 'group_message'
        elif 'new_chat_members' in message:
            return 'new_member'
        elif 'left_chat_member' in message:
            return 'left_member'
        elif 'photo' in message:
            return 'photo'
        elif 'video' in message:
            return 'video'
        elif 'document' in message:
            return 'document'
        else:
            return 'unknown'
    
    async def _trigger_event(self, event_name: str, **kwargs):
        """Trigger an event"""
        if event_name in self.events:
            for handler in self.events[event_name]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(**kwargs)
                    else:
                        handler(**kwargs)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_name}: {e}")
    
    def on_event(self, event_name: str):
        """Decorator to register event handler"""
        def decorator(handler):
            if event_name in self.events:
                self.events[event_name].append(handler)
            return handler
        return decorator
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'initialized': self.is_initialized,
            'modules_loaded': sum(len(modules) for modules in self.modules.values()),
            'handlers_registered': sum(len(handlers) for handlers in self.handlers.values()),
            'middleware_count': len(self.middleware),
            'bot_info': self.bot_info,
            'timestamp': datetime.now().isoformat(),
        }