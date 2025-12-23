#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Memory Decay
Gradually forget old and unimportant memories
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class MemoryDecay:
    """Memory Decay and Forgetting System"""
    
    def __init__(self):
        self.config = Config
        self.memory_file = self.config.BASE_DIR / "intelligence" / "memory_store.json"
        
        # Decay parameters
        self.decay_rates = {
            'conversations': 0.1,      # 10% decay per day for old conversations
            'user_profiles': 0.05,     # 5% decay per day for inactive users
            'learned_patterns': 0.02,  # 2% decay per day for unused patterns
            'group_contexts': 0.15,    # 15% decay per day for inactive groups
        }
        
        # Retention periods (in days)
        self.retention_periods = {
            'important_conversations': 90,    # Keep important convos for 90 days
            'regular_conversations': 30,      # Regular convos for 30 days
            'user_profiles': 180,             # User profiles for 180 days
            'learned_patterns': 365,          # Keep patterns for 1 year
            'group_contexts': 60,             # Group contexts for 60 days
        }
        
        # Importance scoring weights
        self.importance_weights = {
            'message_count': 0.3,
            'recency': 0.25,
            'response_quality': 0.2,
            'user_importance': 0.15,
            'pattern_usefulness': 0.1,
        }
    
    async def apply_decay(self):
        """Apply memory decay to all stored memories"""
        try:
            logger.info("Applying memory decay...")
            
            # Load memory
            memory = JSONEngine.load_json(self.memory_file, {})
            if not memory:
                logger.warning("No memory found to decay")
                return
            
            original_size = len(str(memory))
            
            # Apply decay to different memory types
            decayed_count = 0
            
            # 1. Decay conversations
            if 'conversations' in memory:
                decayed = await self._decay_conversations(memory['conversations'])
                decayed_count += decayed
            
            # 2. Decay user profiles
            if 'user_profiles' in memory:
                decayed = await self._decay_user_profiles(memory['user_profiles'])
                decayed_count += decayed
            
            # 3. Decay learned patterns
            if 'learned_patterns' in memory:
                decayed = await self._decay_learned_patterns(memory['learned_patterns'])
                decayed_count += decayed
            
            # 4. Decay group contexts
            if 'group_contexts' in memory:
                decayed = await self._decay_group_contexts(memory['group_contexts'])
                decayed_count += decayed
            
            # Save decayed memory
            JSONEngine.save_json(self.memory_file, memory)
            
            new_size = len(str(memory))
            reduction = original_size - new_size
            
            logger.info(f"Memory decay applied: {decayed_count} items affected, "
                       f"size reduced by {reduction} bytes")
            
            return {
                'decayed_items': decayed_count,
                'size_reduction_bytes': reduction,
                'size_reduction_percent': round((reduction / original_size * 100), 2) if original_size > 0 else 0,
                'timestamp': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to apply memory decay: {e}")
            return {'error': str(e)}
    
    async def _decay_conversations(self, conversations: Dict[str, Any]) -> int:
        """Apply decay to conversations"""
        decayed_count = 0
        current_time = datetime.now()
        
        conversations_to_remove = []
        
        for conv_key, conv_data in conversations.items():
            # Calculate conversation importance
            importance = await self._calculate_conversation_importance(conv_data)
            
            # Calculate age
            last_activity = conv_data.get('last_activity')
            if isinstance(last_activity, int):
                last_active = datetime.fromtimestamp(last_activity)
            else:
                # Try to parse as ISO string
                try:
                    last_active = datetime.fromisoformat(str(last_activity))
                except:
                    last_active = current_time - timedelta(days=365)  # Very old
            
            age_days = (current_time - last_active).days
            
            # Determine retention period based on importance
            if importance > 0.7:
                retention = self.retention_periods['important_conversations']
            else:
                retention = self.retention_periods['regular_conversations']
            
            # Check if should be removed
            if age_days > retention:
                conversations_to_remove.append(conv_key)
                decayed_count += 1
            else:
                # Apply gradual decay to older conversations
                if age_days > 7:  # Only decay conversations older than 7 days
                    decay_factor = 1.0 - (self.decay_rates['conversations'] * (age_days / 30))
                    decay_factor = max(0.1, decay_factor)  # Don't decay below 10%
                    
                    # Reduce message count (simulating forgetting)
                    if 'message_count' in conv_data:
                        conv_data['message_count'] = int(conv_data['message_count'] * decay_factor)
                    
                    # Trim old messages if too many
                    messages = conv_data.get('messages', [])
                    if len(messages) > 10:
                        conv_data['messages'] = messages[-10:]  # Keep only last 10 messages
                    
                    decayed_count += 1
        
        # Remove old conversations
        for conv_key in conversations_to_remove:
            del conversations[conv_key]
        
        return decayed_count
    
    async def _calculate_conversation_importance(self, conv_data: Dict[str, Any]) -> float:
        """Calculate importance score for a conversation"""
        importance = 0.0
        
        # 1. Message count factor
        message_count = conv_data.get('message_count', 0)
        message_score = min(1.0, message_count / 50)  # Max score at 50 messages
        importance += message_score * self.importance_weights['message_count']
        
        # 2. Recency factor
        last_activity = conv_data.get('last_activity')
        current_time = datetime.now().timestamp()
        
        if isinstance(last_activity, (int, float)):
            # Convert to days since activity
            days_since = (current_time - last_activity) / (24 * 3600)
            recency_score = max(0.0, 1.0 - (days_since / 30))  # Linear decay over 30 days
            importance += recency_score * self.importance_weights['recency']
        
        # 3. Response quality factor (if available)
        messages = conv_data.get('messages', [])
        if messages:
            # Count messages with responses
            responded_messages = sum(1 for msg in messages if msg.get('response'))
            if len(messages) > 0:
                response_ratio = responded_messages / len(messages)
                importance += response_ratio * self.importance_weights['response_quality']
        
        return min(1.0, importance)  # Cap at 1.0
    
    async def _decay_user_profiles(self, user_profiles: Dict[str, Any]) -> int:
        """Apply decay to user profiles"""
        decayed_count = 0
        current_time = datetime.now()
        cutoff_days = self.retention_periods['user_profiles']
        
        users_to_remove = []
        
        for user_key, profile in user_profiles.items():
            # Check last seen
            last_seen_str = profile.get('last_seen')
            if not last_seen_str:
                users_to_remove.append(user_key)
                continue
            
            try:
                last_seen = datetime.fromisoformat(last_seen_str)
                days_inactive = (current_time - last_seen).days
                
                if days_inactive > cutoff_days:
                    users_to_remove.append(user_key)
                    decayed_count += 1
                elif days_inactive > 30:
                    # Apply decay to inactive users
                    decay_factor = 1.0 - (self.decay_rates['user_profiles'] * (days_inactive / 30))
                    decay_factor = max(0.3, decay_factor)  # Don't decay below 30%
                    
                    # Reduce common words count
                    if 'common_words' in profile:
                        common_words = profile['common_words']
                        for word in list(common_words.keys()):
                            common_words[word] = int(common_words[word] * decay_factor)
                            if common_words[word] < 2:  # Remove rarely used words
                                del common_words[word]
                    
                    # Reduce interests
                    if 'interests' in profile and len(profile['interests']) > 10:
                        profile['interests'] = profile['interests'][:10]  # Keep only top 10
                    
                    decayed_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to process user profile {user_key}: {e}")
                users_to_remove.append(user_key)
        
        # Remove inactive users
        for user_key in users_to_remove:
            del user_profiles[user_key]
        
        return decayed_count
    
    async def _decay_learned_patterns(self, learned_patterns: Dict[str, Any]) -> int:
        """Apply decay to learned patterns"""
        decayed_count = 0
        current_time = datetime.now()
        
        for pattern_type, patterns in learned_patterns.items():
            if not isinstance(patterns, dict):
                continue
            
            patterns_to_remove = []
            
            for pattern_key, pattern_data in patterns.items():
                # Calculate pattern usefulness
                usefulness = await self._calculate_pattern_usefulness(pattern_data)
                
                # Get last used timestamp (approximate)
                last_used = pattern_data.get('last_used')
                if not last_used:
                    # Use count as proxy for recency
                    count = pattern_data.get('count', 0)
                    if count < 3:  # Rarely used patterns
                        patterns_to_remove.append(pattern_key)
                        decayed_count += 1
                    continue
                
                # Check if pattern is old and not useful
                try:
                    if isinstance(last_used, (int, float)):
                        last_used_dt = datetime.fromtimestamp(last_used)
                    else:
                        last_used_dt = datetime.fromisoformat(str(last_used))
                    
                    days_since_use = (current_time - last_used_dt).days
                    
                    if days_since_use > self.retention_periods['learned_patterns']:
                        patterns_to_remove.append(pattern_key)
                        decayed_count += 1
                    elif days_since_use > 90 and usefulness < 0.3:
                        # Old and not useful patterns
                        patterns_to_remove.append(pattern_key)
                        decayed_count += 1
                    elif days_since_use > 30:
                        # Apply gradual decay
                        decay_factor = 1.0 - (self.decay_rates['learned_patterns'] * (days_since_use / 90))
                        
                        # Reduce counts
                        if 'count' in pattern_data:
                            pattern_data['count'] = int(pattern_data['count'] * decay_factor)
                        
                        if 'responses' in pattern_data:
                            responses = pattern_data['responses']
                            for response_key in list(responses.keys()):
                                responses[response_key] = int(responses[response_key] * decay_factor)
                                if responses[response_key] < 2:
                                    del responses[response_key]
                        
                        decayed_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to process pattern {pattern_key}: {e}")
            
            # Remove old/unused patterns
            for pattern_key in patterns_to_remove:
                del patterns[pattern_key]
        
        return decayed_count
    
    async def _calculate_pattern_usefulness(self, pattern_data: Dict[str, Any]) -> float:
        """Calculate usefulness score for a pattern"""
        if not pattern_data:
            return 0.0
        
        # Factors for usefulness:
        # 1. Frequency of use (count)
        # 2. Variety of responses
        # 3. Recency of use
        
        count = pattern_data.get('count', 0)
        responses = pattern_data.get('responses', {})
        
        if count == 0:
            return 0.0
        
        # Frequency score (logarithmic, so 10 uses is good, 100 is great)
        freq_score = min(1.0, count / 50)
        
        # Variety score (more response options = more useful)
        response_count = len(responses)
        variety_score = min(1.0, response_count / 5)
        
        # Combined usefulness
        usefulness = (freq_score * 0.6) + (variety_score * 0.4)
        
        return usefulness
    
    async def _decay_group_contexts(self, group_contexts: Dict[str, Any]) -> int:
        """Apply decay to group contexts"""
        decayed_count = 0
        current_time = datetime.now()
        cutoff_days = self.retention_periods['group_contexts']
        
        groups_to_remove = []
        
        for group_key, context in group_contexts.items():
            # Check last activity
            last_activity_str = context.get('last_activity')
            if not last_activity_str:
                groups_to_remove.append(group_key)
                continue
            
            try:
                last_activity = datetime.fromisoformat(last_activity_str)
                days_inactive = (current_time - last_activity).days
                
                if days_inactive > cutoff_days:
                    groups_to_remove.append(group_key)
                    decayed_count += 1
                elif days_inactive > 14:
                    # Apply decay to inactive groups
                    decay_factor = 1.0 - (self.decay_rates['group_contexts'] * (days_inactive / 30))
                    
                    # Reduce active users list
                    if 'active_users' in context and len(context['active_users']) > 20:
                        context['active_users'] = context['active_users'][:20]
                    
                    # Trim recent topics
                    if 'recent_topics' in context and len(context['recent_topics']) > 5:
                        context['recent_topics'] = context['recent_topics'][-5:]
                    
                    decayed_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to process group context {group_key}: {e}")
                groups_to_remove.append(group_key)
        
        # Remove inactive groups
        for group_key in groups_to_remove:
            del group_contexts[group_key]
        
        return decayed_count
    
    async def optimize_memory(self):
        """Optimize memory storage"""
        try:
            logger.info("Optimizing memory storage...")
            
            # Load memory
            memory = JSONEngine.load_json(self.memory_file, {})
            if not memory:
                return {'optimized': False, 'message': 'No memory to optimize'}
            
            original_size = self.memory_file.stat().st_size if self.memory_file.exists() else 0
            
            # Apply various optimizations
            
            # 1. Remove empty entries
            await self._remove_empty_entries(memory)
            
            # 2. Compress large lists
            await self._compress_large_lists(memory)
            
            # 3. Sort and organize data
            await self._organize_data(memory)
            
            # Save optimized memory
            JSONEngine.save_json(self.memory_file, memory)
            
            new_size = self.memory_file.stat().st_size if self.memory_file.exists() else 0
            reduction = original_size - new_size
            
            logger.info(f"Memory optimized: size reduced by {reduction} bytes")
            
            return {
                'optimized': True,
                'original_size_bytes': original_size,
                'new_size_bytes': new_size,
                'reduction_bytes': reduction,
                'reduction_percent': round((reduction / original_size * 100), 2) if original_size > 0 else 0,
                'timestamp': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize memory: {e}")
            return {'optimized': False, 'error': str(e)}
    
    async def _remove_empty_entries(self, memory: Dict[str, Any]):
        """Remove empty or nearly empty entries"""
        # Check conversations
        if 'conversations' in memory:
            empty_conversations = []
            for conv_key, conv_data in memory['conversations'].items():
                if not conv_data.get('messages') and conv_data.get('message_count', 0) < 2:
                    empty_conversations.append(conv_key)
            
            for conv_key in empty_conversations:
                del memory['conversations'][conv_key]
    
    async def _compress_large_lists(self, memory: Dict[str, Any]):
        """Compress large lists to save space"""
        # Compress conversation messages
        if 'conversations' in memory:
            for conv_data in memory['conversations'].values():
                messages = conv_data.get('messages', [])
                if len(messages) > 20:
                    # Keep only last 20 messages
                    conv_data['messages'] = messages[-20:]
                    
                    # Update message count
                    conv_data['message_count'] = len(conv_data['messages'])
    
    async def _organize_data(self, memory: Dict[str, Any]):
        """Organize data for better storage efficiency"""
        # Sort conversations by last activity
        if 'conversations' in memory:
            sorted_conversations = dict(sorted(
                memory['conversations'].items(),
                key=lambda x: x[1].get('last_activity', 0),
                reverse=True
            ))
            memory['conversations'] = sorted_conversations
        
        # Sort user profiles by last seen
        if 'user_profiles' in memory:
            sorted_profiles = dict(sorted(
                memory['user_profiles'].items(),
                key=lambda x: x[1].get('last_seen', ''),
                reverse=True
            ))
            memory['user_profiles'] = sorted_profiles
    
    async def get_decay_stats(self) -> Dict[str, Any]:
        """Get decay system statistics"""
        return {
            'decay_rates': self.decay_rates,
            'retention_periods': self.retention_periods,
            'importance_weights': self.importance_weights,
            'memory_file_exists': self.memory_file.exists(),
            'memory_file_size': self.memory_file.stat().st_size if self.memory_file.exists() else 0,
        }
    
    async def schedule_regular_decay(self, interval_hours: int = 24):
        """Schedule regular memory decay"""
        # This would be called during bot startup
        # In a real implementation, this would use asyncio or a scheduling library
        
        logger.info(f"Scheduled regular memory decay every {interval_hours} hours")
        
        async def decay_task():
            while True:
                try:
                    await asyncio.sleep(interval_hours * 3600)
                    await self.apply_decay()
                    await self.optimize_memory()
                except Exception as e:
                    logger.error(f"Scheduled decay failed: {e}")
                    await asyncio.sleep(3600)  # Wait an hour before retry
        
        # Start the task
        asyncio.create_task(decay_task())
        
        return True