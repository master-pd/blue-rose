#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Add Group Panel
Group addition and setup handler
"""

import logging
from typing import Dict, Any

from config import Config

logger = logging.getLogger(__name__)

class AddGroupPanel:
    """Add Group Setup Panel"""
    
    def __init__(self):
        self.config = Config
    
    async def show_add_group_instructions(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Show group addition instructions"""
        instructions = f"""
📦 <b>How to Add {self.config.BOT_NAME} to Your Group</b>

<b>Step 1: Add Bot to Group</b>
1. Go to your Telegram group
2. Click on group name → "Add Members"
3. Search for: @{self.config.BOT_USERNAME}
4. Add the bot to your group

<b>Step 2: Make Bot Administrator</b>
1. In your group, go to:
   Group Settings → Administrators → Add Admin
2. Select @{self.config.BOT_USERNAME}
3. Enable <b>ALL</b> permissions:
   • ✅ Change group info
   • ✅ Delete messages
   • ✅ Ban users
   • ✅ Invite users via link
   • ✅ Pin messages
   • ✅ Add new admins
4. Click "Save"

<b>Step 3: Configure Bot</b>
1. In your group, type: /settings
2. Follow the setup wizard
3. Enable desired features
4. Set up payment plan if needed

<b>Step 4: Test Bot</b>
1. Send a message like "hello"
2. Bot should respond
3. Try admin commands: /settings

<b>Important Notes:</b>
⚠️ Bot <b>MUST</b> have all admin permissions
⚠️ Without permissions, features won't work
⚠️ Contact support if you face issues

<b>Need Help?</b>
Contact: {self.config.DEVELOPER_CONTACT}
        """.strip()
        
        return {
            'action': 'send_message',
            'chat_id': message.get('chat', {}).get('id'),
            'text': instructions,
            'parse_mode': 'HTML',
        }