#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Group Admin Dashboard
Group-specific admin dashboard
"""

import logging
from typing import Dict, Any

from config import Config
from storage.json_engine import JSONEngine
from core.permission_engine import PermissionEngine

logger = logging.getLogger(__name__)

class GroupAdminDashboard:
    """Group Admin Dashboard"""
    
    def __init__(self):
        self.config = Config
        self.permission_engine = PermissionEngine()
    
    async def show_dashboard(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        """Show group admin dashboard"""
        # Check permissions
        can_access = await self.permission_engine.can_perform_action(
            user_id, 'access_group_panel', chat_id
        )
        
        if not can_access:
            return {
                'action': 'send_message',
                'chat_id': chat_id,
                'text': "❌ You don't have permission to access group admin panel.",
                'parse_mode': 'HTML',
            }
        
        # Get group info
        groups = JSONEngine.load_json(self.config.JSON_PATHS['groups'], {})
        group_key = str(chat_id)
        
        if group_key not in groups:
            return {
                'action': 'send_message',
                'chat_id': chat_id,
                'text': "❌ Group not found in database.",
                'parse_mode': 'HTML',
            }
        
        group_data = groups[group_key]
        
        # Build dashboard
        dashboard_text = f"""
🏠 <b>Group Admin Dashboard</b>

<b>Group Info:</b>
📛 Name: {group_data.get('title', 'Unknown Group')}
🆔 ID: <code>{chat_id}</code>
📅 Created: {group_data.get('created_at', 'Unknown')[:10]}

<b>Subscription:</b>
💰 Plan: {group_data.get('plan', 'free').title()}
✅ Status: {'Active' if group_data.get('plan_active', False) else 'Inactive'}
📅 Expiry: {group_data.get('expiry_date', 'N/A')[:10] if group_data.get('expiry_date') else 'N/A'}

<b>Statistics:</b>
👥 Members: Calculating...
💬 Messages: Calculating...
🛡️ Mod Actions: Calculating...

<b>Features Status:</b>
🤖 Auto-reply: {'✅ Enabled' if group_data.get('auto_reply', True) else '❌ Disabled'}
🛡️ Moderation: {'✅ Enabled' if group_data.get('moderation', True) else '❌ Disabled'}
📅 Scheduling: {'✅ Enabled' if group_data.get('scheduling', False) else '❌ Disabled'}

<b>Quick Actions:</b>
Use buttons below to manage group settings.
        """.strip()
        
        from keyboards.group_admin_menu import GroupAdminMenuKeyboard
        keyboard = GroupAdminMenuKeyboard().get_dashboard_keyboard()
        
        return {
            'action': 'send_message',
            'chat_id': chat_id,
            'text': dashboard_text,
            'parse_mode': 'HTML',
            'reply_markup': keyboard,
        }