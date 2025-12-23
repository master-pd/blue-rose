#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Group List Panel
List all groups managed by bot
"""

import logging
from typing import Dict, Any, List

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class GroupListPanel:
    """Group List Management Panel"""
    
    def __init__(self):
        self.config = Config
    
    async def show_group_list(self, user_id: int, page: int = 1) -> Dict[str, Any]:
        """Show paginated group list"""
        groups = JSONEngine.load_json(self.config.JSON_PATHS['groups'], {})
        
        if not groups:
            return {
                'action': 'send_message',
                'chat_id': user_id,
                'text': "📭 No groups are currently managed by the bot.",
                'parse_mode': 'HTML',
            }
        
        # Paginate groups
        groups_list = list(groups.items())
        items_per_page = 10
        total_pages = (len(groups_list) + items_per_page - 1) // items_per_page
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_groups = groups_list[start_idx:end_idx]
        
        # Build group list text
        group_text = f"""
📋 <b>Managed Groups</b>
Page {page}/{total_pages} • Total: {len(groups_list)} groups

"""
        
        for idx, (chat_id_str, group_data) in enumerate(page_groups, start_idx + 1):
            title = group_data.get('title', 'Unknown Group')
            plan = group_data.get('plan', 'free')
            active = group_data.get('active', True)
            
            status_emoji = '✅' if active else '❌'
            plan_emoji = '💰' if plan != 'free' else '🆓'
            
            group_text += f"{idx}. {status_emoji} <b>{title}</b>\n"
            group_text += f"   ID: <code>{chat_id_str}</code>\n"
            group_text += f"   Plan: {plan_emoji} {plan.title()}\n"
            
            # Show expiry if paid plan
            if plan != 'free' and group_data.get('expiry_date'):
                group_text += f"   Expires: {group_data['expiry_date'][:10]}\n"
            
            group_text += "\n"
        
        group_text += "\nUse /admin to return to admin dashboard."
        
        from keyboards.admin_menu import AdminMenuKeyboard
        keyboard = AdminMenuKeyboard().get_group_list_keyboard(page, total_pages)
        
        return {
            'action': 'send_message',
            'chat_id': user_id,
            'text': group_text,
            'parse_mode': 'HTML',
            'reply_markup': keyboard,
        }