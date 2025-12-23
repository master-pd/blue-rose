#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Admin Menu Keyboard
Admin panel keyboard generator
"""

class AdminMenuKeyboard:
    """Admin Menu Keyboard Generator"""
    
    def get_dashboard_keyboard(self):
        """Get admin dashboard keyboard"""
        return {
            'inline_keyboard': [
                [
                    {'text': '📋 Group List', 'callback_data': 'admin_groups'},
                    {'text': '💰 Payments', 'callback_data': 'admin_payments'},
                ],
                [
                    {'text': '⚙️ Force Join/Leave', 'callback_data': 'admin_force'},
                    {'text': '🎛️ Feature Control', 'callback_data': 'admin_features'},
                ],
                [
                    {'text': '🚨 Emergency', 'callback_data': 'admin_emergency'},
                    {'text': '📊 Analytics', 'callback_data': 'admin_analytics'},
                ],
                [
                    {'text': '💾 Backup', 'callback_data': 'admin_backup'},
                    {'text': '🔄 Restart', 'callback_data': 'admin_restart'},
                ],
                [
                    {'text': '🏠 Home', 'callback_data': 'admin_home'},
                ],
            ]
        }
    
    def get_group_list_keyboard(self, current_page: int, total_pages: int):
        """Get group list pagination keyboard"""
        keyboard = []
        
        # Navigation buttons
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append({'text': '◀️ Previous', 'callback_data': f'admin_groups_page_{current_page-1}'})
        
        nav_buttons.append({'text': f'📄 {current_page}/{total_pages}', 'callback_data': 'admin_groups_info'})
        
        if current_page < total_pages:
            nav_buttons.append({'text': 'Next ▶️', 'callback_data': f'admin_groups_page_{current_page+1}'})
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Action buttons
        keyboard.extend([
            [
                {'text': '🔄 Refresh', 'callback_data': f'admin_groups_page_{current_page}'},
                {'text': '📊 Stats', 'callback_data': 'admin_groups_stats'},
            ],
            [
                {'text': '🏠 Dashboard', 'callback_data': 'admin_dashboard'},
            ],
        ])
        
        return {'inline_keyboard': keyboard}