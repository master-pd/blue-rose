#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Group Admin Menu Keyboard
Complete group administration keyboard layouts
"""

from typing import List, Dict, Any
import telebot.types as telebot_types

class GroupAdminMenu:
    """Group Admin Menu Keyboards"""

    @staticmethod
    def main_menu(group_id: int = 0) -> telebot_types.InlineKeyboardMarkup:
        """Main group admin menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            telebot_types.InlineKeyboardButton("🛠️ Service Control", callback_data=f"group_admin:service_control:{group_id}"),
            telebot_types.InlineKeyboardButton("📝 Message Settings", callback_data=f"group_admin:message_settings:{group_id}"),
            telebot_types.InlineKeyboardButton("⏰ Time Settings", callback_data=f"group_admin:time_settings:{group_id}"),
            telebot_types.InlineKeyboardButton("🛡️ Moderation", callback_data=f"group_admin:moderation:{group_id}"),
            telebot_types.InlineKeyboardButton("💳 Payment/Plan", callback_data=f"group_admin:payment:{group_id}"),
            telebot_types.InlineKeyboardButton("📊 Analytics", callback_data=f"group_admin:analytics:{group_id}"),
            telebot_types.InlineKeyboardButton("🔓 Feature Unlock", callback_data=f"group_admin:feature_unlock:{group_id}"),
            telebot_types.InlineKeyboardButton("👋 Welcome/Farewell", callback_data=f"group_admin:welcome_farewell:{group_id}"),
            telebot_types.InlineKeyboardButton("🕌 Prayer Alerts", callback_data=f"group_admin:prayer_alerts:{group_id}"),
            telebot_types.InlineKeyboardButton("📋 Templates", callback_data=f"group_admin:templates:{group_id}"),
            telebot_types.InlineKeyboardButton("😊 Reaction Settings", callback_data=f"group_admin:reactions:{group_id}"),
            telebot_types.InlineKeyboardButton("🤖 Auto-reply Settings", callback_data=f"group_admin:auto_reply:{group_id}"),
            telebot_types.InlineKeyboardButton("📋 Report", callback_data=f"group_admin:report:{group_id}"),
            telebot_types.InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        ]

        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])
        
        return keyboard

    @staticmethod
    def service_control_menu(group_id: int) -> telebot_types.InlineKeyboardMarkup:
        """Service control menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            telebot_types.InlineKeyboardButton("✅ Master Service ON", callback_data=f"service:toggle:master:on:{group_id}"),
            telebot_types.InlineKeyboardButton("❌ Master Service OFF", callback_data=f"service:toggle:master:off:{group_id}"),
            telebot_types.InlineKeyboardButton("🤖 Auto-reply", callback_data=f"service:toggle:auto_reply:{group_id}"),
            telebot_types.InlineKeyboardButton("🛡️ Moderation", callback_data=f"service:toggle:moderation:{group_id}"),
            telebot_types.InlineKeyboardButton("👋 Welcome", callback_data=f"service:toggle:welcome:{group_id}"),
            telebot_types.InlineKeyboardButton("👋 Farewell", callback_data=f"service:toggle:goodbye:{group_id}"),
            telebot_types.InlineKeyboardButton("🕌 Prayer Alerts", callback_data=f"service:toggle:prayer_alerts:{group_id}"),
            telebot_types.InlineKeyboardButton("⏰ Scheduled Messages", callback_data=f"service:toggle:scheduled:{group_id}"),
            telebot_types.InlineKeyboardButton("🌙 Night Mode", callback_data=f"service:toggle:night_mode:{group_id}"),
            telebot_types.InlineKeyboardButton("📊 Analytics", callback_data=f"service:toggle:analytics:{group_id}"),
            telebot_types.InlineKeyboardButton("🔄 Reset All", callback_data=f"service:reset_all:{group_id}"),
            telebot_types.InlineKeyboardButton("📋 Status Report", callback_data=f"service:report:{group_id}"),
            telebot_types.InlineKeyboardButton("🔙 Back", callback_data=f"group_admin:main:{group_id}")
        ]

        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])

        return keyboard

    @staticmethod
    def message_settings_menu(group_id: int) -> telebot_types.InlineKeyboardMarkup:
        """Message settings menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            telebot_types.InlineKeyboardButton("📝 Edit Welcome", callback_data=f"message:edit:welcome:{group_id}"),
            telebot_types.InlineKeyboardButton("📝 Edit Farewell", callback_data=f"message:edit:goodbye:{group_id}"),
            telebot_types.InlineKeyboardButton("📋 Edit Templates", callback_data=f"message:edit:templates:{group_id}"),
            telebot_types.InlineKeyboardButton("🕌 Edit Prayer Messages", callback_data=f"message:edit:prayer:{group_id}"),
            telebot_types.InlineKeyboardButton("⏰ Edit Scheduled", callback_data=f"message:edit:scheduled:{group_id}"),
            telebot_types.InlineKeyboardButton("🔔 Edit Alerts", callback_data=f"message:edit:alerts:{group_id}"),
            telebot_types.InlineKeyboardButton("📖 View Defaults", callback_data=f"message:view_defaults:{group_id}"),
            telebot_types.InlineKeyboardButton("🔄 Reset All", callback_data=f"message:reset_all:{group_id}"),
            telebot_types.InlineKeyboardButton("🔙 Back", callback_data=f"group_admin:main:{group_id}")
        ]

        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])

        return keyboard

    @staticmethod
    def time_settings_menu(group_id: int) -> telebot_types.InlineKeyboardMarkup:
        """Time settings menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            telebot_types.InlineKeyboardButton("⏰ Manage Time Slots", callback_data=f"time:manage_slots:{group_id}"),
            telebot_types.InlineKeyboardButton("🌙 Night Mode", callback_data=f"time:night_mode:{group_id}"),
            telebot_types.InlineKeyboardButton("🕌 Prayer Times", callback_data=f"time:prayer_times:{group_id}"),
            telebot_types.InlineKeyboardButton("📅 Schedule Editor", callback_data=f"time:schedule_editor:{group_id}"),
            telebot_types.InlineKeyboardButton("⏱️ Quiet Hours", callback_data=f"time:quiet_hours:{group_id}"),
            telebot_types.InlineKeyboardButton("🔄 Reset Schedule", callback_data=f"time:reset_schedule:{group_id}"),
            telebot_types.InlineKeyboardButton("📋 Schedule Report", callback_data=f"time:report:{group_id}"),
            telebot_types.InlineKeyboardButton("🔙 Back", callback_data=f"group_admin:main:{group_id}")
        ]

        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])

        return keyboard

    @staticmethod
    def moderation_menu(group_id: int) -> telebot_types.InlineKeyboardMarkup:
        """Moderation menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            telebot_types.InlineKeyboardButton("🛡️ General Settings", callback_data=f"moderation:general:{group_id}"),
            telebot_types.InlineKeyboardButton("🚫 Anti-Spam", callback_data=f"moderation:anti_spam:{group_id}"),
            telebot_types.InlineKeyboardButton("🌊 Anti-Flood", callback_data=f"moderation:anti_flood:{group_id}"),
            telebot_types.InlineKeyboardButton("🔗 Anti-Link", callback_data=f"moderation:anti_link:{group_id}"),
            telebot_types.InlineKeyboardButton("📤 Anti-Forward", callback_data=f"moderation:anti_forward:{group_id}"),
            telebot_types.InlineKeyboardButton("🤖 Anti-Bot", callback_data=f"moderation:anti_bot:{group_id}"),
            telebot_types.InlineKeyboardButton("⚡ Auto Actions", callback_data=f"moderation:auto_actions:{group_id}"),
            telebot_types.InlineKeyboardButton("🛡️ Raid Protection", callback_data=f"moderation:raid_protection:{group_id}"),
            telebot_types.InlineKeyboardButton("📋 Moderation Logs", callback_data=f"moderation:logs:{group_id}"),
            telebot_types.InlineKeyboardButton("🔄 Reset Settings", callback_data=f"moderation:reset:{group_id}"),
            telebot_types.InlineKeyboardButton("📋 Settings Report", callback_data=f"moderation:report:{group_id}"),
            telebot_types.InlineKeyboardButton("🔙 Back", callback_data=f"group_admin:main:{group_id}")
        ]

        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])

        return keyboard

    @staticmethod
    def toggle_menu(group_id: int, item_type: str, item_name: str) -> telebot_types.InlineKeyboardMarkup:
        """Toggle menu for items"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            telebot_types.InlineKeyboardButton("✅ Enable", callback_data=f"toggle:enable:{item_type}:{item_name}:{group_id}"),
            telebot_types.InlineKeyboardButton("❌ Disable", callback_data=f"toggle:disable:{item_type}:{item_name}:{group_id}"),
            telebot_types.InlineKeyboardButton("🔙 Back", callback_data=f"group_admin:{item_type}:{group_id}")
        ]

        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.row(buttons[i], buttons[i + 1])
            else:
                keyboard.row(buttons[i])

        return keyboard

    @staticmethod
    def confirmation_menu(action: str, group_id: int, item: str = "") -> telebot_types.InlineKeyboardMarkup:
        """Confirmation menu"""
        keyboard = telebot_types.InlineKeyboardMarkup(row_width=2)

        if item:
            callback_data = f"confirm:{action}:{item}:{group_id}"
        else:
            callback_data = f"confirm:{action}:{group_id}"

        buttons = [
            telebot_types.InlineKeyboardButton("✅ Yes", callback_data=f"{callback_data}:yes"),
            telebot_types.InlineKeyboardButton("❌ No", callback_data=f"{callback_data}:no")
        ]

        keyboard.row(buttons[0], buttons[1])
        return keyboard
