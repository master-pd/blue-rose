#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Confirmation Keyboards
Confirmation dialogs for various actions
"""

import telebot.types as telebot_types

class ConfirmationKeyboard:
    """Confirmation Keyboards"""
    
    @staticmethod
    def yes_no(action: str, data: str = "") -> telebot_types.InlineKeyboardMarkup:
        """Simple Yes/No confirmation"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        if data:
            callback_yes = f"confirm:{action}:{data}:yes"
            callback_no = f"confirm:{action}:{data}:no"
        else:
            callback_yes = f"confirm:{action}:yes"
            callback_no = f"confirm:{action}:no"
        
        buttons = [
            telebot_types.InlineKeyboardButton("✅ Yes", callback_data=callback_yes),
            telebot_types.InlineKeyboardButton("❌ No", callback_data=callback_no)
        ]
        
        keyboard.row(buttons[0], buttons[1])
        return keyboard
    
    @staticmethod
    def confirm_cancel(action: str, data: str = "") -> telebot_types.InlineKeyboardMarkup:
        """Confirm/Cancel confirmation"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        if data:
            callback_confirm = f"confirm:{action}:{data}"
            callback_cancel = f"cancel:{action}:{data}"
        else:
            callback_confirm = f"confirm:{action}"
            callback_cancel = f"cancel:{action}"
        
        buttons = [
            telebot_types.InlineKeyboardButton("✅ Confirm", callback_data=callback_confirm),
            telebot_types.InlineKeyboardButton("❌ Cancel", callback_data=callback_cancel)
        ]
        
        keyboard.row(buttons[0], buttons[1])
        return keyboard
    
    @staticmethod
    def proceed_back(action: str, data: str = "") -> telebot_types.InlineKeyboardMarkup:
        """Proceed/Back confirmation"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        if data:
            callback_proceed = f"proceed:{action}:{data}"
            callback_back = f"back:{action}:{data}"
        else:
            callback_proceed = f"proceed:{action}"
            callback_back = f"back:{action}"
        
        buttons = [
            telebot_types.InlineKeyboardButton("➡️ Proceed", callback_data=callback_proceed),
            telebot_types.InlineKeyboardButton("🔙 Back", callback_data=callback_back)
        ]
        
        keyboard.row(buttons[0], buttons[1])
        return keyboard
    
    @staticmethod
    def enable_disable(item_type: str, item_id: str) -> telebot_types.InlineKeyboardMarkup:
        """Enable/Disable toggle"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton(
                "✅ Enable",
                callback_data=f"toggle:enable:{item_type}:{item_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "❌ Disable",
                callback_data=f"toggle:disable:{item_type}:{item_id}"
            )
        ]
        
        keyboard.row(buttons[0], buttons[1])
        return keyboard
    
    @staticmethod
    def approve_reject(request_id: str) -> telebot_types.InlineKeyboardMarkup:
        """Approve/Reject confirmation"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=3)
        
        buttons = [
            telebot_types.InlineKeyboardButton("✅ Approve", callback_data=f"approve:{request_id}"),
            telebot_types.InlineKeyboardButton("❌ Reject", callback_data=f"reject:{request_id}"),
            telebot_types.InlineKeyboardButton("📋 View", callback_data=f"view:{request_id}")
        ]
        
        keyboard.row(buttons[0], buttons[1], buttons[2])
        return keyboard
    
    @staticmethod
    def save_discard(action: str, data: str = "") -> telebot_types.InlineKeyboardMarkup:
        """Save/Discard changes"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        if data:
            callback_save = f"save:{action}:{data}"
            callback_discard = f"discard:{action}:{data}"
        else:
            callback_save = f"save:{action}"
            callback_discard = f"discard:{action}"
        
        buttons = [
            telebot_types.InlineKeyboardButton("💾 Save", callback_data=callback_save),
            telebot_types.InlineKeyboardButton("🗑️ Discard", callback_data=callback_discard)
        ]
        
        keyboard.row(buttons[0], buttons[1])
        return keyboard
    
    @staticmethod
    def delete_keep(item_type: str, item_id: str) -> telebot_types.InlineKeyboardMarkup:
        """Delete/Keep confirmation"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{item_type}:{item_id}"),
            telebot_types.InlineKeyboardButton("💾 Keep", callback_data=f"keep:{item_type}:{item_id}")
        ]
        
        keyboard.row(buttons[0], buttons[1])
        return keyboard
    
    @staticmethod
    def restart_shutdown() -> telebot_types.InlineKeyboardMarkup:
        """Restart/Shutdown confirmation"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton("🔄 Restart", callback_data="system:restart"),
            telebot_types.InlineKeyboardButton("🔴 Shutdown", callback_data="system:shutdown"),
            telebot_types.InlineKeyboardButton("❌ Cancel", callback_data="system:cancel")
        ]
        
        keyboard.row(buttons[0], buttons[1])
        keyboard.row(buttons[2])
        return keyboard
    
    @staticmethod
    def emergency_actions() -> telebot_types.InlineKeyboardMarkup:
        """Emergency actions confirmation"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton("🚨 Lockdown", callback_data="emergency:lockdown"),
            telebot_types.InlineKeyboardButton("🔓 Release", callback_data="emergency:release"),
            telebot_types.InlineKeyboardButton("📴 Silent Mode", callback_data="emergency:silent"),
            telebot_types.InlineKeyboardButton("❌ Cancel", callback_data="emergency:cancel")
        ]
        
        keyboard.row(buttons[0], buttons[1])
        keyboard.row(buttons[2], buttons[3])
        return keyboard
    
    @staticmethod
    def plan_selection_confirmation(plan_type: str, group_id: int) -> telebot_types.InlineKeyboardMarkup:
        """Plan selection confirmation"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        plan_names = {
            'free': 'Free Trial (30 Days)',
            'basic': 'Basic (30 Days - 60৳)',
            'standard': 'Standard (90 Days - 100৳)',
            'premium': 'Premium (8 Months - 200৳)'
        }
        
        plan_name = plan_names.get(plan_type, plan_type)
        
        buttons = [
            telebot_types.InlineKeyboardButton(
                f"✅ Select {plan_name}",
                callback_data=f"plan:select:{plan_type}:{group_id}:confirm"
            ),
            telebot_types.InlineKeyboardButton(
                "🔄 Change Plan",
                callback_data=f"plan:change:{group_id}"
            ),
            telebot_types.InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"plan:cancel:{group_id}"
            )
        ]
        
        keyboard.row(buttons[0])
        keyboard.row(buttons[1], buttons[2])
        return keyboard