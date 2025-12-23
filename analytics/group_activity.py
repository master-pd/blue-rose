#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Group Activity Analytics
Group activity tracking and analysis
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class GroupActivityAnalytics:
    """Group Activity Analytics System"""
    
    def __init__(self):
        self.config = Config
        self.activity_file = self.config.DATA_DIR / "analytics" / "group_activity.json"
        self.activity_file.parent.mkdir(exist_ok=True)
        
    async def record_activity(self, chat_id: int, activity_type: str,
                            user_id: Optional[int] = None,
                            details: Dict[str, Any] = None):
        """Record group activity"""
        try:
            activities = JSONEngine.load_json(self.activity_file, [])
            
            activity = {
                'chat_id': chat_id,
                'activity_type': activity_type,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'details': details or {},
            }
            
            activities.append(activity)
            
            # Keep only last 5000 activities
            if len(activities) > 5000:
                activities = activities[-5000:]
            
            JSONEngine.save_json(self.activity_file, activities)
            
        except Exception as e:
            logger.error(f"Failed to record activity: {e}")
    
    async def get_group_stats(self, chat_id: int, days: int = 7) -> Dict[str, Any]:
        """Get group activity statistics"""
        try:
            activities = JSONEngine.load_json(self.activity_file, [])
            
            # Filter by chat and date
            cutoff_date = datetime.now() - timedelta(days=days)
            group_activities = [
                a for a in activities
                if a.get('chat_id') == chat_id and
                datetime.fromisoformat(a.get('timestamp')) > cutoff_date
            ]
            
            if not group_activities:
                return {
                    'chat_id': chat_id,
                    'period_days': days,
                    'total_activities': 0,
                    'message': 'No activity recorded in this period',
                }
            
            # Count by activity type
            activity_counts = {}
            for activity in group_activities:
                activity_type = activity.get('activity_type', 'unknown')
                activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
            
            # Get top users
            user_counts = {}
            for activity in group_activities:
                user_id = activity.get('user_id')
                if user_id:
                    user_counts[user_id] = user_counts.get(user_id, 0) + 1
            
            top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Daily activity
            daily_activity = {}
            for activity in group_activities:
                date = activity['timestamp'][:10]  # YYYY-MM-DD
                daily_activity[date] = daily_activity.get(date, 0) + 1
            
            return {
                'chat_id': chat_id,
                'period_days': days,
                'total_activities': len(group_activities),
                'activity_counts': activity_counts,
                'top_users': top_users,
                'daily_activity': daily_activity,
                'first_activity': group_activities[0]['timestamp'],
                'last_activity': group_activities[-1]['timestamp'],
            }
            
        except Exception as e:
            logger.error(f"Failed to get group stats: {e}")
            return {'error': str(e)}
