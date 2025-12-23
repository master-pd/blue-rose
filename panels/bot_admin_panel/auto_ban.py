#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Auto Ban
Automatic banning system
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class AutoBan:
    """Automatic Banning System"""
    
    def __init__(self):
        self.config = Config
        self.bans_file = self.config.DATA_DIR / "users" / "bans.json"
    
    async def ban_user(self, user_id: int, chat_id: int,
                      duration: int, reason: str,
                      banned_by: int = 0) -> Dict[str, Any]:
        """Ban a user"""
        try:
            # Load existing bans
            bans = JSONEngine.load_json(self.bans_file, {})
            
            user_key = f"{chat_id}_{user_id}"
            
            ban_entry = {
                'user_id': user_id,
                'chat_id': chat_id,
                'duration': duration,
                'reason': reason,
                'banned_by': banned_by,
                'banned_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=duration)).isoformat(),
                'active': True,
            }
            
            bans[user_key] = ban_entry
            
            # Save bans
            JSONEngine.save_json(self.bans_file, bans)
            
            logger.info(f"User {user_id} banned in chat {chat_id} for {duration} seconds: {reason}")
            
            return {
                'success': True,
                'ban': ban_entry,
                'human_duration': self._format_duration(duration),
            }
            
        except Exception as e:
            logger.error(f"Failed to ban user: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in human-readable format"""
        if seconds == 0:
            return "permanent"
        elif seconds < 60:
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