#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Event Loop Manager
Handles asynchronous event processing
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from collections import deque

from config import Config

logger = logging.getLogger(__name__)

class EventLoop:
    """Asynchronous Event Loop Manager"""
    
    def __init__(self):
        self.config = Config
        self.loop = None
        self.tasks = []
        self.event_queue = deque(maxlen=1000)
        self.is_running = False
        self.processors = {}
        
    async def initialize(self) -> bool:
        """Initialize event loop"""
        try:
            logger.info("Initializing event loop...")
            
            # Get or create event loop
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            
            # Initialize processors
            self.processors = {
                'message': self._process_message,
                'command': self._process_command,
                'callback': self._process_callback,
                'timer': self._process_timer,
                'error': self._process_error,
            }
            
            logger.info("✅ Event loop initialized!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize event loop: {e}")
            return False
    
    async def start(self):
        """Start event loop processing"""
        if self.is_running:
            logger.warning("Event loop already running!")
            return
        
        self.is_running = True
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._queue_processor()),
            asyncio.create_task(self._health_monitor()),
            asyncio.create_task(self._cleanup_task()),
        ]
        
        logger.info("✅ Event loop started!")
    
    async def stop(self):
        """Stop event loop processing"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks = []
        logger.info("✅ Event loop stopped!")
    
    async def add_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Add event to processing queue"""
        try:
            event = {
                'type': event_type,
                'data': data,
                'timestamp': asyncio.get_event_loop().time(),
                'id': len(self.event_queue) + 1,
            }
            
            self.event_queue.append(event)
            
            logger.debug(f"Event added to queue: {event_type} (ID: {event['id']})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add event: {e}")
            return False
    
    async def _queue_processor(self):
        """Process events from queue"""
        logger.info("Starting queue processor...")
        
        while self.is_running:
            try:
                if self.event_queue:
                    event = self.event_queue.popleft()
                    await self._process_event(event)
                
                # Small delay to prevent CPU hogging
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
                await asyncio.sleep(1)
        
        logger.info("Queue processor stopped")
    
    async def _process_event(self, event: Dict[str, Any]):
        """Process a single event"""
        try:
            event_type = event['type']
            
            if event_type in self.processors:
                processor = self.processors[event_type]
                await processor(event['data'])
            else:
                logger.warning(f"No processor for event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Failed to process event {event.get('id', 'unknown')}: {e}")
            
            # Add error event
            error_event = {
                'original_event': event,
                'error': str(e),
            }
            await self.add_event('error', error_event)
    
    async def _process_message(self, message: Dict[str, Any]):
        """Process message event"""
        # This would be connected to the Telegram bot API
        # For now, just log it
        logger.debug(f"Processing message: {message.get('text', 'No text')}")
        
        # Add human-like delay if enabled
        if self.config.HUMANIZE_DELAY:
            import random
            delay = random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY)
            await asyncio.sleep(delay)
    
    async def _process_command(self, command: Dict[str, Any]):
        """Process command event"""
        logger.debug(f"Processing command: {command.get('command', 'Unknown')}")
        
        # Command processing logic would go here
        # Would connect to command router
    
    async def _process_callback(self, callback: Dict[str, Any]):
        """Process callback query event"""
        logger.debug(f"Processing callback: {callback.get('data', 'No data')}")
        
        # Callback processing logic would go here
    
    async def _process_timer(self, timer: Dict[str, Any]):
        """Process timer event"""
        logger.debug(f"Processing timer: {timer.get('name', 'Unknown timer')}")
        
        # Timer/reminder processing logic
    
    async def _process_error(self, error: Dict[str, Any]):
        """Process error event"""
        logger.error(f"Error event: {error.get('error', 'Unknown error')}")
        
        # Error handling logic
        # Would connect to crash handler
    
    async def _health_monitor(self):
        """Monitor event loop health"""
        logger.info("Starting health monitor...")
        
        while self.is_running:
            try:
                # Check queue size
                queue_size = len(self.event_queue)
                if queue_size > 500:
                    logger.warning(f"Event queue getting large: {queue_size} events")
                
                # Check task count
                task_count = len(asyncio.all_tasks())
                if task_count > 100:
                    logger.warning(f"High task count: {task_count} tasks")
                
                # Log statistics every 5 minutes
                if int(asyncio.get_event_loop().time()) % 300 == 0:
                    logger.info(f"Event loop stats - Queue: {queue_size}, Tasks: {task_count}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)
        
        logger.info("Health monitor stopped")
    
    async def _cleanup_task(self):
        """Cleanup old tasks"""
        logger.info("Starting cleanup task...")
        
        while self.is_running:
            try:
                # Check for stale tasks
                current_time = asyncio.get_event_loop().time()
                
                # This would track task creation times and clean up old ones
                # For now, just sleep
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(300)
        
        logger.info("Cleanup task stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event loop statistics"""
        return {
            'is_running': self.is_running,
            'queue_size': len(self.event_queue),
            'tasks_count': len(self.tasks),
            'processors': list(self.processors.keys()),
        }