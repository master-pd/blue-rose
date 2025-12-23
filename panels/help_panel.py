#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Help Panel
Help command handler
"""

import logging
from typing import Dict, Any

from config import Config

logger = logging.getLogger(__name__)

class HelpPanel:
    """Help Command Panel"""
    
    def __init__(self):
        self.config = Config
    
    async def show_help(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Show help message"""
        help_text = f"""
🆘 <b>{self.config.BOT_NAME} Help</b>

🤖 <b>About:</b>
I'm an advanced Telegram bot with multiple features for group management and automation.

<b>Basic Commands:</b>
/start - Start the bot
/help - Show this help message
/about - About the bot
/groups - List your groups
/plan - Subscription information
/support - Support channel

<b>Group Admin Commands:</b>
/settings - Group settings panel
/stats - Group statistics
/members - Member management

<b>Bot Admin Commands:</b>
/admin - Bot admin panel (owners/admins only)
/analytics - System analytics
/backup - Backup system

<b>Group Features:</b>
• 🤖 Auto-reply system
• 🛡️ Moderation (anti-spam, anti-flood)
• 📅 Scheduled messages
• 🕌 Prayer time alerts
• 👥 Welcome/goodbye messages
• 🌙 Night mode
• 💰 Payment plans

<b>Setup Guide:</b>
1. Add me to your group
2. Make me administrator
3. Use /settings to configure features
4. Set up payment plan if needed

<b>Need Help?</b>
Join our support channel: {self.config.DEVELOPER_CONTACT}
Email: ranaeditz333@gmail.com

<b>Developer:</b> {self.config.DEVELOPER}
        """.strip()
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': help_text,
            'parse_mode': 'HTML',
        }