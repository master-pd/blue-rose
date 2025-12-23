"""
Blue Rose Bot - Keyboards Module
Inline and reply keyboards for user interfaces
"""

__version__ = "1.0.0"
__author__ = "RANA (MASTER)"

from .start import StartKeyboard
from .main_menu import MainMenuKeyboard
from .admin_menu import AdminMenuKeyboard
from .group_admin_menu import GroupAdminMenuKeyboard
from .payment_menu import PaymentMenuKeyboard
from .confirmation import ConfirmationKeyboard

__all__ = [
    'StartKeyboard',
    'MainMenuKeyboard',
    'AdminMenuKeyboard',
    'GroupAdminMenuKeyboard',
    'PaymentMenuKeyboard',
    'ConfirmationKeyboard',
]