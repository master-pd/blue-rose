#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Anti Forward
Control forwarded messages
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AntiForward:
    """Anti-Forward Protection System"""
    
    async def check_forward(self, message: Dict[str, Any],
                          group_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Check if message is forwarded"""
        is_forwarded = 'forward_from' in message or 'forward_from_chat' in message
        
        return {
            'is_forwarded': is_forwarded,
            'forward_source': message.get('forward_from') or message.get('forward_from_chat'),
            'should_block': is_forwarded and group_settings.get('block_forwards', False),
        }