#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Payment Menu Keyboard
Payment and plan management keyboard layouts
"""

from typing import List, Dict, Any
import telebot.types as telebot_types

class PaymentMenu:
    """Payment Menu Keyboard"""
    
    @staticmethod
    def main_menu() -> telebot_types.InlineKeyboardMarkup:
        """Main payment menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton(
                "💳 Request Plan",
                callback_data="payment:request_plan"
            ),
            telebot_types.InlineKeyboardButton(
                "📋 My Plans",
                callback_data="payment:my_plans"
            ),
            telebot_types.InlineKeyboardButton(
                "⏰ Expiry Status",
                callback_data="payment:expiry_status"
            ),
            telebot_types.InlineKeyboardButton(
                "📊 Payment History",
                callback_data="payment:history"
            ),
            telebot_types.InlineKeyboardButton(
                "🔄 Renew Plan",
                callback_data="payment:renew"
            ),
            telebot_types.InlineKeyboardButton(
                "❌ Cancel Plan",
                callback_data="payment:cancel"
            ),
            telebot_types.InlineKeyboardButton(
                "🆘 Payment Help",
                callback_data="payment:help"
            ),
            telebot_types.InlineKeyboardButton(
                "🔙 Back",
                callback_data="main_menu"
            )
        ]
        
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard
    
    @staticmethod
    def plan_selection(group_id: int = 0) -> telebot_types.InlineKeyboardMarkup:
        """Plan selection menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton(
                "🆓 Free Trial (30 Days)",
                callback_data=f"payment:select:free:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "💰 Basic (30 Days - 60৳)",
                callback_data=f"payment:select:basic:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "💎 Standard (90 Days - 100৳)",
                callback_data=f"payment:select:standard:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "👑 Premium (8 Months - 200৳)",
                callback_data=f"payment:select:premium:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "🔙 Back",
                callback_data="payment:main"
            )
        ]
        
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard
    
    @staticmethod
    def payment_methods(plan_type: str, group_id: int) -> telebot_types.InlineKeyboardMarkup:
        """Payment methods menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton(
                "📱 bKash",
                callback_data=f"payment:method:bkash:{plan_type}:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "📱 Nagad",
                callback_data=f"payment:method:nagad:{plan_type}:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "🏦 Bank Transfer",
                callback_data=f"payment:method:bank:{plan_type}:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "💳 Other",
                callback_data=f"payment:method:other:{plan_type}:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "🔙 Back",
                callback_data=f"payment:select:{group_id}"
            )
        ]
        
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard
    
    @staticmethod
    def payment_confirmation(plan_type: str, method: str, group_id: int) -> telebot_types.InlineKeyboardMarkup:
        """Payment confirmation menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton(
                "✅ Confirm Payment",
                callback_data=f"payment:confirm:{plan_type}:{method}:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"payment:cancel_request:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "🔄 Change Method",
                callback_data=f"payment:change_method:{plan_type}:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "🔙 Back",
                callback_data=f"payment:method:{plan_type}:{group_id}"
            )
        ]
        
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard
    
    @staticmethod
    def admin_approval_menu(request_id: str) -> telebot_types.InlineKeyboardMarkup:
        """Admin approval menu for payments"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton(
                "✅ Approve (30 Days)",
                callback_data=f"admin:approve:basic:{request_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "✅ Approve (90 Days)",
                callback_data=f"admin:approve:standard:{request_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "✅ Approve (8 Months)",
                callback_data=f"admin:approve:premium:{request_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"admin:reject:{request_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "📋 View Details",
                callback_data=f"admin:details:{request_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "👤 Contact User",
                callback_data=f"admin:contact:{request_id}"
            )
        ]
        
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard
    
    @staticmethod
    def plan_management(group_id: int) -> telebot_types.InlineKeyboardMarkup:
        """Plan management menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton(
                "🔄 Renew Plan",
                callback_data=f"plan:renew:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "📊 Upgrade Plan",
                callback_data=f"plan:upgrade:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "📉 Downgrade Plan",
                callback_data=f"plan:downgrade:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "❌ Cancel Plan",
                callback_data=f"plan:cancel:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "⏰ Extend Trial",
                callback_data=f"plan:extend_trial:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "📋 Plan Details",
                callback_data=f"plan:details:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "🔙 Back",
                callback_data="payment:main"
            )
        ]
        
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard
    
    @staticmethod
    def expiry_alerts_menu(group_id: int) -> telebot_types.InlineKeyboardMarkup:
        """Expiry alerts menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton(
                "🔔 Enable Alerts",
                callback_data=f"alert:enable:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "🔕 Disable Alerts",
                callback_data=f"alert:disable:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "⏰ Set Reminder",
                callback_data=f"alert:reminder:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "📋 Alert Settings",
                callback_data=f"alert:settings:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "🔙 Back",
                callback_data="payment:main"
            )
        ]
        
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard