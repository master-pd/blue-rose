#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Anti Flood
Prevent message flooding
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AntiFlood:
    """Anti-Flood Protection System"""
    
    def __init__(self):
        self.message_times = {}
        self.flood_detections = {}
        self.thresholds = {
            'messages_per_second': 5,
            'messages_per_minute': 20,
            'identical_messages_per_minute': 3,
        }
    
    async def check_flood(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Check for message flooding"""
        chat_id = message.get('chat', {}).get('id')
        user_id = message.get('from', {}).get('id')
        
        if not chat_id or not user_id:
            return {'is_flood': False}
        
        user_key = f"{chat_id}_{user_id}"
        current_time = datetime.now()
        
        # Initialize tracking
        if user_key not in self.message_times:
            self.message_times[user_key] = []
            self.flood_detections[user_key] = 0
        
        # Add current message time
        self.message_times[user_key].append(current_time)
        
        # Check flooding
        flood_reasons = []
        
        # Check per-second rate
        one_second_ago = current_time - timedelta(seconds=1)
        recent_second = [t for t in self.message_times[user_key] if t > one_second_ago]
        if len(recent_second) > self.thresholds['messages_per_second']:
            flood_reasons.append(f"High per-second rate: {len(recent_second)} messages")
        
        # Check per-minute rate
        one_minute_ago = current_time - timedelta(minutes=1)
        recent_minute = [t for t in self.message_times[user_key] if t > one_minute_ago]
        if len(recent_minute) > self.thresholds['messages_per_minute']:
            flood_reasons.append(f"High per-minute rate: {len(recent_minute)} messages")
        
        is_flood = len(flood_reasons) > 0
        
        if is_flood:
            self.flood_detections[user_key] += 1
            logger.warning(f"Flood detected: user {user_id} in chat {chat_id}")
        
        return {
            'is_flood': is_flood,
            'reasons': flood_reasons,
            'user_id': user_id,
            'chat_id': chat_id,
        }