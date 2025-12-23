"""
Blue Rose Bot - Core Module
Central system components and utilities
"""

__version__ = "1.0.0"
__author__ = "RANA (MASTER)"

from .kernel import Kernel
from .boot import BootManager
from .shutdown import ShutdownManager
from .event_loop import EventLoop
from .dispatcher import Dispatcher
from .permission_engine import PermissionEngine
from .feature_switch import FeatureSwitch
from .rate_limiter import RateLimiter
from .anti_ban_guard import AntiBanGuard

__all__ = [
    'Kernel',
    'BootManager',
    'ShutdownManager',
    'EventLoop',
    'Dispatcher',
    'PermissionEngine',
    'FeatureSwitch',
    'RateLimiter',
    'AntiBanGuard',
]