#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Plan Engine
Subscription plan management
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class PlanEngine:
    """Subscription Plan Engine"""
    
    def __init__(self):
        self.config = Config
        self.plans_file = self.config.JSON_PATHS['plans']
        self._initialize_plans()
    
    def _initialize_plans(self):
        """Initialize default plans"""
        if not self.plans_file.exists():
            default_plans = {
                'free': {
                    'name': 'Free Trial',
                    'price': 0,
                    'duration_days': 30,
                    'features': ['basic_auto_reply', 'welcome_message'],
                    'max_groups': 1,
                    'priority': 0,
                },
                'basic': {
                    'name': '30 Days',
                    'price': 60,
                    'duration_days': 30,
                    'features': ['all_auto_reply', 'moderation', 'scheduling'],
                    'max_groups': 3,
                    'priority': 1,
                },
                'standard': {
                    'name': '90 Days',
                    'price': 100,
                    'duration_days': 90,
                    'features': ['all_features', 'priority_support'],
                    'max_groups': 10,
                    'priority': 2,
                },
                'premium': {
                    'name': '8 Months',
                    'price': 200,
                    'duration_days': 240,
                    'features': ['all_features', 'highest_priority', 'customization'],
                    'max_groups': 50,
                    'priority': 3,
                }
            }
            JSONEngine.save_json(self.plans_file, default_plans)