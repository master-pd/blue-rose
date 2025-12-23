"""
Blue Rose Bot - Panels Module
User interface panels and menus
"""

__version__ = "1.0.0"
__author__ = "RANA (MASTER)"

from .start_panel import StartPanel
from .help_panel import HelpPanel
from .support_panel import SupportPanel
from .add_group_panel import AddGroupPanel

# Bot Admin Panels
from .bot_admin_panel.dashboard import BotAdminDashboard
from .bot_admin_panel.group_list import GroupListPanel
from .bot_admin_panel.force_join import ForceJoinPanel
from .bot_admin_panel.force_leave import ForceLeavePanel
from .bot_admin_panel.payment_control import PaymentControlPanel
from .bot_admin_panel.feature_override import FeatureOverridePanel

# Group Admin Panels
from .group_admin_panel.dashboard import GroupAdminDashboard
from .group_admin_panel.service_toggle import ServiceTogglePanel
from .group_admin_panel.time_slot_editor import TimeSlotEditor
from .group_admin_panel.message_editor import MessageEditor
from .group_admin_panel.moderation_settings import ModerationSettingsPanel

__all__ = [
    'StartPanel',
    'HelpPanel',
    'SupportPanel',
    'AddGroupPanel',
    'BotAdminDashboard',
    'GroupListPanel',
    'ForceJoinPanel',
    'ForceLeavePanel',
    'PaymentControlPanel',
    'FeatureOverridePanel',
    'GroupAdminDashboard',
    'ServiceTogglePanel',
    'TimeSlotEditor',
    'MessageEditor',
    'ModerationSettingsPanel',
]