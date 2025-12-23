"""
Blue Rose Bot - Storage Module
Data storage and persistence
"""

__version__ = "1.0.0"
__author__ = "RANA (MASTER)"

from .json_engine import JSONEngine
from .file_lock import FileLock
from .backup import BackupManager
from .restore import RestoreManager

__all__ = [
    'JSONEngine',
    'FileLock',
    'BackupManager',
    'RestoreManager',
]