"""
Blue Rose Bot - Supremacy Module
Bot supremacy and competition management
"""

__version__ = "1.0.0"
__author__ = "RANA (MASTER)"

from .bot_detector import BotDetector
from .bot_capability_scan import BotCapabilityScan
from .rival_kicker import RivalKicker

__all__ = [
    'BotDetector',
    'BotCapabilityScan',
    'RivalKicker',
]