#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Anti Spam
Detect and prevent spam messages
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class AntiSpam:
    """Anti-Spam Protection System"""
    
    def __init__(self):
        self.config = Config
        self.spam_patterns = self._load_spam_patterns()
        self.user_message_times = {}
        self.user_message_counts = {}
        self.spam_detections = {}
        
        # Spam detection thresholds
        self.thresholds = {
            'messages_per_minute': 10,
            'identical_messages': 3,
            'similar_messages': 5,
            'url_density': 0.3,  # 30% of messages contain URLs
            'caps_ratio': 0.7,   # 70% capital letters
        }
        
        # Cleanup interval
        self.cleanup_interval = 300  # 5 minutes
    
    def _load_spam_patterns(self) -> Dict[str, Any]:
        """Load spam detection patterns"""
        return {
            'common_spam_keywords': [
                # English
                'buy now', 'click here', 'free money', 'make money',
                'work from home', 'earn cash', 'get rich', 'lottery',
                'prize winner', 'congratulations', 'you won', 'limited time',
                'special offer', 'discount', 'sale', 'promotion',
                'investment', 'bitcoin', 'crypto', 'trading',
                'follow me', 'subscribe', 'like and share',
                
                # Bangla
                'কিনুন এখন', 'ফ্রি মানি', 'টাকা উপার্জন',
                'বিনিয়োগ', 'বিটকয়েন', 'ক্রিপ্টো',
                'অফার', 'ডিসকাউন্ট', 'সেল', 'প্রমোশন',
                'লটারি', 'প্রাইজ', 'অভিনন্দন', 'জিতেছেন',
                'সাবস্ক্রাইব', 'লাইক শেয়ার', 'ফলো মি',
                
                # URLs and mentions
                r'http://', r'https://', r'www\.', r'\.com',
                r'@\w+', r'#\w+',
            ],
            'suspicious_patterns': [
                r'\b[A-Z]{3,}\b',  # All caps words
                r'\!{3,}',          # Multiple exclamation marks
                r'\?{3,}',          # Multiple question marks
                r'\.{3,}',          # Multiple dots
                r'[\*\-_=]{5,}',    # Repeated special characters
            ],
            'spam_phrases': [
                # Too good to be true
                '100% guaranteed', 'no risk', 'risk free',
                'easy money', 'quick cash', 'instant profit',
                
                # Urgency
                'act now', 'limited offer', 'today only',
                'last chance', 'don\'t miss', 'hurry up',
                
                # Secrecy
                'secret method', 'hidden secret', 'insider info',
                'confidential', 'exclusive', 'private offer',
            ],
        }
    
    async def check_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Check if message is spam"""
        try:
            chat_id = message.get('chat', {}).get('id')
            user_id = message.get('from', {}).get('id')
            text = message.get('text', '')
            
            if not chat_id or not user_id:
                return {'is_spam': False, 'reasons': []}
            
            # Initialize user tracking
            user_key = f"{chat_id}_{user_id}"
            current_time = datetime.now()
            
            if user_key not in self.user_message_times:
                self.user_message_times[user_key] = []
                self.user_message_counts[user_key] = 0
                self.spam_detections[user_key] = 0
            
            # Record message time
            self.user_message_times[user_key].append(current_time)
            self.user_message_counts[user_key] += 1
            
            # Check various spam indicators
            spam_reasons = []
            spam_score = 0
            
            # 1. Check message frequency
            freq_reason = await self._check_frequency(user_key)
            if freq_reason:
                spam_reasons.append(freq_reason)
                spam_score += 30
            
            # 2. Check spam patterns in text
            if text:
                pattern_reasons = await self._check_patterns(text)
                spam_reasons.extend(pattern_reasons)
                spam_score += len(pattern_reasons) * 10
                
                # 3. Check for identical/similar messages
                similarity_reason = await self._check_similarity(user_key, text)
                if similarity_reason:
                    spam_reasons.append(similarity_reason)
                    spam_score += 25
                
                # 4. Check URL density
                url_reason = await self._check_url_density(user_key, text)
                if url_reason:
                    spam_reasons.append(url_reason)
                    spam_score += 20
                
                # 5. Check caps ratio
                caps_reason = await self._check_caps_ratio(text)
                if caps_reason:
                    spam_reasons.append(caps_reason)
                    spam_score += 15
            
            # Determine if spam
            is_spam = spam_score >= 50  # Threshold for spam
            
            if is_spam:
                self.spam_detections[user_key] += 1
                logger.warning(f"Spam detected: user {user_id} in chat {chat_id}, "
                             f"score: {spam_score}, reasons: {spam_reasons}")
            
            return {
                'is_spam': is_spam,
                'score': spam_score,
                'reasons': spam_reasons,
                'user_id': user_id,
                'chat_id': chat_id,
                'timestamp': current_time.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Spam check failed: {e}")
            return {'is_spam': False, 'error': str(e)}
    
    async def _check_frequency(self, user_key: str) -> Optional[str]:
        """Check message frequency"""
        message_times = self.user_message_times.get(user_key, [])
        
        if len(message_times) < 2:
            return None
        
        # Check messages in last minute
        current_time = datetime.now()
        one_minute_ago = current_time - timedelta(minutes=1)
        
        recent_messages = [t for t in message_times if t > one_minute_ago]
        
        if len(recent_messages) > self.thresholds['messages_per_minute']:
            return f"High frequency: {len(recent_messages)} messages per minute"
        
        return None
    
    async def _check_patterns(self, text: str) -> List[str]:
        """Check for spam patterns in text"""
        reasons = []
        text_lower = text.lower()
        
        # Check common spam keywords
        for keyword in self.spam_patterns['common_spam_keywords']:
            if re.search(keyword, text_lower, re.IGNORECASE):
                reasons.append(f"Contains spam keyword: {keyword}")
                break
        
        # Check suspicious patterns
        for pattern in self.spam_patterns['suspicious_patterns']:
            if re.search(pattern, text):
                reasons.append(f"Suspicious pattern: {pattern}")
        
        # Check spam phrases
        for phrase in self.spam_patterns['spam_phrases']:
            if phrase.lower() in text_lower:
                reasons.append(f"Spam phrase: {phrase}")
        
        return reasons
    
    async def _check_similarity(self, user_key: str, text: str) -> Optional[str]:
        """Check for identical or similar messages"""
        # In a real implementation, this would compare with previous messages
        # For now, use a simple approach
        
        # Store recent messages (simplified)
        if not hasattr(self, 'user_recent_messages'):
            self.user_recent_messages = {}
        
        if user_key not in self.user_recent_messages:
            self.user_recent_messages[user_key] = []
        
        recent_messages = self.user_recent_messages[user_key]
        
        # Check for identical messages
        identical_count = 0
        for prev_text in recent_messages:
            if prev_text == text:
                identical_count += 1
        
        if identical_count >= self.thresholds['identical_messages']:
            return f"Identical messages sent: {identical_count + 1} times"
        
        # Check for similar messages (simplified)
        # In real implementation, use text similarity algorithms
        if len(recent_messages) >= self.thresholds['similar_messages']:
            return f"Multiple similar messages: {len(recent_messages) + 1}"
        
        # Add current message to history
        recent_messages.append(text)
        if len(recent_messages) > 10:  # Keep only last 10 messages
            recent_messages.pop(0)
        
        return None
    
    async def _check_url_density(self, user_key: str, text: str) -> Optional[str]:
        """Check URL density in messages"""
        # Count URLs in text
        url_pattern = r'https?://\S+|www\.\S+'
        urls = re.findall(url_pattern, text)
        
        if not urls:
            return None
        
        # Track URL messages per user
        if not hasattr(self, 'user_url_messages'):
            self.user_url_messages = {}
        
        if user_key not in self.user_url_messages:
            self.user_url_messages[user_key] = []
        
        url_messages = self.user_url_messages[user_key]
        url_messages.append({
            'text': text,
            'timestamp': datetime.now(),
            'url_count': len(urls),
        })
        
        # Keep only recent messages
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        url_messages = [msg for msg in url_messages if msg['timestamp'] > five_minutes_ago]
        self.user_url_messages[user_key] = url_messages
        
        # Calculate URL density
        total_messages = self.user_message_counts.get(user_key, 0)
        if total_messages > 0:
            url_message_count = len(url_messages)
            url_density = url_message_count / total_messages
            
            if url_density > self.thresholds['url_density']:
                return f"High URL density: {round(url_density * 100)}% of messages contain URLs"
        
        return None
    
    async def _check_caps_ratio(self, text: str) -> Optional[str]:
        """Check ratio of capital letters"""
        if not text:
            return None
        
        # Count capital letters
        total_chars = len(text)
        if total_chars == 0:
            return None
        
        caps_chars = sum(1 for c in text if c.isupper())
        caps_ratio = caps_chars / total_chars
        
        if caps_ratio > self.thresholds['caps_ratio']:
            return f"High caps ratio: {round(caps_ratio * 100)}% capital letters"
        
        return None
    
    async def take_action(self, spam_result: Dict[str, Any]) -> Dict[str, Any]:
        """Take action against spam"""
        if not spam_result.get('is_spam'):
            return {'action_taken': False, 'reason': 'Not spam'}
        
        user_id = spam_result.get('user_id')
        chat_id = spam_result.get('chat_id')
        spam_score = spam_result.get('score', 0)
        
        user_key = f"{chat_id}_{user_id}"
        spam_count = self.spam_detections.get(user_key, 0)
        
        actions = []
        
        # Determine action based on spam score and count
        if spam_score >= 80 or spam_count > 3:
            # Severe spam - ban
            actions.append({
                'type': 'ban',
                'duration': 86400,  # 24 hours
                'reason': 'Severe spam detection',
            })
        elif spam_score >= 60 or spam_count > 2:
            # Medium spam - mute
            actions.append({
                'type': 'mute',
                'duration': 3600,  # 1 hour
                'reason': 'Medium spam detection',
            })
        elif spam_score >= 50 or spam_count > 1:
            # Light spam - warn
            actions.append({
                'type': 'warn',
                'reason': 'Light spam detection',
            })
        
        # Log the action
        if actions:
            log_entry = {
                'user_id': user_id,
                'chat_id': chat_id,
                'spam_score': spam_score,
                'spam_count': spam_count,
                'actions': actions,
                'timestamp': datetime.now().isoformat(),
                'reasons': spam_result.get('reasons', []),
            }
            
            # Save to spam log
            await self._log_spam_action(log_entry)
            
            logger.info(f"Anti-spam action: {actions} for user {user_id} in chat {chat_id}")
        
        return {
            'action_taken': len(actions) > 0,
            'actions': actions,
            'user_id': user_id,
            'chat_id': chat_id,
        }
    
    async def _log_spam_action(self, log_entry: Dict[str, Any]):
        """Log spam action to file"""
        try:
            log_file = self.config.DATA_DIR / "moderation" / "spam_logs.json"
            log_file.parent.mkdir(exist_ok=True)
            
            # Load existing logs
            logs = JSONEngine.load_json(log_file, [])
            
            # Add new log entry
            logs.append(log_entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Save logs
            JSONEngine.save_json(log_file, logs)
            
        except Exception as e:
            logger.error(f"Failed to log spam action: {e}")
    
    async def cleanup_old_data(self):
        """Cleanup old tracking data"""
        try:
            current_time = datetime.now()
            five_minutes_ago = current_time - timedelta(minutes=5)
            
            # Cleanup message times
            for user_key in list(self.user_message_times.keys()):
                message_times = self.user_message_times[user_key]
                # Keep only messages from last 5 minutes
                filtered_times = [t for t in message_times if t > five_minutes_ago]
                
                if filtered_times:
                    self.user_message_times[user_key] = filtered_times
                else:
                    # Remove user if no recent messages
                    del self.user_message_times[user_key]
                    self.user_message_counts.pop(user_key, None)
                    self.spam_detections.pop(user_key, None)
            
            logger.debug("Cleaned up old anti-spam data")
            
        except Exception as e:
            logger.error(f"Failed to cleanup anti-spam data: {e}")
    
    async def get_user_spam_stats(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Get spam statistics for a user"""
        user_key = f"{chat_id}_{user_id}"
        
        return {
            'user_id': user_id,
            'chat_id': chat_id,
            'total_messages': self.user_message_counts.get(user_key, 0),
            'spam_detections': self.spam_detections.get(user_key, 0),
            'recent_activity': len(self.user_message_times.get(user_key, [])),
            'is_tracked': user_key in self.user_message_times,
        }
    
    async def get_anti_spam_stats(self) -> Dict[str, Any]:
        """Get anti-spam system statistics"""
        return {
            'tracked_users': len(self.user_message_times),
            'total_spam_detections': sum(self.spam_detections.values()),
            'thresholds': self.thresholds,
            'pattern_count': {
                'keywords': len(self.spam_patterns['common_spam_keywords']),
                'patterns': len(self.spam_patterns['suspicious_patterns']),
                'phrases': len(self.spam_patterns['spam_phrases']),
            },
        }