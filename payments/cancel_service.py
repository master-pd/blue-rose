#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Cancel Service
Service cancellation and plan termination
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import Config
from storage.json_engine import JSONEngine
from core.feature_switch import FeatureSwitch

logger = logging.getLogger(__name__)

class CancelService:
    """Service Cancellation System"""
    
    def __init__(self):
        self.config = Config
        self.feature_switch = FeatureSwitch()
        self.groups_file = self.config.JSON_PATHS['groups']
        self.services_file = self.config.DATA_DIR / "groups" / "group_services.json"
        self.cancellations_file = self.config.DATA_DIR / "payments" / "cancellations.json"
    
    async def cancel_group_plan(self, chat_id: int, cancelled_by: int,
                              reason: str = "") -> Dict[str, Any]:
        """Cancel group subscription plan"""
        try:
            # Update group plan status
            groups = JSONEngine.load_json(self.groups_file, {})
            group_key = str(chat_id)
            
            if group_key not in groups:
                return {'success': False, 'error': 'Group not found'}
            
            # Mark plan as cancelled
            groups[group_key]['plan_active'] = False
            groups[group_key]['cancelled_at'] = datetime.now().isoformat()
            groups[group_key]['cancelled_by'] = cancelled_by
            groups[group_key]['cancellation_reason'] = reason
            
            # Disable paid features (keep only free features)
            await self._disable_paid_features(chat_id)
            
            # Save updated groups
            JSONEngine.save_json(self.groups_file, groups)
            
            # Log cancellation
            await self._log_cancellation(chat_id, cancelled_by, reason)
            
            logger.info(f"Cancelled plan for group {chat_id} by {cancelled_by}: {reason}")
            
            return {
                'success': True,
                'chat_id': chat_id,
                'cancelled_by': cancelled_by,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel plan: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _disable_paid_features(self, chat_id: int):
        """Disable paid features for a group"""
        # Define which features are paid vs free
        paid_features = [
            'moderation', 'anti_spam', 'anti_flood', 'anti_link',
            'scheduled_messages', 'prayer_alerts', 'night_mode',
            'intelligence', 'analytics', 'priority_support',
        ]
        
        free_features = [
            'auto_reply', 'welcome_message', 'goodbye_message',
        ]
        
        # Disable paid features
        for feature in paid_features:
            await self.feature_switch.disable_feature(
                feature,
                disabled_by=self.config.BOT_OWNER_ID,
                group_id=chat_id
            )
        
        # Ensure free features remain enabled
        for feature in free_features:
            await self.feature_switch.enable_feature(
                feature,
                enabled_by=self.config.BOT_OWNER_ID,
                group_id=chat_id
            )
    
    async def _log_cancellation(self, chat_id: int, cancelled_by: int,
                              reason: str):
        """Log cancellation to file"""
        try:
            cancellations = JSONEngine.load_json(self.cancellations_file, [])
            
            cancellation_entry = {
                'chat_id': chat_id,
                'cancelled_by': cancelled_by,
                'reason': reason,
                'cancelled_at': datetime.now().isoformat(),
            }
            
            cancellations.append(cancellation_entry)
            
            # Keep only last 500 entries
            if len(cancellations) > 500:
                cancellations = cancellations[-500:]
            
            JSONEngine.save_json(self.cancellations_file, cancellations)
            
        except Exception as e:
            logger.error(f"Failed to log cancellation: {e}")
    
    async def get_cancellation_history(self, chat_id: Optional[int] = None) -> list:
        """Get cancellation history"""
        try:
            cancellations = JSONEngine.load_json(self.cancellations_file, [])
            
            if chat_id:
                # Filter for specific chat
                cancellations = [c for c in cancellations if c.get('chat_id') == chat_id]
            
            return cancellations
            
        except Exception as e:
            logger.error(f"Failed to get cancellation history: {e}")
            return []
    
    async def restore_plan(self, chat_id: int, restored_by: int,
                         plan: str, duration_days: int = 30) -> Dict[str, Any]:
        """Restore cancelled plan"""
        try:
            groups = JSONEngine.load_json(self.groups_file, {})
            group_key = str(chat_id)
            
            if group_key not in groups:
                return {'success': False, 'error': 'Group not found'}
            
            # Calculate new expiry date
            from datetime import timedelta
            expiry_date = datetime.now() + timedelta(days=duration_days)
            
            # Update group plan
            groups[group_key]['plan'] = plan
            groups[group_key]['plan_active'] = True
            groups[group_key]['expiry_date'] = expiry_date.isoformat()
            groups[group_key]['restored_at'] = datetime.now().isoformat()
            groups[group_key]['restored_by'] = restored_by
            
            # Remove cancellation info
            groups[group_key].pop('cancelled_at', None)
            groups[group_key].pop('cancelled_by', None)
            groups[group_key].pop('cancellation_reason', None)
            
            # Save updated groups
            JSONEngine.save_json(self.groups_file, groups)
            
            # Re-enable paid features
            from payments.unlock_service import UnlockService
            unlock_service = UnlockService()
            await unlock_service.unlock_group_services(chat_id, plan)
            
            logger.info(f"Restored plan for group {chat_id} by {restored_by}")
            
            return {
                'success': True,
                'chat_id': chat_id,
                'plan': plan,
                'duration_days': duration_days,
                'expiry_date': expiry_date.isoformat(),
                'restored_by': restored_by,
            }
            
        except Exception as e:
            logger.error(f"Failed to restore plan: {e}")
            return {'success': False, 'error': str(e)}
