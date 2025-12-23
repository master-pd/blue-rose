#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Main Menu Keyboard
Main menu keyboard generator
"""

class MainMenuKeyboard:
    """Main Menu Keyboard Generator"""
    
    def get_main_menu(self):
        """Get main menu keyboard"""
        return {
            'inline_keyboard': [
                [
                    {'text': '🏠 Home', 'callback_data': 'menu_home'},
                    {'text': '⚙️ Settings', 'callback_data': 'menu_settings'},
                ],
                [
                    {'text': '📊 Stats', 'callback_data': 'menu_stats'},
                    {'text': '🛡️ Moderation', 'callback_data': 'menu_moderation'},
                ],
                [
                    {'text': '📅 Schedule', 'callback_data': 'menu_schedule'},
                    {'text': '🕌 Prayer Times', 'callback_data': 'menu_prayer'},
                ],
                [
                    {'text': '💰 Payments', 'callback_data': 'menu_payments'},
                    {'text': '📞 Support', 'callback_data': 'menu_support'},
                ],
            ]
        }