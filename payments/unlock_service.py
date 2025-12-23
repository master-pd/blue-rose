#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Unlock Service
Service unlocking after payment approval
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from config import Config
from storage.json_engine import JSONEngine
from core.feature_switch import FeatureSwitch

logger = logging.getLogger(__name__)

class UnlockService:
    """Service Unlocking System"""
    
    def __init__(self):
        self.config = Config
        self.feature_switch = FeatureSwitch()
        self.groups_file = self.config.JSON_PATHS['groups']
        self.services_file = self.config.DATA_DIR / "groups" / "group_services.json"
    
    async def unlock_group_services(self, chat_id: int, plan: str) -> Dict[str, Any]:
        """Unlock services for a group based on plan"""
        try:
            # Load plan details
            plans = JSONEngine.load_json(self.config.JSON_PATHS['plans'], {})
            plan_info = plans.get(plan, {})
            
            if not plan_info:
                return {'success': False, 'error': f'Plan not found: {plan}'}
            
            # Get features for this plan
            plan_features = plan_info.get('features', [])
            
            # Map plan features to service features
            service_mapping = {
                'basic_auto_reply': ['auto_reply'],
                'all_auto_reply': ['auto_reply', 'welcome_message', 'goodbye_message'],
                'moderation': ['moderation', 'anti_spam', 'anti_flood'],
                'scheduling': ['scheduled_messages', 'prayer_alerts'],
                'all_features': ['auto_reply', 'moderation', 'intelligence', 'analytics'],
                'priority_support': ['priority_support'],
                'customization': ['custom_messages', 'custom_keywords'],
            }
            
            # Determine which services to unlock
            services_to_unlock = []
            for plan_feature in plan_features:
                if plan_feature in service_mapping:
                    services_to_unlock.extend(service_mapping[plan_feature])
            
            # Remove duplicates
            services_to_unlock = list(set(services_to_unlock))
            
            # Unlock services
            unlocked_services = []
            for service in services_to_unlock:
                success = await self.feature_switch.enable_feature(
                    service, 
                    enabled_by=self.config.BOT_OWNER_ID,
                    group_id=chat_id
                )
                
                if success:
                    unlocked_services.append(service)
            
            # Update group services record
            await self._update_group_services(chat_id, plan, unlocked_services)
            
            logger.info(f"Unlocked {len(unlocked_services)} services for group {chat_id} on plan {plan}")
            
            return {
                'success': True,
                'chat_id': chat_id,
                'plan': plan,
                'unlocked_services': unlocked_services,
                'total_services': len(unlocked_services),
            }
            
        except Exception as e:
            logger.error(f"Failed to unlock services: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _update_group_services(self, chat_id: int, plan: str,
                                   services: List[str]):
        """Update group services record"""
        try:
            group_services = JSONEngine.load_json(self.services_file, {})
            group_key = str(chat_id)
            
            if group_key not in group_services:
                group_services[group_key] = {}
            
            group_services[group_key]['plan'] = plan
            group_services[group_key]['services'] = services
            group_services[group_key]['unlocked_at'] = datetime.now().isoformat()
            group_services[group_key]['active'] = True
            
            JSONEngine.save_json(self.services_file, group_services)
            
        except Exception as e:
            logger.error(f"Failed to update group services: {e}")
            raise
    
    async def check_service_status(self, chat_id: int) -> Dict[str, Any]:
        """Check service status for a group"""
        try:
            # Check group plan
            groups = JSONEngine.load_json(self.groups_file, {})
            group_key = str(chat_id)
            
            if group_key not in groups:
                return {'has_plan': False, 'message': 'Group not found'}
            
            group_data = groups[group_key]
            plan = group_data.get('plan', 'free')
            plan_active = group_data.get('plan_active', False)
            expiry_date = group_data.get('expiry_date')
            
            # Check expiry
            is_expired = False
            if expiry_date:
                try:
                    expiry = datetime.fromisoformat(expiry_date)
                    if datetime.now() > expiry:
                        is_expired = True
                        plan_active = False
                except:
                    pass
            
            # Get unlocked services
            group_services = JSONEngine.load_json(self.services_file, {})
            services = group_services.get(group_key, {}).get('services', [])
            
            # Check which features are actually enabled
            enabled_features = []
            for service in services:
                if await self.feature_switch.is_enabled(service, chat_id):
                    enabled_features.append(service)
            
            return {
                'has_plan': True,
                'plan': plan,
                'plan_active': plan_active,
                'is_expired': is_expired,
                'expiry_date': expiry_date,
                'unlocked_services': services,
                'enabled_features': enabled_features,
                'total_services': len(services),
                'enabled_count': len(enabled_features),
            }
            
        except Exception as e:
            logger.error(f"Failed to check service status: {e}")
            return {'error': str(e)}
    
    async def force_unlock_service(self, chat_id: int, service: str,
                                 unlocked_by: int) -> Dict[str, Any]:
        """Force unlock a specific service (admin override)"""
        try:
            success = await self.feature_switch.enable_feature(
                service,
                enabled_by=unlocked_by,
                group_id=chat_id
            )
            
            if success:
                # Update group services record
                group_services = JSONEngine.load_json(self.services_file, {})
                group_key = str(chat_id)
                
                if group_key not in group_services:
                    group_services[group_key] = {'services': []}
                
                if 'services' not in group_services[group_key]:
                    group_services[group_key]['services'] = []
                
                if service not in group_services[group_key]['services']:
                    group_services[group_key]['services'].append(service)
                
                group_services[group_key]['force_unlocked'] = True
                group_services[group_key]['force_unlocked_by'] = unlocked_by
                group_services[group_key]['force_unlocked_at'] = datetime.now().isoformat()
                
                JSONEngine.save_json(self.services_file, group_services)
                
                logger.info(f"Force unlocked service '{service}' for group {chat_id} by {unlocked_by}")
            
            return {
                'success': success,
                'service': service,
                'chat_id': chat_id,
                'unlocked_by': unlocked_by,
            }
            
        except Exception as e:
            logger.error(f"Failed to force unlock service: {e}")
            return {'success': False, 'error': str(e)}