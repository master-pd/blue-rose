"""
Blue Rose Bot - Failsafe Module
Crash recovery and system safety
"""

__version__ = "1.0.0"
__author__ = "RANA (MASTER)"

from .crash_handler import CrashHandler
from .auto_restart import AutoRestart
from .data_integrity import DataIntegrityChecker
from .emergency_lock import EmergencyLock

__all__ = [
    'CrashHandler',
    'AutoRestart',
    'DataIntegrityChecker',
    'EmergencyLock',
]