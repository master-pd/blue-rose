#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Auto Mute
Automatic muting system
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class AutoMute:
    """Automatic Muting System"""
    
    def __init__(self):
        self.config = Config
        self.mutes_file = self.config.DATA_DIR / "users" / "mutes.json"
    
    async def mute_user(self, user_id: int, chat_id: int,
                       duration: int, reason: str,
                       muted_by: int = 0) -> Dict[str, Any]:
        """Mute a user"""
        try:
            # Load existing mutes
            mutes = JSONEngine.load_json(self.mutes_file, {})
            
            user_key = f"{chat_id}_{user_id}"
            
            mute_entry = {
                'user_id': user_id,
                'chat_id': chat_id,
                'duration': duration,
                'reason': reason,
                'muted_by': muted_by,
                'muted_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=duration)).isoformat(),
                'active': True,
            }
            
            mutes[user_key] = mute_entry
            
            # Save mutes
            JSONEngine.save_json(self.mutes_file, mutes)
            
            logger.info(f"User {user_id} muted in chat {chat_id} for {duration} seconds: {reason}")
            
            return {
                'success': True,
                'mute': mute_entry,
                'human_duration': self._format_duration(duration),
            }
            
        except Exception as e:
            logger.error(f"Failed to mute user: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minutes"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hours"
        else:
            days = seconds // 86400
            return f"{days} days"