#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Permission Engine
Manages hierarchical permissions and access control
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from enum import Enum

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class Role(Enum):
    """User Roles"""
    BOT_OWNER = 1000  # Root / God Mode
    BOT_ADMIN = 900   # Global Operator
    GROUP_OWNER = 800 # Group Owner
    GROUP_ADMIN = 700 # Group Admin
    MODERATOR = 600   # Moderator
    MEMBER = 500      # Regular Member
    GUEST = 400       # Guest / Restricted
    RESTRICTED = 300  # Restricted User
    BANNED = 200      # Banned User
    EXTERNAL_BOT = 100 # External Bot

class Permission(Enum):
    """Permission Types"""
    # Bot Level Permissions
    MANAGE_BOT_ADMINS = "manage_bot_admins"
    MANAGE_GLOBAL_SETTINGS = "manage_global_settings"
    VIEW_GLOBAL_ANALYTICS = "view_global_analytics"
    FORCE_JOIN_LEAVE = "force_join_leave"
    OVERRIDE_FEATURES = "override_features"
    EMERGENCY_CONTROL = "emergency_control"
    
    # Group Level Permissions
    MANAGE_GROUP_SETTINGS = "manage_group_settings"
    MANAGE_GROUP_ADMINS = "manage_group_admins"
    MANAGE_MODERATORS = "manage_moderators"
    VIEW_GROUP_ANALYTICS = "view_group_analytics"
    MANAGE_PAYMENTS = "manage_payments"
    MANAGE_SERVICES = "manage_services"
    
    # Moderation Permissions
    WARN_USERS = "warn_users"
    MUTE_USERS = "mute_users"
    BAN_USERS = "ban_users"
    DELETE_MESSAGES = "delete_messages"
    PIN_MESSAGES = "pin_messages"
    RESTRICT_USERS = "restrict_users"
    
    # Feature Permissions
    USE_AI_RESPONSES = "use_ai_responses"
    USE_SCHEDULED_MESSAGES = "use_scheduled_messages"
    USE_NIGHT_MODE = "use_night_mode"
    USE_AUTO_REPLIES = "use_auto_replies"
    USE_MODERATION = "use_moderation"
    
    # Payment Permissions
    REQUEST_PAYMENT = "request_payment"
    APPROVE_PAYMENTS = "approve_payments"
    VIEW_PAYMENT_HISTORY = "view_payment_history"
    
    # Access Permissions
    ACCESS_ADMIN_PANEL = "access_admin_panel"
    ACCESS_GROUP_PANEL = "access_group_panel"
    ACCESS_BOT_PANEL = "access_bot_panel"
    ACCESS_ANALYTICS = "access_analytics"

