#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Emergency Lock System
Global lockdown and emergency controls
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class LockLevel(Enum):
    """Emergency lock levels"""
    NORMAL = 0      # Everything operational
    WARNING = 1     # Enhanced monitoring
    RESTRICTED = 2  # Limited functionality
    LOCKDOWN = 3    # Read-only mode
    SHUTDOWN = 4    # Complete stop

class EmergencyLock:
    """Emergency Lock Manager"""
    
    def __init__(self):
        self.config = Config
        self.lock_file = self.config.DATA_DIR / "emergency_lock.json"
        self.current_level = LockLevel.NORMAL
        
        # Load lock status
        self._load_lock_status()
    
    def _load_lock_status(self):
        """Load lock status from file"""
        try:
            if self.lock_file.exists():
                lock_data = JSONEngine.load_json(self.lock_file)
                level_name = lock_data.get('level', 'NORMAL')
                self.current_level = LockLevel[level_name]
            else:
                self._save_lock_status()
        except Exception as e:
            logger.error(f"Failed to load lock status: {e}")
    
    def _save_lock_status(self):
        """Save lock status to file"""
        try:
            lock_data = {
                'level': self.current_level.name,
                'timestamp': datetime.now().isoformat(),
                'reason': getattr(self, 'lock_reason', ''),
                'initiated_by': getattr(self, 'lock_initiator', 0)
            }
            JSONEngine.save_json(self.lock_file, lock_data)
        except Exception as e:
            logger.error(f"Failed to save lock status: {e}")
    
    async def set_lock_level(self, level: LockLevel, 
                           reason: str = "",
                           initiator_id: int = 0) -> bool:
        """Set emergency lock level"""
        try:
            old_level = self.current_level
            
            # Check if escalation is allowed
            if not await self._validate_escalation(level, initiator_id):
                return False
            
            self.current_level = level
            self.lock_reason = reason
            self.lock_initiator = initiator_id
            
            # Apply restrictions based on level
            await self._apply_restrictions(old_level, level)
            
            # Save status
            self._save_lock_status()
            
            # Log the change
            logger.warning(
                f"Emergency lock changed: {old_level.name} -> {level.name}. "
                f"Reason: {reason}"
            )
            
            # Notify if needed
            if level.value >= LockLevel.RESTRICTED.value:
                await self._notify_admins(level, reason)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to set lock level: {e}")
            return False
    
    async def _validate_escalation(self, new_level: LockLevel, 
                                 initiator_id: int) -> bool:
        """Validate if escalation is allowed"""
        # Bot owner can do anything
        if initiator_id == self.config.BOT_OWNER_ID:
            return True
        
        # Bot admins can set up to RESTRICTED
        if (initiator_id in self.config.BOT_ADMIN_IDS and 
            new_level.value <= LockLevel.RESTRICTED.value):
            return True
        
        # Only owner can do LOCKDOWN or SHUTDOWN
        if new_level.value >= LockLevel.LOCKDOWN.value:
            logger.error(
                f"Non-owner {initiator_id} attempted lockdown/shutdown"
            )
            return False
        
        return True
    
    async def _apply_restrictions(self, old_level: LockLevel, 
                                new_level: LockLevel):
        """Apply restrictions based on lock level"""
        restrictions = {
            LockLevel.NORMAL: {
                'message_processing': True,
                'command_processing': True,
                'auto_replies': True,
                'moderation': True,
                'payments': True,
                'new_groups': True
            },
            LockLevel.WARNING: {
                'message_processing': True,
                'command_processing': True,
                'auto_replies': True,
                'moderation': True,
                'payments': True,
                'new_groups': True,
                'enhanced_logging': True
            },
            LockLevel.RESTRICTED: {
                'message_processing': True,
                'command_processing': True,
                'auto_replies': False,
                'moderation': False,
                'payments': False,
                'new_groups': False,
                'rate_limited': True
            },
            LockLevel.LOCKDOWN: {
                'message_processing': True,
                'command_processing': False,
                'auto_replies': False,
                'moderation': False,
                'payments': False,
                'new_groups': False,
                'read_only': True
            },
            LockLevel.SHUTDOWN: {
                'message_processing': False,
                'command_processing': False,
                'auto_replies': False,
                'moderation': False,
                'payments': False,
                'new_groups': False,
                'shutdown': True
            }
        }
        
        new_restrictions = restrictions[new_level]
        logger.info(f"Applying restrictions for level {new_level.name}: {new_restrictions}")
    
    async def _notify_admins(self, level: LockLevel, reason: str):
        """Notify admins about emergency lock"""
        # This would be implemented with actual notification logic
        # For now, just log
        logger.warning(
            f"Emergency {level.name} active. Notifying admins. Reason: {reason}"
        )
    
    def get_lock_status(self) -> Dict[str, Any]:
        """Get current lock status"""
        return {
            'level': self.current_level.name,
            'level_value': self.current_level.value,
            'description': self._get_level_description(self.current_level),
            'restrictions': self._get_current_restrictions(),
            'file_path': str(self.lock_file),
            'can_escalate': self.current_level.value < LockLevel.SHUTDOWN.value,
            'can_deescalate': self.current_level.value > LockLevel.NORMAL.value
        }
    
    def _get_level_description(self, level: LockLevel) -> str:
        """Get description for lock level"""
        descriptions = {
            LockLevel.NORMAL: "Normal operation - All features active",
            LockLevel.WARNING: "Warning mode - Enhanced monitoring",
            LockLevel.RESTRICTED: "Restricted mode - Limited functionality",
            LockLevel.LOCKDOWN: "Lockdown mode - Read-only, admin only",
            LockLevel.SHUTDOWN: "Shutdown mode - Complete stop"
        }
        return descriptions.get(level, "Unknown")
    
    def _get_current_restrictions(self) -> Dict[str, bool]:
        """Get current restrictions based on level"""
        restrictions = {
            LockLevel.NORMAL: {},
            LockLevel.WARNING: {'enhanced_logging': True},
            LockLevel.RESTRICTED: {
                'auto_replies': False,
                'moderation': False,
                'payments': False,
                'new_groups': False
            },
            LockLevel.LOCKDOWN: {
                'commands': False,
                'auto_replies': False,
                'moderation': False,
                'payments': False,
                'new_groups': False,
                'read_only': True
            },
            LockLevel.SHUTDOWN: {
                'all_operations': False,
                'shutdown': True
            }
        }
        return restrictions.get(self.current_level, {})
    
    async def check_permission(self, operation: str, 
                             user_id: int = 0) -> bool:
        """Check if operation is allowed under current lock"""
        # Bot owner always has permission
        if user_id == self.config.BOT_OWNER_ID:
            return True
        
        # Get restrictions for current level
        restrictions = self._get_current_restrictions()
        
        # Map operations to restrictions
        operation_map = {
            'send_message': 'auto_replies',
            'process_command': 'commands',
            'moderate': 'moderation',
            'process_payment': 'payments',
            'join_group': 'new_groups',
            'all': 'all_operations'
        }
        
        restriction_key = operation_map.get(operation, operation)
        
        if restriction_key == 'shutdown' and self.current_level == LockLevel.SHUTDOWN:
            return False
        
        if restriction_key in restrictions:
            return not restrictions[restriction_key]
        
        return True
    
    async def emergency_release(self, initiator_id: int) -> bool:
        """Emergency release from lockdown/shutdown"""
        if initiator_id != self.config.BOT_OWNER_ID:
            logger.error(f"Non-owner {initiator_id} attempted emergency release")
            return False
        
        if self.current_level in [LockLevel.LOCKDOWN, LockLevel.SHUTDOWN]:
            await self.set_lock_level(LockLevel.NORMAL, 
                                    "Emergency release by owner",
                                    initiator_id)
            return True
        
        return False
    
    def is_operational(self) -> bool:
        """Check if system is operational"""
        return self.current_level.value < LockLevel.SHUTDOWN.value
    
    def is_read_only(self) -> bool:
        """Check if system is in read-only mode"""
        return self.current_level == LockLevel.LOCKDOWN