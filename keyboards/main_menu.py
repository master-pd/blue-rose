#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Main Menu Keyboard
Main menu keyboard generator
"""

import telebot.types as types

class MainMenuKeyboard:
    """Main Menu Keyboard Generator"""
    
    @staticmethod
    def get_main_menu() -> types.InlineKeyboardMarkup:
        """Get main menu keyboard"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            types.InlineKeyboardButton("🏠 Home", callback_data="menu_home"),
            types.InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"),
            types.InlineKeyboardButton("📊 Stats", callback_data="menu_stats"),
            types.InlineKeyboardButton("🛡️ Moderation", callback_data="menu_moderation"),
            types.InlineKeyboardButton("📅 Schedule", callback_data="menu_schedule"),
            types.InlineKeyboardButton("🕌 Prayer Times", callback_data="menu_prayer"),
            types.InlineKeyboardButton("💰 Payments", callback_data="menu_payments"),
            types.InlineKeyboardButton("📞 Support", callback_data="menu_support"),
            types.InlineKeyboardButton("📝 Feedback", callback_data="menu_feedback"),
            types.InlineKeyboardButton("🔔 Notifications", callback_data="menu_notifications"),
            types.InlineKeyboardButton("📋 Templates", callback_data="menu_templates"),
            types.InlineKeyboardButton("🤖 Auto-replies", callback_data="menu_auto_reply"),
            types.InlineKeyboardButton("🔓 Unlock Features", callback_data="menu_unlock_features"),
            types.InlineKeyboardButton("🔙 Back", callback_data="main_menu_back")
        ]
        
        # Add buttons in rows of 2
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard
