#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Bot Admin Dashboard
Global admin dashboard
"""

import logging
from typing import Dict, Any

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class BotAdminDashboard:
    """Bot Admin Dashboard"""
    
    def __init__(self):
        self.config = Config
    
    async def show_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Show bot admin dashboard"""
        # Check if user is bot owner/admin
        if user_id != self.config.BOT_OWNER_ID:
            from storage.json_engine import JSONEngine
            bot_admins = JSONEngine.load_json(self.config.JSON_PATHS['bot_admins'], {})
            if user_id not in bot_admins.get('admins', []):
                return {
                    'action': 'send_message',
                    'chat_id': user_id,
                    'text': "❌ Access denied. Bot admin privileges required.",
                    'parse_mode': 'HTML',
                }
        
        # Get statistics
        stats = await self._get_system_stats()
        
        dashboard_text = f"""
👑 <b>Bot Admin Dashboard</b>

<b>System Status:</b>
✅ Bot: Online
📊 Version: {self.config.BOT_VERSION}
⏰ Uptime: Calculating...

<b>Statistics:</b>
📈 Total Groups: {stats['total_groups']}
👥 Active Groups: {stats['active_groups']}
💰 Paid Groups: {stats['paid_groups']}
👤 Total Users: {stats['total_users']}

<b>Payment Statistics:</b>
💵 Total Revenue: {stats['total_revenue']}৳
📋 Pending Requests: {stats['pending_requests']}
✅ Approved Today: {stats['approved_today']}
❌ Rejected Today: {stats['rejected_today']}

<b>System Health:</b>
💾 Memory Usage: {stats['memory_usage']}
🗄️ Storage: {stats['storage_used']}
📁 Database Size: {stats['db_size']}

<b>Quick Actions:</b>
Use the buttons below for specific actions.
        """.strip()
        
        from keyboards.admin_menu import AdminMenuKeyboard
        keyboard = AdminMenuKeyboard().get_dashboard_keyboard()
        
        return {
            'action': 'send_message',
            'chat_id': user_id,
            'text': dashboard_text,
            'parse_mode': 'HTML',
            'reply_markup': keyboard,
        }
    
    async def _get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            # Group statistics
            groups = JSONEngine.load_json(self.config.JSON_PATHS['groups'], {})
            total_groups = len(groups)
            active_groups = sum(1 for g in groups.values() if g.get('active', True))
            paid_groups = sum(1 for g in groups.values() if g.get('plan') != 'free')
            
            # User statistics (simplified)
            users = JSONEngine.load_json(self.config.DATA_DIR / "users" / "users.json", {})
            total_users = len(users)
            
            # Payment statistics
            requests = JSONEngine.load_json(self.config.JSON_PATHS['payment_requests'], [])
            pending_requests = sum(1 for r in requests if r.get('status') == 'pending')
            
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            approved_today = sum(1 for r in requests 
                               if r.get('status') == 'approved' and 
                               r.get('processed_at', '').startswith(today))
            rejected_today = sum(1 for r in requests 
                               if r.get('status') == 'rejected' and 
                               r.get('processed_at', '').startswith(today))
            
            # Revenue calculation (simplified)
            total_revenue = paid_groups * 100  # Simplified calculation
            
            # System stats (simplified)
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'total_groups': total_groups,
                'active_groups': active_groups,
                'paid_groups': paid_groups,
                'total_users': total_users,
                'pending_requests': pending_requests,
                'approved_today': approved_today,
                'rejected_today': rejected_today,
                'total_revenue': total_revenue,
                'memory_usage': f"{memory.percent}%",
                'storage_used': f"{disk.percent}%",
                'db_size': "Calculating...",
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {
                'total_groups': 0,
                'active_groups': 0,
                'paid_groups': 0,
                'total_users': 0,
                'pending_requests': 0,
                'approved_today': 0,
                'rejected_today': 0,
                'total_revenue': 0,
                'memory_usage': "N/A",
                'storage_used': "N/A",
                'db_size': "N/A",
            }