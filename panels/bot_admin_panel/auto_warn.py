#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Auto Warn
Automatic warning system
"""

import logging
from typing import Dict, Any

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class AutoWarn:
    """Automatic Warning System"""
    
    def __init__(self):
        self.config = Config
        self.warnings_file = self.config.DATA_DIR / "users" / "warnings.json"
    
    async def issue_warning(self, user_id: int, chat_id: int,
                          reason: str, warned_by: int = 0) -> Dict[str, Any]:
        """Issue a warning to user"""
        try:
            # Load existing warnings
            warnings = JSONEngine.load_json(self.warnings_file, {})
            
            user_key = f"{chat_id}_{user_id}"
            
            if user_key not in warnings:
                warnings[user_key] = []
            
            warning_entry = {
                'user_id': user_id,
                'chat_id': chat_id,
                'reason': reason,
                'warned_by': warned_by,
                'timestamp': datetime.now().isoformat(),
                'warning_id': len(warnings[user_key]) + 1,
            }
            
            warnings[user_key].append(warning_entry)
            
            # Save warnings
            JSONEngine.save_json(self.warnings_file, warnings)
            
            warning_count = len(warnings[user_key])
            
            logger.info(f"Warning issued to user {user_id} in chat {chat_id}: {reason}")
            
            return {
                'success': True,
                'warning': warning_entry,
                'total_warnings': warning_count,
                'action_required': warning_count >= 3,
            }
            
        except Exception as e:
            logger.error(f"Failed to issue warning: {e}")
            return {'success': False, 'error': str(e)}

from datetime import datetime