#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Message Collector
Collect and analyze messages for intelligence
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class MessageCollector:
    """Message Collection and Analysis System"""
    
    def __init__(self):
        self.config = Config
        self.memory_file = self.config.BASE_DIR / "intelligence" / "memory_store.json"
        self.message_buffer = []
        self.buffer_size = 100
        self.analysis_interval = 60  # seconds
        
        # Initialize memory file
        self._initialize_memory()
    
    def _initialize_memory(self):
        """Initialize memory storage"""
        if not self.memory_file.exists():
            initial_memory = {
                'messages': [],
                'keywords': {},
                'patterns': {},
                'statistics': {
                    'total_messages': 0,
                    'unique_users': set(),
                    'active_groups': set(),
                    'last_updated': datetime.now().isoformat(),
                }
            }
            JSONEngine.save_json(self.memory_file, initial_memory)
    
    async def collect(self, message: Dict[str, Any]):
        """Collect a message for analysis"""
        try:
            # Extract message info
            message_data = self._extract_message_data(message)
            
            # Add to buffer
            self.message_buffer.append(message_data)
            
            # Process buffer if full
            if len(self.message_buffer) >= self.buffer_size:
                await self._process_buffer()
            
            logger.debug(f"Message collected: {message_data.get('id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to collect message: {e}")
    
    def _extract_message_data(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant data from message"""
        message_id = message.get('message_id')
        chat_id = message.get('chat', {}).get('id')
        user_id = message.get('from', {}).get('id')
        text = message.get('text', '')
        timestamp = message.get('date', int(datetime.now().timestamp()))
        
        return {
            'id': message_id,
            'chat_id': chat_id,
            'user_id': user_id,
            'text': text,
            'timestamp': timestamp,
            'type': 'text' if text else 'other',
            'length': len(text) if text else 0,
            'words': len(text.split()) if text else 0,
            'collected_at': datetime.now().isoformat(),
        }
    
    async def _process_buffer(self):
        """Process message buffer"""
        if not self.message_buffer:
            return
        
        try:
            # Load current memory
            memory = JSONEngine.load_json(self.memory_file, {})
            if 'messages' not in memory:
                memory['messages'] = []
            
            # Add messages to memory
            memory['messages'].extend(self.message_buffer)
            
            # Keep only recent messages (last 1000)
            max_messages = 1000
            if len(memory['messages']) > max_messages:
                memory['messages'] = memory['messages'][-max_messages:]
            
            # Update statistics
            await self._update_statistics(memory)
            
            # Analyze for patterns
            await self._analyze_patterns(memory)
            
            # Save updated memory
            memory['last_updated'] = datetime.now().isoformat()
            JSONEngine.save_json(self.memory_file, memory)
            
            # Clear buffer
            self.message_buffer.clear()
            
            logger.info(f"Processed {len(self.message_buffer)} messages")
            
        except Exception as e:
            logger.error(f"Failed to process buffer: {e}")
    
    async def _update_statistics(self, memory: Dict[str, Any]):
        """Update message statistics"""
        if 'statistics' not in memory:
            memory['statistics'] = {
                'total_messages': 0,
                'unique_users': set(),
                'active_groups': set(),
                'last_updated': datetime.now().isoformat(),
            }
        
        stats = memory['statistics']
        messages = memory.get('messages', [])
        
        # Update counts
        stats['total_messages'] = len(messages)
        
        # Update unique users
        user_ids = {msg.get('user_id') for msg in messages if msg.get('user_id')}
        stats['unique_users'] = list(user_ids)
        
        # Update active groups
        chat_ids = {msg.get('chat_id') for msg in messages if msg.get('chat_id')}
        stats['active_groups'] = list(chat_ids)
        
        # Calculate message frequency
        if messages:
            recent_messages = [msg for msg in messages 
                             if self._is_recent(msg.get('timestamp'))]
            stats['recent_activity'] = len(recent_messages)
    
    async def _analyze_patterns(self, memory: Dict[str, Any]):
        """Analyze messages for patterns"""
        messages = memory.get('messages', [])
        
        if not messages:
            return
        
        # Extract keywords from recent messages
        recent_messages = [msg for msg in messages 
                         if self._is_recent(msg.get('timestamp'))]
        
        if not recent_messages:
            return
        
        # Simple keyword frequency analysis
        keyword_counts = {}
        
        for msg in recent_messages:
            text = msg.get('text', '')
            if text:
                words = text.lower().split()
                for word in words:
                    if len(word) > 3:  # Ignore short words
                        keyword_counts[word] = keyword_counts.get(word, 0) + 1
        
        # Store top keywords
        top_keywords = dict(sorted(
            keyword_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:50])
        
        memory['keywords'] = top_keywords
        
        # Detect common questions
        questions = [msg for msg in recent_messages 
                    if msg.get('text', '').endswith('?')]
        
        if questions:
            memory['recent_questions'] = [
                {'text': q.get('text'), 'count': 1} 
                for q in questions[:10]
            ]
    
    def _is_recent(self, timestamp, hours=24):
        """Check if timestamp is recent"""
        if not timestamp:
            return False
        
        try:
            if isinstance(timestamp, int):
                message_time = datetime.fromtimestamp(timestamp)
            else:
                message_time = datetime.fromisoformat(str(timestamp))
            
            time_diff = datetime.now() - message_time
            return time_diff.total_seconds() < (hours * 3600)
            
        except:
            return False
    
    async def get_recent_messages(self, chat_id: Optional[int] = None, 
                                limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            messages = memory.get('messages', [])
            
            # Filter by chat if specified
            if chat_id:
                messages = [msg for msg in messages 
                          if msg.get('chat_id') == chat_id]
            
            # Sort by timestamp (newest first)
            messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            # Apply limit
            return messages[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []
    
    async def get_chat_statistics(self, chat_id: int) -> Dict[str, Any]:
        """Get statistics for a specific chat"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            messages = memory.get('messages', [])
            
            # Filter messages for this chat
            chat_messages = [msg for msg in messages 
                           if msg.get('chat_id') == chat_id]
            
            if not chat_messages:
                return {'error': 'No messages found for this chat'}
            
            # Calculate statistics
            total_messages = len(chat_messages)
            
            # Unique users
            user_ids = {msg.get('user_id') for msg in chat_messages}
            unique_users = len(user_ids)
            
            # Message frequency
            recent_messages = [msg for msg in chat_messages 
                             if self._is_recent(msg.get('timestamp'))]
            recent_count = len(recent_messages)
            
            # Average message length
            text_messages = [msg for msg in chat_messages 
                           if msg.get('text')]
            avg_length = sum(len(msg.get('text', '')) for msg in text_messages) / max(1, len(text_messages))
            
            return {
                'chat_id': chat_id,
                'total_messages': total_messages,
                'unique_users': unique_users,
                'recent_activity': recent_count,
                'avg_message_length': round(avg_length, 1),
                'last_updated': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat statistics: {e}")
            return {'error': str(e)}
    
    async def get_keyword_analysis(self, limit: int = 20) -> Dict[str, Any]:
        """Get keyword analysis"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            keywords = memory.get('keywords', {})
            
            # Sort by frequency
            sorted_keywords = dict(sorted(
                keywords.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:limit])
            
            return {
                'total_keywords': len(keywords),
                'top_keywords': sorted_keywords,
                'analysis_time': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to get keyword analysis: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_messages(self, days: int = 30):
        """Cleanup messages older than specified days"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            messages = memory.get('messages', [])
            
            if not messages:
                return 0
            
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            # Filter out old messages
            filtered_messages = [
                msg for msg in messages 
                if msg.get('timestamp', 0) > cutoff_timestamp
            ]
            
            removed_count = len(messages) - len(filtered_messages)
            
            if removed_count > 0:
                memory['messages'] = filtered_messages
                JSONEngine.save_json(self.memory_file, memory)
                logger.info(f"Removed {removed_count} old messages")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}")
            return 0
    
    async def get_collector_stats(self) -> Dict[str, Any]:
        """Get collector statistics"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            stats = memory.get('statistics', {})
            
            return {
                'buffer_size': len(self.message_buffer),
                'total_messages': stats.get('total_messages', 0),
                'unique_users': len(stats.get('unique_users', [])),
                'active_groups': len(stats.get('active_groups', [])),
                'last_updated': stats.get('last_updated'),
                'memory_file_size': self.memory_file.stat().st_size if self.memory_file.exists() else 0,
            }
            
        except Exception as e:
            logger.error(f"Failed to get collector stats: {e}")
            return {'error': str(e)}