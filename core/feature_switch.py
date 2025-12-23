#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Feature Switch
Feature flag management system
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class FeatureSwitch:
    """Feature Flag Management System"""
    
    def __init__(self):
        self.config = Config
        self.features = {}
        self.feature_states = {}
        self.group_overrides = {}
        self.user_overrides = {}
        
        self._load_default_features()
    
    def _load_default_features(self):
        """Load default feature definitions"""
        self.features = {
            # Core Features
            'auto_reply': {
                'name': 'Auto Reply System',
                'description': 'Automatically reply to messages',
                'default': True,
                'scope': ['global', 'group', 'user'],
                'requires': [],
            },
            'moderation': {
                'name': 'Moderation System',
                'description': 'Automatic moderation features',
                'default': True,
                'scope': ['global', 'group'],
                'requires': ['auto_reply'],
            },
            'payments': {
                'name': 'Payment System',
                'description': 'Payment and subscription management',
                'default': True,
                'scope': ['global', 'group'],
                'requires': [],
            },
            'analytics': {
                'name': 'Analytics System',
                'description': 'Statistics and analytics collection',
                'default': True,
                'scope': ['global', 'group'],
                'requires': [],
            },
            'intelligence': {
                'name': 'Intelligence Engine',
                'description': 'AI and smart response system',
                'default': True,
                'scope': ['global', 'group'],
                'requires': ['auto_reply'],
            },
            'supremacy': {
                'name': 'Bot Supremacy',
                'description': 'Competing bot detection and management',
                'default': True,
                'scope': ['global', 'group'],
                'requires': ['moderation'],
            },
            
            # Group Features
            'welcome_message': {
                'name': 'Welcome Messages',
                'description': 'Send welcome messages to new members',
                'default': True,
                'scope': ['group'],
                'requires': ['auto_reply'],
            },
            'goodbye_message': {
                'name': 'Goodbye Messages',
                'description': 'Send goodbye messages to leaving members',
                'default': True,
                'scope': ['group'],
                'requires': ['auto_reply'],
            },
            'prayer_alerts': {
                'name': 'Prayer Time Alerts',
                'description': 'Send prayer time notifications',
                'default': True,
                'scope': ['group'],
                'requires': ['scheduled_messages'],
            },
            'night_mode': {
                'name': 'Night Mode',
                'description': 'Quiet hours for the group',
                'default': True,
                'scope': ['group'],
                'requires': [],
            },
            'scheduled_messages': {
                'name': 'Scheduled Messages',
                'description': 'Send messages at scheduled times',
                'default': True,
                'scope': ['group'],
                'requires': [],
            },
            
            # Moderation Features
            'anti_spam': {
                'name': 'Anti-Spam',
                'description': 'Detect and prevent spam',
                'default': True,
                'scope': ['group'],
                'requires': ['moderation'],
            },
            'anti_flood': {
                'name': 'Anti-Flood',
                'description': 'Prevent message flooding',
                'default': True,
                'scope': ['group'],
                'requires': ['moderation'],
            },
            'anti_link': {
                'name': 'Anti-Link',
                'description': 'Control link sharing',
                'default': True,
                'scope': ['group'],
                'requires': ['moderation'],
            },
            'anti_forward': {
                'name': 'Anti-Forward',
                'description': 'Control forwarded messages',
                'default': True,
                'scope': ['group'],
                'requires': ['moderation'],
            },
            'auto_warn': {
                'name': 'Auto-Warn',
                'description': 'Automatic warnings for violations',
                'default': True,
                'scope': ['group'],
                'requires': ['moderation'],
            },
            'auto_mute': {
                'name': 'Auto-Mute',
                'description': 'Automatic muting for violations',
                'default': True,
                'scope': ['group'],
                'requires': ['moderation'],
            },
            'auto_ban': {
                'name': 'Auto-Ban',
                'description': 'Automatic banning for violations',
                'default': True,
                'scope': ['group'],
                'requires': ['moderation'],
            },
        }
        
        # Initialize default states
        for feature_id, feature_info in self.features.items():
            self.feature_states[feature_id] = feature_info['default']
    
    async def is_enabled(self, feature_id: str, 
                        group_id: Optional[int] = None,
                        user_id: Optional[int] = None) -> bool:
        """Check if a feature is enabled"""
        try:
            # Check if feature exists
            if feature_id not in self.features:
                logger.warning(f"Unknown feature: {feature_id}")
                return False
            
            # Check global state first
            if not self.feature_states.get(feature_id, False):
                return False
            
            # Check group override if group_id provided
            if group_id:
                group_key = f"{group_id}"
                if group_key in self.group_overrides:
                    if feature_id in self.group_overrides[group_key]:
                        return self.group_overrides[group_key][feature_id]
            
            # Check user override if user_id provided
            if user_id:
                user_key = f"{user_id}"
                if user_key in self.user_overrides:
                    if feature_id in self.user_overrides[user_key]:
                        return self.user_overrides[user_key][feature_id]
            
            # Check feature dependencies
            feature_info = self.features[feature_id]
            for required_feature in feature_info.get('requires', []):
                if not await self.is_enabled(required_feature, group_id, user_id):
                    return False
            
            # Default to feature state
            return self.feature_states.get(feature_id, False)
            
        except Exception as e:
            logger.error(f"Failed to check feature {feature_id}: {e}")
            return False
    
    async def enable_feature(self, feature_id: str,
                           enabled_by: int,
                           group_id: Optional[int] = None,
                           user_id: Optional[int] = None) -> bool:
        """Enable a feature"""
        try:
            # Check if feature exists
            if feature_id not in self.features:
                logger.error(f"Feature not found: {feature_id}")
                return False
            
            # Check scope
            feature_info = self.features[feature_id]
            scope = feature_info.get('scope', [])
            
            if group_id and 'group' not in scope:
                logger.error(f"Feature {feature_id} not available for groups")
                return False
            
            if user_id and 'user' not in scope:
                logger.error(f"Feature {feature_id} not available for users")
                return False
            
            # Enable feature
            if group_id:
                group_key = f"{group_id}"
                if group_key not in self.group_overrides:
                    self.group_overrides[group_key] = {}
                self.group_overrides[group_key][feature_id] = True
                
                await self._log_feature_change(
                    feature_id, True, enabled_by, group_id=group_id, user_id=user_id
                )
                
                logger.info(f"Enabled feature {feature_id} for group {group_id}")
                
            elif user_id:
                user_key = f"{user_id}"
                if user_key not in self.user_overrides:
                    self.user_overrides[user_key] = {}
                self.user_overrides[user_key][feature_id] = True
                
                await self._log_feature_change(
                    feature_id, True, enabled_by, user_id=user_id
                )
                
                logger.info(f"Enabled feature {feature_id} for user {user_id}")
                
            else:
                self.feature_states[feature_id] = True
                
                await self._log_feature_change(
                    feature_id, True, enabled_by
                )
                
                logger.info(f"Enabled global feature {feature_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable feature {feature_id}: {e}")
            return False
    
    async def disable_feature(self, feature_id: str,
                            disabled_by: int,
                            group_id: Optional[int] = None,
                            user_id: Optional[int] = None) -> bool:
        """Disable a feature"""
        try:
            # Check if feature exists
            if feature_id not in self.features:
                logger.error(f"Feature not found: {feature_id}")
                return False
            
            # Disable feature
            if group_id:
                group_key = f"{group_id}"
                if group_key not in self.group_overrides:
                    self.group_overrides[group_key] = {}
                self.group_overrides[group_key][feature_id] = False
                
                await self._log_feature_change(
                    feature_id, False, disabled_by, group_id=group_id, user_id=user_id
                )
                
                logger.info(f"Disabled feature {feature_id} for group {group_id}")
                
            elif user_id:
                user_key = f"{user_id}"
                if user_key not in self.user_overrides:
                    self.user_overrides[user_key] = {}
                self.user_overrides[user_key][feature_id] = False
                
                await self._log_feature_change(
                    feature_id, False, disabled_by, user_id=user_id
                )
                
                logger.info(f"Disabled feature {feature_id} for user {user_id}")
                
            else:
                self.feature_states[feature_id] = False
                
                await self._log_feature_change(
                    feature_id, False, disabled_by
                )
                
                logger.info(f"Disabled global feature {feature_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable feature {feature_id}: {e}")
            return False
    
    async def _log_feature_change(self, feature_id: str, enabled: bool,
                                changed_by: int, **kwargs):
        """Log feature changes"""
        log_entry = {
            'timestamp': self._get_timestamp(),
            'feature_id': feature_id,
            'enabled': enabled,
            'changed_by': changed_by,
            **kwargs,
        }
        
        # Save to feature log
        log_file = self.config.DATA_DIR / "feature_logs.json"
        logs = JSONEngine.load_json(log_file) if log_file.exists() else []
        logs.append(log_entry)
        JSONEngine.save_json(log_file, logs)
    
    async def get_feature_info(self, feature_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a feature"""
        if feature_id in self.features:
            info = self.features[feature_id].copy()
            info['enabled_globally'] = self.feature_states.get(feature_id, False)
            return info
        return None
    
    async def get_enabled_features(self, group_id: Optional[int] = None,
                                 user_id: Optional[int] = None) -> List[str]:
        """Get list of enabled features"""
        enabled_features = []
        
        for feature_id in self.features:
            if await self.is_enabled(feature_id, group_id, user_id):
                enabled_features.append(feature_id)
        
        return enabled_features
    
    async def get_feature_status(self, group_id: Optional[int] = None,
                               user_id: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """Get detailed status of all features"""
        status = {}
        
        for feature_id, feature_info in self.features.items():
            is_enabled = await self.is_enabled(feature_id, group_id, user_id)
            
            status[feature_id] = {
                'name': feature_info['name'],
                'description': feature_info['description'],
                'enabled': is_enabled,
                'scope': feature_info['scope'],
                'default': feature_info['default'],
                'global_state': self.feature_states.get(feature_id, False),
            }
            
            # Add override info
            if group_id:
                group_key = f"{group_id}"
                if group_key in self.group_overrides:
                    if feature_id in self.group_overrides[group_key]:
                        status[feature_id]['group_override'] = self.group_overrides[group_key][feature_id]
            
            if user_id:
                user_key = f"{user_id}"
                if user_key in self.user_overrides:
                    if feature_id in self.user_overrides[user_key]:
                        status[feature_id]['user_override'] = self.user_overrides[user_key][feature_id]
        
        return status
    
    async def toggle_feature(self, feature_id: str,
                           toggled_by: int,
                           group_id: Optional[int] = None,
                           user_id: Optional[int] = None) -> bool:
        """Toggle a feature on/off"""
        is_enabled = await self.is_enabled(feature_id, group_id, user_id)
        
        if is_enabled:
            return await self.disable_feature(feature_id, toggled_by, group_id, user_id)
        else:
            return await self.enable_feature(feature_id, toggled_by, group_id, user_id)
    
    async def reset_feature(self, feature_id: str,
                          reset_by: int,
                          group_id: Optional[int] = None,
                          user_id: Optional[int] = None) -> bool:
        """Reset a feature to its default state"""
        try:
            if feature_id not in self.features:
                return False
            
            if group_id:
                group_key = f"{group_id}"
                if group_key in self.group_overrides:
                    if feature_id in self.group_overrides[group_key]:
                        del self.group_overrides[group_key][feature_id]
                        logger.info(f"Reset feature {feature_id} for group {group_id}")
                        return True
            
            elif user_id:
                user_key = f"{user_id}"
                if user_key in self.user_overrides:
                    if feature_id in self.user_overrides[user_key]:
                        del self.user_overrides[user_key][feature_id]
                        logger.info(f"Reset feature {feature_id} for user {user_id}")
                        return True
            
            else:
                # Reset to default
                default_state = self.features[feature_id]['default']
                self.feature_states[feature_id] = default_state
                logger.info(f"Reset global feature {feature_id} to default ({default_state})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to reset feature {feature_id}: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def save_state(self):
        """Save feature states to file"""
        try:
            state = {
                'feature_states': self.feature_states,
                'group_overrides': self.group_overrides,
                'user_overrides': self.user_overrides,
                'saved_at': self._get_timestamp(),
            }
            
            state_file = self.config.DATA_DIR / "feature_states.json"
            JSONEngine.save_json(state_file, state)
            
            logger.info("Feature states saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save feature states: {e}")
    
    async def load_state(self):
        """Load feature states from file"""
        try:
            state_file = self.config.DATA_DIR / "feature_states.json"
            
            if state_file.exists():
                state = JSONEngine.load_json(state_file)
                
                self.feature_states = state.get('feature_states', {})
                self.group_overrides = state.get('group_overrides', {})
                self.user_overrides = state.get('user_overrides', {})
                
                logger.info("Feature states loaded successfully")
                
        except Exception as e:
            logger.error(f"Failed to load feature states: {e}")