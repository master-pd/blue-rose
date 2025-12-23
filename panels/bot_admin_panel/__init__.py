"""
Blue Rose Bot - Moderation Module
Message moderation and spam protection
"""

__version__ = "1.0.0"
__author__ = "RANA (MASTER)"

from .anti_spam import AntiSpam
from .anti_flood import AntiFlood
from .anti_link import AntiLink
from .anti_forward import AntiForward
from .anti_bot import AntiBot
from .auto_warn import AutoWarn
from .auto_mute import AutoMute
from .auto_ban import AutoBan

__all__ = [
    'AntiSpam',
    'AntiFlood',
    'AntiLink',
    'AntiForward',
    'AntiBot',
    'AutoWarn',
    'AutoMute',
    'AutoBan',
]