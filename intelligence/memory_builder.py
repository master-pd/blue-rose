#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Memory Builder
Build and manage conversation memory
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class MemoryBuilder:
    """Conversation Memory Building System"""
    
    def __init__(self):
        self.config = Config
        self.memory_file = self.config.BASE_DIR / "intelligence" / "memory_store.json"
        self.conversation_memory = {}
        self.max_conversation_length = 20
        self.max_memory_items = 1000
        
        # Initialize memory
        self._initialize_memory()
    
    def _initialize_memory(self):
        """Initialize memory storage"""
        if not self.memory_file.exists():
            initial_memory = {
                'conversations': {},
                'user_profiles': {},
                'group_contexts': {},
                'learned_patterns': {},
                'statistics': {
                    'total_conversations': 0,
                    'active_users': 0,
                    'memory_size': 0,
                    'last_updated': datetime.now().isoformat(),
                }
            }
            JSONEngine.save_json(self.memory_file, initial_memory)
    
    async def add_to_memory(self, message: Dict[str, Any], 
                          response: Optional[str] = None):
        """Add message to conversation memory"""
        try:
            # Extract message info
            chat_id = message.get('chat', {}).get('id')
            user_id = message.get('from', {}).get('id')
            text = message.get('text', '')
            timestamp = message.get('date', int(datetime.now().timestamp()))
            
            if not chat_id or not user_id or not text:
                return False
            
            # Load current memory
            memory = JSONEngine.load_json(self.memory_file, {})
            
            # Create conversation key
            conv_key = f"{chat_id}_{user_id}"
            
            # Initialize conversation if not exists
            if conv_key not in memory['conversations']:
                memory['conversations'][conv_key] = {
                    'chat_id': chat_id,
                    'user_id': user_id,
                    'messages': [],
                    'start_time': timestamp,
                    'last_activity': timestamp,
                    'message_count': 0,
                    'topics': set(),
                }
            
            # Add message to conversation
            message_entry = {
                'text': text,
                'timestamp': timestamp,
                'type': 'user',
                'response': response,
                'message_id': message.get('message_id'),
            }
            
            conv = memory['conversations'][conv_key]
            conv['messages'].append(message_entry)
            conv['last_activity'] = timestamp
            conv['message_count'] += 1
            
            # Limit conversation length
            if len(conv['messages']) > self.max_conversation_length:
                conv['messages'] = conv['messages'][-self.max_conversation_length:]
            
            # Update user profile
            await self._update_user_profile(memory, user_id, text, chat_id)
            
            # Update group context
            await self._update_group_context(memory, chat_id, text, user_id)
            
            # Learn patterns
            await self._learn_patterns(memory, text, response)
            
            # Update statistics
            await self._update_statistics(memory)
            
            # Save memory
            JSONEngine.save_json(self.memory_file, memory)
            
            logger.debug(f"Added to memory: {conv_key} - {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to memory: {e}")
            return False
    
    async def _update_user_profile(self, memory: Dict[str, Any], user_id: int,
                                 text: str, chat_id: int):
        """Update user profile based on message"""
        if 'user_profiles' not in memory:
            memory['user_profiles'] = {}
        
        user_key = str(user_id)
        
        if user_key not in memory['user_profiles']:
            memory['user_profiles'][user_key] = {
                'user_id': user_id,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'total_messages': 0,
                'active_chats': set(),
                'common_words': {},
                'interests': set(),
                'behavior_patterns': {},
            }
        
        profile = memory['user_profiles'][user_key]
        profile['last_seen'] = datetime.now().isoformat()
        profile['total_messages'] += 1
        profile['active_chats'].add(str(chat_id))
        
        # Analyze text for interests
        words = text.lower().split()
        for word in words:
            if len(word) > 3:  # Only consider meaningful words
                profile['common_words'][word] = profile['common_words'].get(word, 0) + 1
        
        # Keep only top 50 words
        if len(profile['common_words']) > 50:
            sorted_words = sorted(profile['common_words'].items(), 
                                key=lambda x: x[1], reverse=True)[:50]
            profile['common_words'] = dict(sorted_words)
        
        # Convert sets to lists for JSON serialization
        profile['active_chats'] = list(profile['active_chats'])
        profile['interests'] = list(profile['interests'])
    
    async def _update_group_context(self, memory: Dict[str, Any], chat_id: int,
                                  text: str, user_id: int):
        """Update group context"""
        if 'group_contexts' not in memory:
            memory['group_contexts'] = {}
        
        group_key = str(chat_id)
        
        if group_key not in memory['group_contexts']:
            memory['group_contexts'][group_key] = {
                'chat_id': chat_id,
                'active_users': set(),
                'recent_topics': [],
                'message_count': 0,
                'last_activity': datetime.now().isoformat(),
            }
        
        context = memory['group_contexts'][group_key]
        context['active_users'].add(str(user_id))
        context['message_count'] += 1
        context['last_activity'] = datetime.now().isoformat()
        
        # Add topic if conversation seems substantive
        if len(text.split()) > 5:  # More than 5 words
            topic_info = {
                'text': text[:100],  # First 100 chars
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
            }
            context['recent_topics'].append(topic_info)
            
            # Keep only recent topics
            if len(context['recent_topics']) > 10:
                context['recent_topics'] = context['recent_topics'][-10:]
        
        # Convert sets to lists
        context['active_users'] = list(context['active_users'])
    
    async def _learn_patterns(self, memory: Dict[str, Any], text: str,
                            response: Optional[str]):
        """Learn conversation patterns"""
        if 'learned_patterns' not in memory:
            memory['learned_patterns'] = {
                'question_response': {},
                'greeting_response': {},
                'common_phrases': {},
            }
        
        patterns = memory['learned_patterns']
        
        # Learn question-response patterns
        if text.endswith('?') and response:
            question_key = text.lower().strip('? ')
            if question_key not in patterns['question_response']:
                patterns['question_response'][question_key] = {
                    'responses': {},
                    'count': 0,
                }
            
            pattern = patterns['question_response'][question_key]
            pattern['count'] += 1
            
            # Track response frequency
            response_key = response.lower()[:100]  # First 100 chars
            pattern['responses'][response_key] = pattern['responses'].get(response_key, 0) + 1
        
        # Learn greeting patterns
        greetings = ['hello', 'hi', 'hey', 'সালাম', 'হ্যালো', 'আসসালামুয়ালাইকুম']
        if any(greeting in text.lower() for greeting in greetings) and response:
            greeting_key = 'greeting'
            if greeting_key not in patterns['greeting_response']:
                patterns['greeting_response'][greeting_key] = {
                    'responses': {},
                    'count': 0,
                }
            
            pattern = patterns['greeting_response'][greeting_key]
            pattern['count'] += 1
            
            response_key = response.lower()[:100]
            pattern['responses'][response_key] = pattern['responses'].get(response_key, 0) + 1
    
    async def _update_statistics(self, memory: Dict[str, Any]):
        """Update memory statistics"""
        if 'statistics' not in memory:
            memory['statistics'] = {}
        
        stats = memory['statistics']
        stats['total_conversations'] = len(memory.get('conversations', {}))
        stats['active_users'] = len(memory.get('user_profiles', {}))
        
        # Calculate memory size (approximate)
        import json
        memory_json = json.dumps(memory)
        stats['memory_size'] = len(memory_json.encode('utf-8'))
        
        stats['last_updated'] = datetime.now().isoformat()
    
    async def get_conversation_history(self, chat_id: int, user_id: int,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a user in a chat"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            conv_key = f"{chat_id}_{user_id}"
            
            if conv_key not in memory.get('conversations', {}):
                return []
            
            conv = memory['conversations'][conv_key]
            messages = conv.get('messages', [])
            
            # Apply limit
            return messages[-limit:] if limit > 0 else messages
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user profile from memory"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            user_key = str(user_id)
            
            if user_key not in memory.get('user_profiles', {}):
                return {
                    'user_id': user_id,
                    'exists': False,
                    'message': 'User profile not found',
                }
            
            profile = memory['user_profiles'][user_key].copy()
            profile['exists'] = True
            
            # Calculate activity level
            last_seen = datetime.fromisoformat(profile['last_seen'])
            days_inactive = (datetime.now() - last_seen).days
            profile['days_inactive'] = days_inactive
            
            # Get top interests
            if profile['common_words']:
                top_words = sorted(profile['common_words'].items(),
                                 key=lambda x: x[1], reverse=True)[:10]
                profile['top_interests'] = [word for word, _ in top_words]
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return {
                'user_id': user_id,
                'exists': False,
                'error': str(e),
            }
    
    async def get_group_context(self, chat_id: int) -> Dict[str, Any]:
        """Get group context from memory"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            group_key = str(chat_id)
            
            if group_key not in memory.get('group_contexts', {}):
                return {
                    'chat_id': chat_id,
                    'exists': False,
                    'message': 'Group context not found',
                }
            
            context = memory['group_contexts'][group_key].copy()
            context['exists'] = True
            
            # Calculate activity metrics
            last_activity = datetime.fromisoformat(context['last_activity'])
            hours_inactive = (datetime.now() - last_activity).total_seconds() / 3600
            context['hours_inactive'] = round(hours_inactive, 1)
            
            # Get active user count
            context['active_user_count'] = len(context.get('active_users', []))
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get group context: {e}")
            return {
                'chat_id': chat_id,
                'exists': False,
                'error': str(e),
            }
    
    async def get_learned_patterns(self, pattern_type: str = None) -> Dict[str, Any]:
        """Get learned conversation patterns"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            patterns = memory.get('learned_patterns', {})
            
            if pattern_type:
                if pattern_type in patterns:
                    return {
                        'pattern_type': pattern_type,
                        'patterns': patterns[pattern_type],
                        'count': len(patterns[pattern_type]),
                    }
                else:
                    return {
                        'pattern_type': pattern_type,
                        'patterns': {},
                        'count': 0,
                        'message': f'Pattern type not found: {pattern_type}',
                    }
            
            # Return all patterns
            result = {}
            for p_type, p_data in patterns.items():
                result[p_type] = {
                    'count': len(p_data),
                    'example_count': sum(item.get('count', 0) for item in p_data.values()),
                }
            
            return {
                'all_patterns': result,
                'total_pattern_types': len(patterns),
            }
            
        except Exception as e:
            logger.error(f"Failed to get learned patterns: {e}")
            return {'error': str(e)}
    
    async def find_similar_conversations(self, text: str, 
                                       limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar past conversations"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            conversations = memory.get('conversations', {})
            
            similar_conversations = []
            
            for conv_key, conv_data in conversations.items():
                messages = conv_data.get('messages', [])
                
                for msg in messages[-5:]:  # Check last 5 messages
                    msg_text = msg.get('text', '')
                    
                    # Simple similarity check (in real implementation, use similarity engine)
                    if msg_text and text.lower() in msg_text.lower():
                        similar_conversations.append({
                            'conversation_key': conv_key,
                            'matched_text': msg_text,
                            'response': msg.get('response'),
                            'timestamp': msg.get('timestamp'),
                            'chat_id': conv_data.get('chat_id'),
                            'user_id': conv_data.get('user_id'),
                        })
                        
                        if len(similar_conversations) >= limit:
                            break
                
                if len(similar_conversations) >= limit:
                    break
            
            return similar_conversations
            
        except Exception as e:
            logger.error(f"Failed to find similar conversations: {e}")
            return []
    
    async def cleanup_old_memory(self, days: int = 30):
        """Cleanup old memory entries"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            removed_count = 0
            
            # Cleanup old conversations
            conversations = memory.get('conversations', {})
            keys_to_remove = []
            
            for conv_key, conv_data in conversations.items():
                last_activity = conv_data.get('last_activity', 0)
                if last_activity < cutoff_timestamp:
                    keys_to_remove.append(conv_key)
            
            for key in keys_to_remove:
                del conversations[key]
                removed_count += 1
            
            # Cleanup inactive user profiles
            user_profiles = memory.get('user_profiles', {})
            user_keys_to_remove = []
            
            for user_key, profile in user_profiles.items():
                last_seen_str = profile.get('last_seen')
                if last_seen_str:
                    try:
                        last_seen = datetime.fromisoformat(last_seen_str)
                        if last_seen < cutoff_time:
                            user_keys_to_remove.append(user_key)
                    except:
                        pass
            
            for key in user_keys_to_remove:
                del user_profiles[key]
                removed_count += 1
            
            # Save cleaned memory
            JSONEngine.save_json(self.memory_file, memory)
            
            logger.info(f"Cleaned up {removed_count} old memory entries")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old memory: {e}")
            return 0
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            memory = JSONEngine.load_json(self.memory_file, {})
            stats = memory.get('statistics', {})
            
            return {
                'total_conversations': stats.get('total_conversations', 0),
                'active_users': stats.get('active_users', 0),
                'memory_size_bytes': stats.get('memory_size', 0),
                'memory_size_mb': round(stats.get('memory_size', 0) / (1024 * 1024), 2),
                'group_contexts': len(memory.get('group_contexts', {})),
                'learned_patterns': len(memory.get('learned_patterns', {})),
                'last_updated': stats.get('last_updated'),
                'file_size': self.memory_file.stat().st_size if self.memory_file.exists() else 0,
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {'error': str(e)}