#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Approval Panel
Payment request approval system for bot owner
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class ApprovalPanel:
    """Payment Request Approval Panel"""
    
    def __init__(self):
        self.config = Config
        self.requests_file = self.config.JSON_PATHS['payment_requests']
        self.groups_file = self.config.JSON_PATHS['groups']
        self.history_file = self.config.DATA_DIR / "payments" / "payment_history.json"
        
    async def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending payment requests"""
        try:
            requests = JSONEngine.load_json(self.requests_file, [])
            pending = [req for req in requests if req.get('status') == 'pending']
            
            # Sort by creation date (oldest first)
            pending.sort(key=lambda x: x.get('created_at', ''))
            
            return pending
            
        except Exception as e:
            logger.error(f"Failed to get pending requests: {e}")
            return []
    
    async def get_request_details(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Get details of a specific payment request"""
        try:
            requests = JSONEngine.load_json(self.requests_file, [])
            
            for request in requests:
                if request.get('request_id') == request_id:
                    return request
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get request details: {e}")
            return None
    
    async def approve_request(self, request_id: int, approved_by: int,
                            plan_duration: Optional[int] = None) -> Dict[str, Any]:
        """Approve a payment request"""
        try:
            requests = JSONEngine.load_json(self.requests_file, [])
            
            for i, request in enumerate(requests):
                if request.get('request_id') == request_id:
                    if request.get('status') != 'pending':
                        return {
                            'success': False,
                            'error': f"Request already {request.get('status')}"
                        }
                    
                    # Update request status
                    requests[i]['status'] = 'approved'
                    requests[i]['processed_by'] = approved_by
                    requests[i]['processed_at'] = datetime.now().isoformat()
                    requests[i]['plan_duration'] = plan_duration
                    
                    # Update group plan
                    chat_id = request.get('chat_id')
                    plan = request.get('plan')
                    
                    if chat_id and plan:
                        await self._update_group_plan(chat_id, plan, plan_duration)
                    
                    # Save updated requests
                    JSONEngine.save_json(self.requests_file, requests)
                    
                    # Log to history
                    await self._log_to_history(request, 'approved', approved_by)
                    
                    logger.info(f"Payment request {request_id} approved by {approved_by}")
                    
                    return {
                        'success': True,
                        'request_id': request_id,
                        'chat_id': chat_id,
                        'plan': plan,
                        'approved_by': approved_by,
                    }
            
            return {'success': False, 'error': 'Request not found'}
            
        except Exception as e:
            logger.error(f"Failed to approve request: {e}")
            return {'success': False, 'error': str(e)}
    
    async def reject_request(self, request_id: int, rejected_by: int,
                           reason: str = "") -> Dict[str, Any]:
        """Reject a payment request"""
        try:
            requests = JSONEngine.load_json(self.requests_file, [])
            
            for i, request in enumerate(requests):
                if request.get('request_id') == request_id:
                    if request.get('status') != 'pending':
                        return {
                            'success': False,
                            'error': f"Request already {request.get('status')}"
                        }
                    
                    # Update request status
                    requests[i]['status'] = 'rejected'
                    requests[i]['processed_by'] = rejected_by
                    requests[i]['processed_at'] = datetime.now().isoformat()
                    requests[i]['rejection_reason'] = reason
                    
                    # Save updated requests
                    JSONEngine.save_json(self.requests_file, requests)
                    
                    # Log to history
                    await self._log_to_history(request, 'rejected', rejected_by, reason)
                    
                    logger.info(f"Payment request {request_id} rejected by {rejected_by}: {reason}")
                    
                    return {
                        'success': True,
                        'request_id': request_id,
                        'rejected_by': rejected_by,
                        'reason': reason,
                    }
            
            return {'success': False, 'error': 'Request not found'}
            
        except Exception as e:
            logger.error(f"Failed to reject request: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _update_group_plan(self, chat_id: int, plan: str,
                               duration_days: Optional[int] = None):
        """Update group subscription plan"""
        try:
            groups = JSONEngine.load_json(self.groups_file, {})
            group_key = str(chat_id)
            
            if group_key not in groups:
                groups[group_key] = {}
            
            # Calculate expiry date
            if duration_days is None:
                # Use default duration for plan
                plans = JSONEngine.load_json(self.config.JSON_PATHS['plans'], {})
                plan_info = plans.get(plan, {})
                duration_days = plan_info.get('duration_days', 30)
            
            expiry_date = datetime.now() + timedelta(days=duration_days)
            
            # Update group data
            groups[group_key]['plan'] = plan
            groups[group_key]['plan_active'] = True
            groups[group_key]['expiry_date'] = expiry_date.isoformat()
            groups[group_key]['last_payment'] = datetime.now().isoformat()
            groups[group_key]['payment_status'] = 'paid'
            
            # Save updated groups
            JSONEngine.save_json(self.groups_file, groups)
            
            logger.info(f"Group {chat_id} plan updated to {plan}, expires {expiry_date}")
            
        except Exception as e:
            logger.error(f"Failed to update group plan: {e}")
            raise
    
    async def _log_to_history(self, request: Dict[str, Any], action: str,
                            processed_by: int, reason: str = ""):
        """Log payment action to history"""
        try:
            history = JSONEngine.load_json(self.history_file, [])
            
            history_entry = {
                'request_id': request.get('request_id'),
                'chat_id': request.get('chat_id'),
                'user_id': request.get('user_id'),
                'plan': request.get('plan'),
                'action': action,
                'processed_by': processed_by,
                'processed_at': datetime.now().isoformat(),
                'reason': reason,
                'admin_info': request.get('admin_info', {}),
            }
            
            history.append(history_entry)
            
            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]
            
            JSONEngine.save_json(self.history_file, history)
            
        except Exception as e:
            logger.error(f"Failed to log to history: {e}")
    
    async def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval panel statistics"""
        try:
            requests = JSONEngine.load_json(self.requests_file, [])
            history = JSONEngine.load_json(self.history_file, [])
            
            stats = {
                'total_requests': len(requests),
                'pending_requests': len([r for r in requests if r.get('status') == 'pending']),
                'approved_requests': len([r for r in requests if r.get('status') == 'approved']),
                'rejected_requests': len([r for r in requests if r.get('status') == 'rejected']),
                'total_history': len(history),
                'today_approvals': len([h for h in history 
                                      if h.get('action') == 'approved' and
                                      h.get('processed_at', '').startswith(datetime.now().strftime('%Y-%m-%d'))]),
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get approval stats: {e}")
            return {'error': str(e)}