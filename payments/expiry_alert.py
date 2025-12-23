#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Expiry Alert
Subscription expiry notification system
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class ExpiryAlert:
    """Subscription Expiry Alert System"""
    
    def __init__(self):
        self.config = Config
        self.groups_file = self.config.JSON_PATHS['groups']
        self.expiry_file = self.config.DATA_DIR / "payments" / "expiry_tracker.json"
        self.alerts_file = self.config.DATA_DIR / "payments" / "expiry_alerts.json"
        
        # Alert thresholds (days before expiry)
        self.alert_thresholds = [30, 14, 7, 3, 1, 0]
        
        # Initialize expiry tracker
        self._initialize_tracker()
    
    def _initialize_tracker(self):
        """Initialize expiry tracker"""
        if not self.expiry_file.exists():
            initial_tracker = {
                'tracked_groups': {},
                'last_check': datetime.now().isoformat(),
                'total_alerts_sent': 0,
            }
            JSONEngine.save_json(self.expiry_file, initial_tracker)
    
    async def check_expiries(self):
        """Check all groups for expiring subscriptions"""
        try:
            groups = JSONEngine.load_json(self.groups_file, {})
            tracker = JSONEngine.load_json(self.expiry_file, {})
            
            expiring_groups = []
            expired_groups = []
            
            current_time = datetime.now()
            
            for chat_id_str, group_data in groups.items():
                if not group_data.get('plan_active', False):
                    continue
                
                expiry_date_str = group_data.get('expiry_date')
                if not expiry_date_str:
                    continue
                
                try:
                    expiry_date = datetime.fromisoformat(expiry_date_str)
                    
                    # Check if expired
                    if current_time > expiry_date:
                        expired_groups.append({
                            'chat_id': int(chat_id_str),
                            'group_data': group_data,
                            'expired_at': expiry_date.isoformat(),
                            'days_expired': (current_time - expiry_date).days,
                        })
                        continue
                    
                    # Check days until expiry
                    days_until = (expiry_date - current_time).days
                    
                    if days_until in self.alert_thresholds:
                        expiring_groups.append({
                            'chat_id': int(chat_id_str),
                            'group_data': group_data,
                            'expiry_date': expiry_date.isoformat(),
                            'days_until': days_until,
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to parse expiry date for group {chat_id_str}: {e}")
            
            # Send alerts
            alerts_sent = 0
            for group in expiring_groups:
                sent = await self._send_expiry_alert(group)
                if sent:
                    alerts_sent += 1
            
            # Handle expired groups
            expired_handled = 0
            for group in expired_groups:
                handled = await self._handle_expired_group(group)
                if handled:
                    expired_handled += 1
            
            # Update tracker
            tracker['last_check'] = current_time.isoformat()
            tracker['last_check_results'] = {
                'total_groups_checked': len(groups),
                'expiring_groups': len(expiring_groups),
                'expired_groups': len(expired_groups),
                'alerts_sent': alerts_sent,
                'expired_handled': expired_handled,
            }
            tracker['total_alerts_sent'] = tracker.get('total_alerts_sent', 0) + alerts_sent
            
            JSONEngine.save_json(self.expiry_file, tracker)
            
            logger.info(f"Expiry check: {len(expiring_groups)} expiring, "
                       f"{len(expired_groups)} expired, {alerts_sent} alerts sent")
            
            return {
                'checked_at': current_time.isoformat(),
                'expiring_groups': expiring_groups,
                'expired_groups': expired_groups,
                'alerts_sent': alerts_sent,
                'expired_handled': expired_handled,
            }
            
        except Exception as e:
            logger.error(f"Failed to check expiries: {e}")
            return {'error': str(e)}
    
    async def _send_expiry_alert(self, group_info: Dict[str, Any]) -> bool:
        """Send expiry alert to group"""
        try:
            chat_id = group_info['chat_id']
            days_until = group_info['days_until']
            group_data = group_info['group_data']
            expiry_date = group_info['expiry_date']
            
            # Create alert message
            if days_until > 0:
                message = f"""
🔔 <b>Subscription Expiry Alert</b>

Your {group_data.get('plan', 'Unknown')} plan will expire in <b>{days_until} day(s)</b>.

Expiry Date: {expiry_date.split('T')[0]}

Please renew your subscription to continue enjoying all features.

Contact admin for renewal: {self.config.DEVELOPER_CONTACT}
                """.strip()
            else:
                message = f"""
⚠️ <b>Subscription Expired Today!</b>

Your {group_data.get('plan', 'Unknown')} plan has expired today.

Some features may be disabled. Please renew immediately to restore full functionality.

Contact admin for renewal: {self.config.DEVELOPER_CONTACT}
                """.strip()
            
            # In a real implementation, this would send a Telegram message
            # For now, just log it
            logger.info(f"Expiry alert for group {chat_id}: {days_until} days until expiry")
            
            # Log the alert
            await self._log_alert(chat_id, days_until, message)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send expiry alert: {e}")
            return False
    
    async def _handle_expired_group(self, group_info: Dict[str, Any]) -> bool:
        """Handle expired group subscription"""
        try:
            chat_id = group_info['chat_id']
            group_data = group_info['group_data']
            
            # Update group status
            groups = JSONEngine.load_json(self.groups_file, {})
            group_key = str(chat_id)
            
            if group_key in groups:
                groups[group_key]['plan_active'] = False
                groups[group_key]['expired_at'] = datetime.now().isoformat()
                
                JSONEngine.save_json(self.groups_file, groups)
            
            # Disable paid features
            from payments.cancel_service import CancelService
            cancel_service = CancelService()
            
            await cancel_service.cancel_group_plan(
                chat_id,
                cancelled_by=self.config.BOT_OWNER_ID,
                reason="Subscription expired"
            )
            
            logger.info(f"Handled expired subscription for group {chat_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle expired group: {e}")
            return False
    
    async def _log_alert(self, chat_id: int, days_until: int, message: str):
        """Log sent alert"""
        try:
            alerts = JSONEngine.load_json(self.alerts_file, [])
            
            alert_entry = {
                'chat_id': chat_id,
                'days_until': days_until,
                'message': message,
                'sent_at': datetime.now().isoformat(),
                'alert_type': 'expiry',
            }
            
            alerts.append(alert_entry)
            
            # Keep only last 1000 alerts
            if len(alerts) > 1000:
                alerts = alerts[-1000:]
            
            JSONEngine.save_json(self.alerts_file, alerts)
            
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")
    
    async def schedule_expiry_checks(self, interval_hours: int = 6):
        """Schedule regular expiry checks"""
        logger.info(f"Scheduled expiry checks every {interval_hours} hours")
        
        async def check_task():
            while True:
                try:
                    await asyncio.sleep(interval_hours * 3600)
                    await self.check_expiries()
                except Exception as e:
                    logger.error(f"Scheduled expiry check failed: {e}")
                    await asyncio.sleep(3600)  # Wait an hour before retry
        
        # Start the task
        asyncio.create_task(check_task())
        
        return True
    
    async def get_expiry_stats(self) -> Dict[str, Any]:
        """Get expiry alert statistics"""
        try:
            tracker = JSONEngine.load_json(self.expiry_file, {})
            alerts = JSONEngine.load_json(self.alerts_file, [])
            
            # Count groups by status
            groups = JSONEngine.load_json(self.groups_file, {})
            
            active_groups = 0
            expiring_soon = 0
            expired_groups = 0
            
            current_time = datetime.now()
            
            for group_data in groups.values():
                if not group_data.get('plan_active', False):
                    continue
                
                active_groups += 1
                
                expiry_date_str = group_data.get('expiry_date')
                if expiry_date_str:
                    try:
                        expiry_date = datetime.fromisoformat(expiry_date_str)
                        days_until = (expiry_date - current_time).days
                        
                        if days_until <= 7:
                            expiring_soon += 1
                        
                        if current_time > expiry_date:
                            expired_groups += 1
                    except:
                        pass
            
            return {
                'total_alerts_sent': tracker.get('total_alerts_sent', 0),
                'last_check': tracker.get('last_check'),
                'total_alerts_logged': len(alerts),
                'active_groups': active_groups,
                'expiring_soon': expiring_soon,
                'expired_groups': expired_groups,
                'alert_thresholds': self.alert_thresholds,
            }
            
        except Exception as e:
            logger.error(f"Failed to get expiry stats: {e}")
            return {'error': str(e)}