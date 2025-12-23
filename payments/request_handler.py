#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Payment Request Handler
Handle payment requests
"""

import logging
from typing import Dict, Any

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class PaymentRequestHandler:
    """Payment Request Handler"""
    
    def __init__(self):
        self.config = Config
        self.requests_file = self.config.JSON_PATHS['payment_requests']
    
    async def create_request(self, chat_id: int, user_id: int,
                           plan: str, admin_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment request"""
        try:
            requests = JSONEngine.load_json(self.requests_file, [])
            
            request_id = len(requests) + 1
            request = {
                'request_id': request_id,
                'chat_id': chat_id,
                'user_id': user_id,
                'plan': plan,
                'admin_info': admin_info,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'processed_by': None,
                'processed_at': None,
            }
            
            requests.append(request)
            JSONEngine.save_json(self.requests_file, requests)
            
            logger.info(f"Payment request created: {request_id} for chat {chat_id}")
            
            return {'success': True, 'request_id': request_id, 'request': request}
            
        except Exception as e:
            logger.error(f"Failed to create payment request: {e}")
            return {'success': False, 'error': str(e)}

from datetime import datetime