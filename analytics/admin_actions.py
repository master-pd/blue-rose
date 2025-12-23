#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Admin Actions Analytics
Track and analyze admin actions
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class AdminActionsAnalytics:
    """Admin Actions Analytics"""
    
    def __init__(self):
        self.config = Config
        self.analytics_file = self.config.DATA_DIR / "analytics" / "admin_actions.json"
        self.analytics_file.parent.mkdir(exist_ok=True)
        
        # Initialize analytics file if not exists
        self._initialize_analytics()
    
    def _initialize_analytics(self):
        """Initialize analytics file"""
        if not self.analytics_file.exists():
            default_analytics = {
                'metadata': {
                    'description': 'Admin actions analytics',
                    'version': '1.0.0',
                    'created': datetime.now().isoformat(),
                    'updated': datetime.now().isoformat()
                },
                'actions': [],
                'daily_stats': {},
                'admin_stats': {},
                'group_stats': {},
                'action_types': {}
            }
            JSONEngine.save_json(self.analytics_file, default_analytics)
    
    async def log_action(self, action_type: str, 
                       admin_id: int,
                       group_id: Optional[int] = None,
                       target_id: Optional[int] = None,
                       details: Optional[Dict] = None,
                       result: str = "success") -> bool:
        """Log an admin action"""
        try:
            analytics = JSONEngine.load_json(self.analytics_file, {})
            
            action_entry = {
                'id': self._generate_id(),
                'action_type': action_type,
                'admin_id': admin_id,
                'group_id': group_id,
                'target_id': target_id,
                'details': details or {},
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'hour': datetime.now().hour
            }
            
            # Add to actions list
            if 'actions' not in analytics:
                analytics['actions'] = []
            analytics['actions'].append(action_entry)
            
            # Update daily stats
            await self._update_daily_stats(analytics, action_entry)
            
            # Update admin stats
            await self._update_admin_stats(analytics, action_entry)
            
            # Update group stats
            if group_id:
                await self._update_group_stats(analytics, action_entry)
            
            # Update action type stats
            await self._update_action_type_stats(analytics, action_entry)
            
            # Save analytics
            analytics['metadata']['updated'] = datetime.now().isoformat()
            JSONEngine.save_json(self.analytics_file, analytics)
            
            logger.debug(f"Logged admin action: {action_type} by {admin_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
            return False
    
    async def _update_daily_stats(self, analytics: Dict, action: Dict):
        """Update daily statistics"""
        date = action['date']
        
        if 'daily_stats' not in analytics:
            analytics['daily_stats'] = {}
        
        if date not in analytics['daily_stats']:
            analytics['daily_stats'][date] = {
                'total_actions': 0,
                'successful_actions': 0,
                'failed_actions': 0,
                'action_types': {},
                'admins': {}
            }
        
        daily = analytics['daily_stats'][date]
        daily['total_actions'] += 1
        
        if action['result'] == 'success':
            daily['successful_actions'] += 1
        else:
            daily['failed_actions'] += 1
        
        # Update action types for the day
        action_type = action['action_type']
        if action_type not in daily['action_types']:
            daily['action_types'][action_type] = 0
        daily['action_types'][action_type] += 1
        
        # Update admin stats for the day
        admin_id = str(action['admin_id'])
        if admin_id not in daily['admins']:
            daily['admins'][admin_id] = 0
        daily['admins'][admin_id] += 1
    
    async def _update_admin_stats(self, analytics: Dict, action: Dict):
        """Update admin statistics"""
        admin_id = str(action['admin_id'])
        
        if 'admin_stats' not in analytics:
            analytics['admin_stats'] = {}
        
        if admin_id not in analytics['admin_stats']:
            analytics['admin_stats'][admin_id] = {
                'total_actions': 0,
                'successful_actions': 0,
                'failed_actions': 0,
                'action_types': {},
                'groups': {},
                'first_action': action['timestamp'],
                'last_action': action['timestamp']
            }
        
        admin = analytics['admin_stats'][admin_id]
        admin['total_actions'] += 1
        admin['last_action'] = action['timestamp']
        
        if action['result'] == 'success':
            admin['successful_actions'] += 1
        else:
            admin['failed_actions'] += 1
        
        # Update action types for admin
        action_type = action['action_type']
        if action_type not in admin['action_types']:
            admin['action_types'][action_type] = 0
        admin['action_types'][action_type] += 1
        
        # Update group stats for admin
        if action['group_id']:
            group_id = str(action['group_id'])
            if group_id not in admin['groups']:
                admin['groups'][group_id] = 0
            admin['groups'][group_id] += 1
    
    async def _update_group_stats(self, analytics: Dict, action: Dict):
        """Update group statistics"""
        group_id = str(action['group_id'])
        
        if 'group_stats' not in analytics:
            analytics['group_stats'] = {}
        
        if group_id not in analytics['group_stats']:
            analytics['group_stats'][group_id] = {
                'total_actions': 0,
                'successful_actions': 0,
                'failed_actions': 0,
                'action_types': {},
                'admins': {},
                'first_action': action['timestamp'],
                'last_action': action['timestamp']
            }
        
        group = analytics['group_stats'][group_id]
        group['total_actions'] += 1
        group['last_action'] = action['timestamp']
        
        if action['result'] == 'success':
            group['successful_actions'] += 1
        else:
            group['failed_actions'] += 1
        
        # Update action types for group
        action_type = action['action_type']
        if action_type not in group['action_types']:
            group['action_types'][action_type] = 0
        group['action_types'][action_type] += 1
        
        # Update admin stats for group
        admin_id = str(action['admin_id'])
        if admin_id not in group['admins']:
            group['admins'][admin_id] = 0
        group['admins'][admin_id] += 1
    
    async def _update_action_type_stats(self, analytics: Dict, action: Dict):
        """Update action type statistics"""
        action_type = action['action_type']
        
        if 'action_types' not in analytics:
            analytics['action_types'] = {}
        
        if action_type not in analytics['action_types']:
            analytics['action_types'][action_type] = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'admins': {},
                'groups': {},
                'first_action': action['timestamp'],
                'last_action': action['timestamp']
            }
        
        action_type_stats = analytics['action_types'][action_type]
        action_type_stats['total'] += 1
        action_type_stats['last_action'] = action['timestamp']
        
        if action['result'] == 'success':
            action_type_stats['successful'] += 1
        else:
            action_type_stats['failed'] += 1
        
        # Update admin stats for action type
        admin_id = str(action['admin_id'])
        if admin_id not in action_type_stats['admins']:
            action_type_stats['admins'][admin_id] = 0
        action_type_stats['admins'][admin_id] += 1
        
        # Update group stats for action type
        if action['group_id']:
            group_id = str(action['group_id'])
            if group_id not in action_type_stats['groups']:
                action_type_stats['groups'][group_id] = 0
            action_type_stats['groups'][group_id] += 1
    
    def _generate_id(self) -> str:
        """Generate unique ID for action"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    async def get_admin_stats(self, admin_id: int, 
                            days: int = 7) -> Dict[str, Any]:
        """Get statistics for a specific admin"""
        try:
            analytics = JSONEngine.load_json(self.analytics_file, {})
            admin_key = str(admin_id)
            
            if admin_key not in analytics.get('admin_stats', {}):
                return {
                    'admin_id': admin_id,
                    'exists': False,
                    'message': 'No actions found for this admin'
                }
            
            admin_stats = analytics['admin_stats'][admin_key]
            
            # Filter recent actions
            recent_actions = []
            cutoff_date = (datetime.now() - timedelta(days=days)).date()
            
            for action in analytics.get('actions', []):
                if (str(action.get('admin_id')) == admin_key and 
                    datetime.fromisoformat(action['timestamp']).date() >= cutoff_date):
                    recent_actions.append(action)
            
            # Calculate daily activity
            daily_activity = {}
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_activity[date] = 0
            
            for action in recent_actions:
                date = action['date']
                if date in daily_activity:
                    daily_activity[date] += 1
            
            return {
                'admin_id': admin_id,
                'exists': True,
                'total_actions': admin_stats['total_actions'],
                'successful_actions': admin_stats.get('successful_actions', 0),
                'failed_actions': admin_stats.get('failed_actions', 0),
                'success_rate': (
                    (admin_stats.get('successful_actions', 0) / admin_stats['total_actions'] * 100)
                    if admin_stats['total_actions'] > 0 else 0
                ),
                'first_action': admin_stats.get('first_action', ''),
                'last_action': admin_stats.get('last_action', ''),
                'action_types': admin_stats.get('action_types', {}),
                'groups': admin_stats.get('groups', {}),
                'recent_actions_count': len(recent_actions),
                'daily_activity': daily_activity,
                'most_common_action': max(
                    admin_stats.get('action_types', {}).items(),
                    key=lambda x: x[1],
                    default=('None', 0)
                )[0],
                'most_active_group': max(
                    admin_stats.get('groups', {}).items(),
                    key=lambda x: x[1],
                    default=('None', 0)
                )[0]
            }
        
        except Exception as e:
            logger.error(f"Failed to get admin stats: {e}")
            return {'error': str(e)}
    
    async def get_group_stats(self, group_id: int, 
                            days: int = 7) -> Dict[str, Any]:
        """Get statistics for a specific group"""
        try:
            analytics = JSONEngine.load_json(self.analytics_file, {})
            group_key = str(group_id)
            
            if group_key not in analytics.get('group_stats', {}):
                return {
                    'group_id': group_id,
                    'exists': False,
                    'message': 'No actions found for this group'
                }
            
            group_stats = analytics['group_stats'][group_key]
            
            # Filter recent actions
            recent_actions = []
            cutoff_date = (datetime.now() - timedelta(days=days)).date()
            
            for action in analytics.get('actions', []):
                if (str(action.get('group_id')) == group_key and 
                    datetime.fromisoformat(action['timestamp']).date() >= cutoff_date):
                    recent_actions.append(action)
            
            return {
                'group_id': group_id,
                'exists': True,
                'total_actions': group_stats['total_actions'],
                'successful_actions': group_stats.get('successful_actions', 0),
                'failed_actions': group_stats.get('failed_actions', 0),
                'success_rate': (
                    (group_stats.get('successful_actions', 0) / group_stats['total_actions'] * 100)
                    if group_stats['total_actions'] > 0 else 0
                ),
                'first_action': group_stats.get('first_action', ''),
                'last_action': group_stats.get('last_action', ''),
                'action_types': group_stats.get('action_types', {}),
                'admins': group_stats.get('admins', {}),
                'recent_actions_count': len(recent_actions),
                'most_common_action': max(
                    group_stats.get('action_types', {}).items(),
                    key=lambda x: x[1],
                    default=('None', 0)
                )[0],
                'most_active_admin': max(
                    group_stats.get('admins', {}).items(),
                    key=lambda x: x[1],
                    default=('None', 0)
                )[0],
                'recent_actions': recent_actions[-10:]  # Last 10 actions
            }
        
        except Exception as e:
            logger.error(f"Failed to get group stats: {e}")
            return {'error': str(e)}
    
    async def get_system_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get overall system statistics"""
        try:
            analytics = JSONEngine.load_json(self.analytics_file, {})
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)
            
            # Initialize results
            total_actions = 0
            successful_actions = 0
            failed_actions = 0
            active_admins = set()
            active_groups = set()
            action_type_counts = {}
            daily_counts = {}
            
            # Initialize daily counts
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                daily_counts[date_str] = 0
                current_date += timedelta(days=1)
            
            # Process actions
            for action in analytics.get('actions', []):
                action_date = datetime.fromisoformat(action['timestamp']).date()
                
                # Only count actions within date range
                if start_date <= action_date <= end_date:
                    total_actions += 1
                    
                    if action['result'] == 'success':
                        successful_actions += 1
                    else:
                        failed_actions += 1
                    
                    # Track active admins and groups
                    active_admins.add(str(action['admin_id']))
                    if action.get('group_id'):
                        active_groups.add(str(action['group_id']))
                    
                    # Count action types
                    action_type = action['action_type']
                    if action_type not in action_type_counts:
                        action_type_counts[action_type] = 0
                    action_type_counts[action_type] += 1
                    
                    # Count daily actions
                    date_str = action_date.strftime('%Y-%m-%d')
                    if date_str in daily_counts:
                        daily_counts[date_str] += 1
            
            # Calculate averages
            avg_daily_actions = total_actions / days if days > 0 else 0
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'totals': {
                    'actions': total_actions,
                    'successful': successful_actions,
                    'failed': failed_actions,
                    'success_rate': (
                        (successful_actions / total_actions * 100) 
                        if total_actions > 0 else 0
                    )
                },
                'activity': {
                    'active_admins': len(active_admins),
                    'active_groups': len(active_groups),
                    'avg_daily_actions': avg_daily_actions,
                    'daily_counts': daily_counts
                },
                'action_types': action_type_counts,
                'top_admins': sorted(
                    analytics.get('admin_stats', {}).items(),
                    key=lambda x: x[1].get('total_actions', 0),
                    reverse=True
                )[:5],
                'top_groups': sorted(
                    analytics.get('group_stats', {}).items(),
                    key=lambda x: x[1].get('total_actions', 0),
                    reverse=True
                )[:5]
            }
        
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {'error': str(e)}
    
    async def export_analytics(self, format_type: str = 'json') -> Dict[str, Any]:
        """Export analytics data"""
        try:
            analytics = JSONEngine.load_json(self.analytics_file, {})
            
            if format_type == 'json':
                return analytics
            elif format_type == 'summary':
                return await self.get_system_stats(days=30)
            else:
                return {'error': f'Unsupported format: {format_type}'}
        
        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Cleanup old analytics data"""
        try:
            analytics = JSONEngine.load_json(self.analytics_file, {})
            
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date()
            cutoff_timestamp = datetime.combine(cutoff_date, datetime.min.time()).isoformat()
            
            # Filter actions
            if 'actions' in analytics:
                original_count = len(analytics['actions'])
                analytics['actions'] = [
                    action for action in analytics['actions']
                    if datetime.fromisoformat(action['timestamp']).date() >= cutoff_date
                ]
                removed_count = original_count - len(analytics['actions'])
                
                # Recalculate stats based on remaining actions
                await self._recalculate_stats(analytics)
                
                # Save cleaned analytics
                analytics['metadata']['updated'] = datetime.now().isoformat()
                JSONEngine.save_json(self.analytics_file, analytics)
                
                logger.info(f"Cleaned up {removed_count} old action records")
                return removed_count
            
            return 0
        
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    async def _recalculate_stats(self, analytics: Dict):
        """Recalculate statistics from actions"""
        # Clear all stats
        analytics['daily_stats'] = {}
        analytics['admin_stats'] = {}
        analytics['group_stats'] = {}
        analytics['action_types'] = {}
        
        # Recalculate from remaining actions
        for action in analytics.get('actions', []):
            await self._update_daily_stats(analytics, action)
            await self._update_admin_stats(analytics, action)
            if action.get('group_id'):
                await self._update_group_stats(analytics, action)
            await self._update_action_type_stats(analytics, action)