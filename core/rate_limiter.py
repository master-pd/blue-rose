#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Rate Limiter
Prevent abuse through rate limiting
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from collections import defaultdict

from config import Config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate Limiting System"""
    
    def __init__(self):
        self.config = Config
        self.limits = self.config.RATE_LIMITS
        
        # Store request timestamps
        self.user_requests = defaultdict(list)  # user_id -> list of timestamps
        self.chat_requests = defaultdict(list)  # chat_id -> list of timestamps
        self.command_requests = defaultdict(lambda: defaultdict(list))  # command -> user_id -> timestamps
        
        # Store blocked entities
        self.blocked_users = set()
        self.blocked_chats = set()
        
        # Cleanup task
        self.cleanup_task = None
        
    async def start(self):
        """Start rate limiter"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Rate limiter started")
    
    async def stop(self):
        """Stop rate limiter"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Rate limiter stopped")
    
    async def check_limit(self, user_id: int, chat_id: Optional[int] = None,
                        command: Optional[str] = None) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        current_time = time.time()
        
        # Check if user is blocked
        if user_id in self.blocked_users:
            return {
                'allowed': False,
                'reason': 'user_blocked',
                'retry_after': 3600,  # 1 hour
            }
        
        # Check if chat is blocked
        if chat_id and chat_id in self.blocked_chats:
            return {
                'allowed': False,
                'reason': 'chat_blocked',
                'retry_after': 3600,
            }
        
        # Check user limits
        user_allowed, user_wait = self._check_user_limit(user_id, current_time)
        if not user_allowed:
            return {
                'allowed': False,
                'reason': 'user_rate_limit',
                'retry_after': user_wait,
            }
        
        # Check chat limits
        if chat_id:
            chat_allowed, chat_wait = self._check_chat_limit(chat_id, current_time)
            if not chat_allowed:
                return {
                    'allowed': False,
                    'reason': 'chat_rate_limit',
                    'retry_after': chat_wait,
                }
        
        # Check command limits
        if command:
            cmd_allowed, cmd_wait = self._check_command_limit(command, user_id, current_time)
            if not cmd_allowed:
                return {
                    'allowed': False,
                    'reason': 'command_rate_limit',
                    'retry_after': cmd_wait,
                }
        
        # All checks passed
        return {
            'allowed': True,
            'reason': 'ok',
            'retry_after': 0,
        }
    
    def _check_user_limit(self, user_id: int, current_time: float) -> tuple[bool, float]:
        """Check user-level rate limit"""
        window = 60  # 1 minute window
        max_requests = self.limits.get('commands_per_minute', 30)
        
        # Clean old requests
        self.user_requests[user_id] = [
            t for t in self.user_requests[user_id]
            if current_time - t < window
        ]
        
        # Check limit
        if len(self.user_requests[user_id]) >= max_requests:
            # Calculate wait time
            oldest = min(self.user_requests[user_id])
            wait_time = window - (current_time - oldest)
            return False, max(1, wait_time)
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        return True, 0
    
    def _check_chat_limit(self, chat_id: int, current_time: float) -> tuple[bool, float]:
        """Check chat-level rate limit"""
        window = 1  # 1 second window
        max_requests = self.limits.get('messages_per_second', 20)
        
        # Clean old requests
        self.chat_requests[chat_id] = [
            t for t in self.chat_requests[chat_id]
            if current_time - t < window
        ]
        
        # Check limit
        if len(self.chat_requests[chat_id]) >= max_requests:
            # Calculate wait time
            oldest = min(self.chat_requests[chat_id])
            wait_time = window - (current_time - oldest)
            return False, max(0.1, wait_time)
        
        # Add current request
        self.chat_requests[chat_id].append(current_time)
        return True, 0
    
    def _check_command_limit(self, command: str, user_id: int, 
                           current_time: float) -> tuple[bool, float]:
        """Check command-specific rate limit"""
        window = 60  # 1 minute window
        max_requests = 10  # Max 10 of same command per minute per user
        
        # Clean old requests
        self.command_requests[command][user_id] = [
            t for t in self.command_requests[command][user_id]
            if current_time - t < window
        ]
        
        # Check limit
        if len(self.command_requests[command][user_id]) >= max_requests:
            # Calculate wait time
            oldest = min(self.command_requests[command][user_id])
            wait_time = window - (current_time - oldest)
            return False, max(1, wait_time)
        
        # Add current request
        self.command_requests[command][user_id].append(current_time)
        return True, 0
    
    async def record_request(self, user_id: int, chat_id: Optional[int] = None,
                           command: Optional[str] = None):
        """Record a request (alternative to check_limit)"""
        current_time = time.time()
        
        # Record user request
        self.user_requests[user_id].append(current_time)
        
        # Record chat request
        if chat_id:
            self.chat_requests[chat_id].append(current_time)
        
        # Record command request
        if command:
            self.command_requests[command][user_id].append(current_time)
    
    async def block_user(self, user_id: int, duration: int = 3600):
        """Block a user temporarily"""
        self.blocked_users.add(user_id)
        logger.warning(f"Blocked user {user_id} for {duration} seconds")
        
        # Schedule unblock
        asyncio.create_task(self._unblock_user_after(user_id, duration))
    
    async def block_chat(self, chat_id: int, duration: int = 3600):
        """Block a chat temporarily"""
        self.blocked_chats.add(chat_id)
        logger.warning(f"Blocked chat {chat_id} for {duration} seconds")
        
        # Schedule unblock
        asyncio.create_task(self._unblock_chat_after(chat_id, duration))
    
    async def _unblock_user_after(self, user_id: int, duration: int):
        """Unblock user after duration"""
        await asyncio.sleep(duration)
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            logger.info(f"Unblocked user {user_id}")
    
    async def _unblock_chat_after(self, chat_id: int, duration: int):
        """Unblock chat after duration"""
        await asyncio.sleep(duration)
        if chat_id in self.blocked_chats:
            self.blocked_chats.remove(chat_id)
            logger.info(f"Unblocked chat {chat_id}")
    
    async def _cleanup_loop(self):
        """Cleanup old entries periodically"""
        while True:
            try:
                await self._cleanup_old_entries()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_entries(self):
        """Cleanup old rate limit entries"""
        current_time = time.time()
        cleanup_threshold = 300  # 5 minutes
        
        # Clean user requests
        for user_id in list(self.user_requests.keys()):
            self.user_requests[user_id] = [
                t for t in self.user_requests[user_id]
                if current_time - t < cleanup_threshold
            ]
            if not self.user_requests[user_id]:
                del self.user_requests[user_id]
        
        # Clean chat requests
        for chat_id in list(self.chat_requests.keys()):
            self.chat_requests[chat_id] = [
                t for t in self.chat_requests[chat_id]
                if current_time - t < cleanup_threshold
            ]
            if not self.chat_requests[chat_id]:
                del self.chat_requests[chat_id]
        
        # Clean command requests
        for command in list(self.command_requests.keys()):
            for user_id in list(self.command_requests[command].keys()):
                self.command_requests[command][user_id] = [
                    t for t in self.command_requests[command][user_id]
                    if current_time - t < cleanup_threshold
                ]
                if not self.command_requests[command][user_id]:
                    del self.command_requests[command][user_id]
            
            if not self.command_requests[command]:
                del self.command_requests[command]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            'blocked_users': len(self.blocked_users),
            'blocked_chats': len(self.blocked_chats),
            'tracked_users': len(self.user_requests),
            'tracked_chats': len(self.chat_requests),
            'tracked_commands': len(self.command_requests),
            'limits': self.limits,
        }