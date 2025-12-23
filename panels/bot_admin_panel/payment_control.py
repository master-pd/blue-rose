#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Payment Control Panel
Payment request management
"""

from payments.approval_panel import ApprovalPanel

class PaymentControlPanel:
    """Payment Control Panel"""
    
    def __init__(self):
        self.approval_panel = ApprovalPanel()
    
    async def show_payment_requests(self, user_id: int) -> Dict[str, Any]:
        """Show pending payment requests"""
        requests = await self.approval_panel.get_pending_requests()
        
        if not requests:
            return {
                'action': 'send_message',
                'chat_id': user_id,
                'text': "📭 No pending payment requests.",
                'parse_mode': 'HTML',
            }
        
        request_text = f"""
💰 <b>Pending Payment Requests</b>
Total: {len(requests)} requests

"""
        
        for req in requests:
            request_text += f"""
📋 Request #{req['request_id']}
👥 Group ID: <code>{req['chat_id']}</code>
📅 Plan: {req['plan'].title()}
👤 Requested by: {req['admin_info'].get('username', 'Unknown')}
⏰ Created: {req['created_at'][:10]}
"""
        
        from keyboards.admin_menu import AdminMenuKeyboard
        keyboard = AdminMenuKeyboard().get_payment_control_keyboard()
        
        return {
            'action': 'send_message',
            'chat_id': user_id,
            'text': request_text,
            'parse_mode': 'HTML',
            'reply_markup': keyboard,
        }