class PermissionEngine:
    """Permission Engine"""
    
    def __init__(self):
        self.config = Config
        self.role_permissions = self._load_role_permissions()
        self.user_overrides = {}
        self.group_overrides = {}
        
    def _load_role_permissions(self) -> Dict[Role, Set[Permission]]:
        """Load default role permissions"""
        return {
            Role.BOT_OWNER: set([
                # All permissions
                perm for perm in Permission
            ]),
            
            Role.BOT_ADMIN: set([
                Permission.MANAGE_GROUP_SETTINGS,
                Permission.MANAGE_GROUP_ADMINS,
                Permission.VIEW_GLOBAL_ANALYTICS,
                Permission.FORCE_JOIN_LEAVE,
                Permission.MANAGE_PAYMENTS,
                Permission.APPROVE_PAYMENTS,
                Permission.ACCESS_BOT_PANEL,
                Permission.ACCESS_ANALYTICS,
                Permission.EMERGENCY_CONTROL,
            ]),
            
            Role.GROUP_OWNER: set([
                Permission.MANAGE_GROUP_SETTINGS,
                Permission.MANAGE_GROUP_ADMINS,
                Permission.MANAGE_MODERATORS,
                Permission.VIEW_GROUP_ANALYTICS,
                Permission.MANAGE_SERVICES,
                Permission.WARN_USERS,
                Permission.MUTE_USERS,
                Permission.BAN_USERS,
                Permission.DELETE_MESSAGES,
                Permission.PIN_MESSAGES,
                Permission.RESTRICT_USERS,
                Permission.USE_AI_RESPONSES,
                Permission.USE_SCHEDULED_MESSAGES,
                Permission.USE_NIGHT_MODE,
                Permission.USE_AUTO_REPLIES,
                Permission.USE_MODERATION,
                Permission.REQUEST_PAYMENT,
                Permission.VIEW_PAYMENT_HISTORY,
                Permission.ACCESS_GROUP_PANEL,
            ]),
            
            Role.GROUP_ADMIN: set([
                Permission.MANAGE_MODERATORS,
                Permission.WARN_USERS,
                Permission.MUTE_USERS,
                Permission.DELETE_MESSAGES,
                Permission.PIN_MESSAGES,
                Permission.RESTRICT_USERS,
                Permission.USE_AI_RESPONSES,
                Permission.USE_SCHEDULED_MESSAGES,
                Permission.USE_NIGHT_MODE,
                Permission.USE_AUTO_REPLIES,
                Permission.USE_MODERATION,
                Permission.ACCESS_GROUP_PANEL,
            ]),
            
            Role.MODERATOR: set([
                Permission.WARN_USERS,
                Permission.MUTE_USERS,
                Permission.DELETE_MESSAGES,
                Permission.RESTRICT_USERS,
                Permission.USE_MODERATION,
            ]),
            
            Role.MEMBER: set([
                Permission.USE_AI_RESPONSES,
                Permission.USE_AUTO_REPLIES,
            ]),
            
            Role.GUEST: set([
                # No permissions by default
            ]),
            
            Role.RESTRICTED: set([
                # Very limited permissions
            ]),
            
            Role.BANNED: set([
                # No permissions
            ]),
            
            Role.EXTERNAL_BOT: set([
                # Bot detection permissions
            ]),
        }
    
    async def get_user_role(self, user_id: int, chat_id: Optional[int] = None) -> Role:
        """Get user's role in a specific context"""
        try:
            # Check if user is bot owner
            if user_id == self.config.BOT_OWNER_ID:
                return Role.BOT_OWNER
            
            # Check if user is bot admin
            bot_admins = JSONEngine.load_json(self.config.JSON_PATHS['bot_admins'])
            if user_id in bot_admins.get('admins', []):
                return Role.BOT_ADMIN
            
            # If chat_id is provided, check group-specific roles
            if chat_id:
                group_admins_path = self.config.DATA_DIR / "groups" / "group_admins.json"
                if group_admins_path.exists():
                    group_admins = JSONEngine.load_json(group_admins_path)
                    
                    if str(chat_id) in group_admins:
                        chat_data = group_admins[str(chat_id)]
                        
                        # Check group owner
                        if user_id == chat_data.get('owner_id'):
                            return Role.GROUP_OWNER
                        
                        # Check group admin
                        if user_id in chat_data.get('admin_ids', []):
                            return Role.GROUP_ADMIN
                        
                        # Check moderator
                        if user_id in chat_data.get('moderator_ids', []):
                            return Role.MODERATOR
            
            # Default to MEMBER role
            return Role.MEMBER
            
        except Exception as e:
            logger.error(f"Failed to get user role: {e}")
            return Role.GUEST
    
    async def has_permission(self, user_id: int, permission: Permission, 
                           chat_id: Optional[int] = None) -> bool:
        """Check if user has a specific permission"""
        try:
            # Get user role
            role = await self.get_user_role(user_id, chat_id)
            
            # Check role permissions
            if permission in self.role_permissions.get(role, set()):
                # Check for overrides
                if await self._check_overrides(user_id, permission, chat_id, allow=True):
                    return True
            
            # Check for user-specific overrides
            user_key = f"{user_id}"
            if user_key in self.user_overrides:
                user_perms = self.user_overrides[user_key]
                if permission in user_perms.get('allowed', set()):
                    return True
                if permission in user_perms.get('denied', set()):
                    return False
            
            # Check for group-specific overrides if chat_id provided
            if chat_id:
                group_key = f"{chat_id}"
                if group_key in self.group_overrides:
                    group_perms = self.group_overrides[group_key]
                    if permission in group_perms.get('allowed', set()):
                        return True
                    if permission in group_perms.get('denied', set()):
                        return False
            
            # Check time-based restrictions
            if not await self._check_time_restrictions(user_id, chat_id):
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False
    
    async def _check_overrides(self, user_id: int, permission: Permission,
                             chat_id: Optional[int], allow: bool) -> bool:
        """Check for permission overrides"""
        # This would check database for custom overrides
        # For now, return the default allow value
        return allow
    
    async def _check_time_restrictions(self, user_id: int, chat_id: Optional[int]) -> bool:
        """Check if user is restricted by time"""
        # Check quiet hours, night mode, etc.
        # For now, always allow
        return True
    
    async def grant_permission(self, user_id: int, permission: Permission,
                             chat_id: Optional[int] = None, 
                             granted_by: Optional[int] = None):
        """Grant a permission to a user"""
        try:
            if chat_id:
                # Group-specific permission
                group_key = f"{chat_id}"
                if group_key not in self.group_overrides:
                    self.group_overrides[group_key] = {
                        'allowed': set(),
                        'denied': set(),
                    }
                self.group_overrides[group_key]['allowed'].add(permission)
            else:
                # User-specific permission
                user_key = f"{user_id}"
                if user_key not in self.user_overrides:
                    self.user_overrides[user_key] = {
                        'allowed': set(),
                        'denied': set(),
                    }
                self.user_overrides[user_key]['allowed'].add(permission)
            
            # Log the permission grant
            await self._log_permission_change(
                user_id, permission, 'granted', chat_id, granted_by
            )
            
            logger.info(f"Permission {permission.value} granted to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to grant permission: {e}")
            return False
    
    async def revoke_permission(self, user_id: int, permission: Permission,
                              chat_id: Optional[int] = None,
                              revoked_by: Optional[int] = None):
        """Revoke a permission from a user"""
        try:
            if chat_id:
                # Group-specific permission
                group_key = f"{chat_id}"
                if group_key in self.group_overrides:
                    self.group_overrides[group_key]['allowed'].discard(permission)
                    self.group_overrides[group_key]['denied'].add(permission)
            else:
                # User-specific permission
                user_key = f"{user_id}"
                if user_key in self.user_overrides:
                    self.user_overrides[user_key]['allowed'].discard(permission)
                    self.user_overrides[user_key]['denied'].add(permission)
            
            # Log the permission revocation
            await self._log_permission_change(
                user_id, permission, 'revoked', chat_id, revoked_by
            )
            
            logger.info(f"Permission {permission.value} revoked from user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke permission: {e}")
            return False
    
    async def _log_permission_change(self, user_id: int, permission: Permission,
                                   action: str, chat_id: Optional[int],
                                   changed_by: Optional[int]):
        """Log permission changes"""
        log_entry = {
            'timestamp': self._get_timestamp(),
            'user_id': user_id,
            'permission': permission.value,
            'action': action,
            'chat_id': chat_id,
            'changed_by': changed_by,
        }
        
        # Save to permissions log
        log_file = self.config.DATA_DIR / "permission_logs.json"
        logs = JSONEngine.load_json(log_file) if log_file.exists() else []
        logs.append(log_entry)
        JSONEngine.save_json(log_file, logs)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def get_user_permissions(self, user_id: int, chat_id: Optional[int] = None) -> Set[Permission]:
        """Get all permissions for a user"""
        try:
            # Get base role permissions
            role = await self.get_user_role(user_id, chat_id)
            permissions = self.role_permissions.get(role, set()).copy()
            
            # Add user-specific permissions
            user_key = f"{user_id}"
            if user_key in self.user_overrides:
                permissions.update(self.user_overrides[user_key].get('allowed', set()))
                permissions.difference_update(self.user_overrides[user_key].get('denied', set()))
            
            # Add group-specific permissions if chat_id provided
            if chat_id:
                group_key = f"{chat_id}"
                if group_key in self.group_overrides:
                    permissions.update(self.group_overrides[group_key].get('allowed', set()))
                    permissions.difference_update(self.group_overrides[group_key].get('denied', set()))
            
            return permissions
            
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return set()
    
    async def can_perform_action(self, user_id: int, action: str,
                               chat_id: Optional[int] = None) -> bool:
        """Check if user can perform a specific action"""
        # Map actions to permissions
        action_to_permission = {
            # Bot actions
            'add_bot_admin': Permission.MANAGE_BOT_ADMINS,
            'remove_bot_admin': Permission.MANAGE_BOT_ADMINS,
            'view_global_stats': Permission.VIEW_GLOBAL_ANALYTICS,
            'force_join': Permission.FORCE_JOIN_LEAVE,
            'force_leave': Permission.FORCE_JOIN_LEAVE,
            'override_feature': Permission.OVERRIDE_FEATURES,
            
            # Group actions
            'change_group_settings': Permission.MANAGE_GROUP_SETTINGS,
            'add_group_admin': Permission.MANAGE_GROUP_ADMINS,
            'remove_group_admin': Permission.MANAGE_GROUP_ADMINS,
            'view_group_stats': Permission.VIEW_GROUP_ANALYTICS,
            'manage_group_payments': Permission.MANAGE_PAYMENTS,
            'toggle_service': Permission.MANAGE_SERVICES,
            
            # Moderation actions
            'warn_user': Permission.WARN_USERS,
            'mute_user': Permission.MUTE_USERS,
            'ban_user': Permission.BAN_USERS,
            'delete_message': Permission.DELETE_MESSAGES,
            'pin_message': Permission.PIN_MESSAGES,
            'restrict_user': Permission.RESTRICT_USERS,
            
            # Feature actions
            'use_ai': Permission.USE_AI_RESPONSES,
            'schedule_message': Permission.USE_SCHEDULED_MESSAGES,
            'set_night_mode': Permission.USE_NIGHT_MODE,
            'set_auto_reply': Permission.USE_AUTO_REPLIES,
            'use_moderation': Permission.USE_MODERATION,
            
            # Payment actions
            'request_payment': Permission.REQUEST_PAYMENT,
            'approve_payment': Permission.APPROVE_PAYMENTS,
            'view_payments': Permission.VIEW_PAYMENT_HISTORY,
            
            # Panel access
            'access_admin_panel': Permission.ACCESS_ADMIN_PANEL,
            'access_group_panel': Permission.ACCESS_GROUP_PANEL,
            'access_bot_panel': Permission.ACCESS_BOT_PANEL,
            'access_analytics': Permission.ACCESS_ANALYTICS,
        }
        
        if action in action_to_permission:
            permission = action_to_permission[action]
            return await self.has_permission(user_id, permission, chat_id)
        
        # Unknown action - default to False for security
        logger.warning(f"Unknown action: {action}")
        return False