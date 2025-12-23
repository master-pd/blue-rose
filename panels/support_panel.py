#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Support Panel
Support information handler
"""

import logging
from typing import Dict, Any

from config import Config

logger = logging.getLogger(__name__)

class SupportPanel:
    """Support Information Panel"""
    
    def __init__(self):
        self.config = Config
    
    async def show_support(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Show support information"""
        support_text = f"""
📞 <b>Support & Contact Information</b>

If you need help or have questions about {self.config.BOT_NAME}:

<b>Primary Contact:</b>
👤 {self.config.DEVELOPER}
📱 Telegram: {self.config.DEVELOPER_CONTACT}
📧 Email: ranaeditz333@gmail.com
☎️ Phone: 01847634486

<b>Support Channel:</b>
🌐 https://t.me/master_account_remover_channel

<b>Types of Support:</b>
• 🐛 Bug reports and technical issues
• 💡 Feature requests and suggestions
• 💰 Payment and subscription inquiries
• 🔧 Setup and configuration help
• 📚 General usage questions

<b>Response Time:</b>
⏰ Usually within 24 hours
🕐 Faster response for priority subscribers

<b>Before Contacting:</b>
1. Check /help for basic information
2. Try /start for main menu
3. Read the instructions in group settings

<b>Business Hours:</b>
🕘 9:00 AM - 11:00 PM (GMT+6)
📅 7 days a week

<b>Emergency:</b>
For critical issues affecting bot functionality, please mention "URGENT" in your message.

Thank you for using {self.config.BOT_NAME}! 🌹
        """.strip()
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': support_text,
            'parse_mode': 'HTML',
        }