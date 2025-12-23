#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - System Health Analytics
Monitor and analyze system health metrics
"""

import asyncio
import logging
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """System Health Monitor"""
    
    def __init__(self):
        self.config = Config
        self.health_file = self.config.DATA_DIR / "analytics" / "system_health.json"
        self.health_file.parent.mkdir(exist_ok=True)
        
        # Initialize health file if not exists
        self._initialize_health_file()
        
        # Monitoring settings
        self.monitoring_enabled = True
        self.check_interval = 300  # 5 minutes
        self.retention_days = 7
    
    def _initialize_health_file(self):
        """Initialize system health file"""
        if not self.health_file.exists():
            default_health = {
                'metadata': {
                    'description': 'System health monitoring data',
                    'version': '1.0.0',
                    'created': datetime.now().isoformat(),
                    'updated': datetime.now().isoformat()
                },
                'health_checks': [],
                'daily_stats': {},
                'alerts': [],
                'system_info': self._get_system_info()
            }
            JSONEngine.save_json(self.health_file, default_health)
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            import platform
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'cpu_count': psutil.cpu_count(),
                'total_ram': psutil.virtual_memory().total,
                'total_disk': psutil.disk_usage('/').total
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check"""
        try:
            check_time = datetime.now()
            
            # Collect metrics
            metrics = {
                'timestamp': check_time.isoformat(),
                'date': check_time.strftime('%Y-%m-%d'),
                'hour': check_time.hour,
                'cpu': await self._get_cpu_metrics(),
                'memory': await self._get_memory_metrics(),
                'disk': await self._get_disk_metrics(),
                'network': await self._get_network_metrics(),
                'bot': await self._get_bot_metrics(),
                'system': await self._get_system_metrics(),
                'status': 'healthy',
                'alerts': []
            }
            
            # Check for issues
            alerts = await self._check_for_alerts(metrics)
            metrics['alerts'] = alerts
            
            if alerts:
                metrics['status'] = 'warning' if len(alerts) < 3 else 'critical'
            
            # Log the health check
            await self._log_health_check(metrics)
            
            # Update daily stats
            await self._update_daily_stats(metrics)
            
            # Send alerts if needed
            if alerts:
                await self._send_alerts(alerts, metrics)
            
            return metrics
        
        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")
            return {'error': str(e), 'status': 'error'}
    
    async def _get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_times = psutil.cpu_times_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            
            return {
                'percent': cpu_percent,
                'user': getattr(cpu_times, 'user', 0),
                'system': getattr(cpu_times, 'system', 0),
                'idle': getattr(cpu_times, 'idle', 0),
                'frequency_current': getattr(cpu_freq, 'current', 0) if cpu_freq else 0,
                'frequency_max': getattr(cpu_freq, 'max', 0) if cpu_freq else 0,
                'cores': psutil.cpu_count(logical=False),
                'threads': psutil.cpu_count(logical=True)
            }
        except Exception as e:
            logger.error(f"Failed to get CPU metrics: {e}")
            return {}
    
    async def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory metrics"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'free': memory.free,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': swap.percent
            }
        except Exception as e:
            logger.error(f"Failed to get memory metrics: {e}")
            return {}
    
    async def _get_disk_metrics(self) -> Dict[str, Any]:
        """Get disk metrics"""
        try:
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent,
                'read_count': getattr(disk_io, 'read_count', 0),
                'write_count': getattr(disk_io, 'write_count', 0),
                'read_bytes': getattr(disk_io, 'read_bytes', 0),
                'write_bytes': getattr(disk_io, 'write_bytes', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get disk metrics: {e}")
            return {}
    
    async def _get_network_metrics(self) -> Dict[str, Any]:
        """Get network metrics"""
        try:
            net_io = psutil.net_io_counters()
            net_connections = psutil.net_connections()
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'active_connections': len([c for c in net_connections if c.status == 'ESTABLISHED'])
            }
        except Exception as e:
            logger.error(f"Failed to get network metrics: {e}")
            return {}
    
    async def _get_bot_metrics(self) -> Dict[str, Any]:
        """Get bot-specific metrics"""
        try:
            # This would be implemented based on your bot's metrics
            # For now, return placeholder data
            return {
                'uptime': await self._get_bot_uptime(),
                'messages_processed': 0,
                'commands_processed': 0,
                'active_groups': 0,
                'active_users': 0,
                'error_count': 0
            }
        except Exception as e:
            logger.error(f"Failed to get bot metrics: {e}")
            return {}
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        try:
            # Process metrics
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            # Load average
            load_avg = psutil.getloadavg()
            
            return {
                'process_count': len(processes),
                'top_processes': processes[:5],  # Top 5 by CPU
                'load_avg_1min': load_avg[0],
                'load_avg_5min': load_avg[1],
                'load_avg_15min': load_avg[2],
                'boot_time': psutil.boot_time(),
                'users': len(psutil.users())
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    async def _get_bot_uptime(self) -> float:
        """Get bot uptime in seconds"""
        # This should be implemented to track bot startup time
        # For now, return placeholder
        return 0.0
    
    async def _check_for_alerts(self, metrics: Dict) -> List[Dict]:
        """Check metrics for potential issues"""
        alerts = []
        
        # CPU alerts
        cpu_percent = metrics.get('cpu', {}).get('percent', 0)
        if cpu_percent > 90:
            alerts.append({
                'type': 'cpu',
                'level': 'critical',
                'message': f'CPU usage is critically high: {cpu_percent}%',
                'value': cpu_percent,
                'threshold': 90
            })
        elif cpu_percent > 80:
            alerts.append({
                'type': 'cpu',
                'level': 'warning',
                'message': f'CPU usage is high: {cpu_percent}%',
                'value': cpu_percent,
                'threshold': 80
            })
        
        # Memory alerts
        memory_percent = metrics.get('memory', {}).get('percent', 0)
        if memory_percent > 90:
            alerts.append({
                'type': 'memory',
                'level': 'critical',
                'message': f'Memory usage is critically high: {memory_percent}%',
                'value': memory_percent,
                'threshold': 90
            })
        elif memory_percent > 80:
            alerts.append({
                'type': 'memory',
                'level': 'warning',
                'message': f'Memory usage is high: {memory_percent}%',
                'value': memory_percent,
                'threshold': 80
            })
        
        # Disk alerts
        disk_percent = metrics.get('disk', {}).get('percent', 0)
        if disk_percent > 90:
            alerts.append({
                'type': 'disk',
                'level': 'critical',
                'message': f'Disk usage is critically high: {disk_percent}%',
                'value': disk_percent,
                'threshold': 90
            })
        elif disk_percent > 80:
            alerts.append({
                'type': 'disk',
                'level': 'warning',
                'message': f'Disk usage is high: {disk_percent}%',
                'value': disk_percent,
                'threshold': 80
            })
        
        # Load average alerts
        load_avg_1min = metrics.get('system', {}).get('load_avg_1min', 0)
        cpu_count = metrics.get('cpu', {}).get('cores', 1)
        
        if load_avg_1min > cpu_count * 2:
            alerts.append({
                'type': 'load',
                'level': 'critical',
                'message': f'System load is critically high: {load_avg_1min}',
                'value': load_avg_1min,
                'threshold': cpu_count * 2
            })
        elif load_avg_1min > cpu_count:
            alerts.append({
                'type': 'load',
                'level': 'warning',
                'message': f'System load is high: {load_avg_1min}',
                'value': load_avg_1min,
                'threshold': cpu_count
            })
        
        return alerts
    
    async def _log_health_check(self, metrics: Dict):
        """Log health check to file"""
        try:
            health_data = JSONEngine.load_json(self.health_file, {})
            
            if 'health_checks' not in health_data:
                health_data['health_checks'] = []
            
            # Keep only recent checks
            health_data['health_checks'].append(metrics)
            
            # Limit to last 1000 checks
            if len(health_data['health_checks']) > 1000:
                health_data['health_checks'] = health_data['health_checks'][-1000:]
            
            health_data['metadata']['updated'] = datetime.now().isoformat()
            JSONEngine.save_json(self.health_file, health_data)
        
        except Exception as e:
            logger.error(f"Failed to log health check: {e}")
    
    async def _update_daily_stats(self, metrics: Dict):
        """Update daily statistics"""
        try:
            health_data = JSONEngine.load_json(self.health_file, {})
            
            date = metrics['date']
            
            if 'daily_stats' not in health_data:
                health_data['daily_stats'] = {}
            
            if date not in health_data['daily_stats']:
                health_data['daily_stats'][date] = {
                    'checks': 0,
                    'healthy_checks': 0,
                    'warning_checks': 0,
                    'critical_checks': 0,
                    'avg_cpu': 0,
                    'avg_memory': 0,
                    'avg_disk': 0,
                    'alerts': [],
                    'first_check': metrics['timestamp'],
                    'last_check': metrics['timestamp']
                }
            
            daily = health_data['daily_stats'][date]
            daily['checks'] += 1
            daily['last_check'] = metrics['timestamp']
            
            # Update status counts
            if metrics['status'] == 'healthy':
                daily['healthy_checks'] += 1
            elif metrics['status'] == 'warning':
                daily['warning_checks'] += 1
            elif metrics['status'] == 'critical':
                daily['critical_checks'] += 1
            
            # Update averages (moving average)
            current_cpu = metrics.get('cpu', {}).get('percent', 0)
            current_memory = metrics.get('memory', {}).get('percent', 0)
            current_disk = metrics.get('disk', {}).get('percent', 0)
            
            daily['avg_cpu'] = (daily['avg_cpu'] * (daily['checks'] - 1) + current_cpu) / daily['checks']
            daily['avg_memory'] = (daily['avg_memory'] * (daily['checks'] - 1) + current_memory) / daily['checks']
            daily['avg_disk'] = (daily['avg_disk'] * (daily['checks'] - 1) + current_disk) / daily['checks']
            
            # Add alerts
            for alert in metrics.get('alerts', []):
                daily['alerts'].append({
                    'timestamp': metrics['timestamp'],
                    'type': alert['type'],
                    'level': alert['level'],
                    'message': alert['message']
                })
            
            JSONEngine.save_json(self.health_file, health_data)
        
        except Exception as e:
            logger.error(f"Failed to update daily stats: {e}")
    
    async def _send_alerts(self, alerts: List[Dict], metrics: Dict):
        """Send alerts to appropriate channels"""
        try:
            health_data = JSONEngine.load_json(self.health_file, {})
            
            # Log alerts
            if 'alerts' not in health_data:
                health_data['alerts'] = []
            
            for alert in alerts:
                alert_entry = {
                    'timestamp': metrics['timestamp'],
                    'type': alert['type'],
                    'level': alert['level'],
                    'message': alert['message'],
                    'value': alert['value'],
                    'threshold': alert['threshold'],
                    'acknowledged': False
                }
                health_data['alerts'].append(alert_entry)
            
            # Here you would implement actual alert sending
            # For example, sending to Telegram admins, email, etc.
            # For now, just log them
            for alert in alerts:
                if alert['level'] == 'critical':
                    logger.critical(f"SYSTEM ALERT: {alert['message']}")
                else:
                    logger.warning(f"System warning: {alert['message']}")
            
            JSONEngine.save_json(self.health_file, health_data)
        
        except Exception as e:
            logger.error(f"Failed to send alerts: {e}")
    
    async def start(self):
        """Start continuous health monitoring"""
        if not self.monitoring_enabled:
            return
        
        logger.info("Starting system health monitoring...")
        
        try:
            while self.monitoring_enabled:
                await self.perform_health_check()
                await asyncio.sleep(self.check_interval)
        
        except asyncio.CancelledError:
            logger.info("Health monitoring stopped")
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
    
    async def stop(self):
        """Stop health monitoring"""
        self.monitoring_enabled = False
        logger.info("Stopping system health monitoring...")
    
    async def get_health_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get health summary for specified hours"""
        try:
            health_data = JSONEngine.load_json(self.health_file, {})
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_checks = []
            
            for check in health_data.get('health_checks', []):
                check_time = datetime.fromisoformat(check['timestamp'])
                if check_time >= cutoff_time:
                    recent_checks.append(check)
            
            if not recent_checks:
                return {'message': 'No health checks found in specified period'}
            
            # Calculate statistics
            cpu_values = [c.get('cpu', {}).get('percent', 0) for c in recent_checks]
            memory_values = [c.get('memory', {}).get('percent', 0) for c in recent_checks]
            disk_values = [c.get('disk', {}).get('percent', 0) for c in recent_checks]
            
            status_counts = {'healthy': 0, 'warning': 0, 'critical': 0, 'error': 0}
            for check in recent_checks:
                status = check.get('status', 'unknown')
                if status in status_counts:
                    status_counts[status] += 1
            
            return {
                'period_hours': hours,
                'total_checks': len(recent_checks),
                'status_distribution': status_counts,
                'averages': {
                    'cpu': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    'memory': sum(memory_values) / len(memory_values) if memory_values else 0,
                    'disk': sum(disk_values) / len(disk_values) if disk_values else 0
                },
                'maximums': {
                    'cpu': max(cpu_values) if cpu_values else 0,
                    'memory': max(memory_values) if memory_values else 0,
                    'disk': max(disk_values) if disk_values else 0
                },
                'recent_alerts': self._get_recent_alerts(health_data, hours),
                'uptime_percentage': (
                    status_counts['healthy'] / len(recent_checks) * 100
                    if recent_checks else 0
                )
            }
        
        except Exception as e:
            logger.error(f"Failed to get health summary: {e}")
            return {'error': str(e)}
    
    def _get_recent_alerts(self, health_data: Dict, hours: int) -> List[Dict]:
        """Get recent alerts"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_alerts = []
            
            for alert in health_data.get('alerts', []):
                alert_time = datetime.fromisoformat(alert['timestamp'])
                if alert_time >= cutoff_time:
                    recent_alerts.append(alert)
            
            return recent_alerts[-10:]  # Last 10 alerts
        
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    async def get_daily_report(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily health report"""
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            health_data = JSONEngine.load_json(self.health_file, {})
            
            if date not in health_data.get('daily_stats', {}):
                return {'message': f'No data for date {date}'}
            
            daily_stats = health_data['daily_stats'][date]
            
            return {
                'date': date,
                'checks': daily_stats['checks'],
                'status_breakdown': {
                    'healthy': daily_stats['healthy_checks'],
                    'warning': daily_stats['warning_checks'],
                    'critical': daily_stats['critical_checks']
                },
                'averages': {
                    'cpu': daily_stats['avg_cpu'],
                    'memory': daily_stats['avg_memory'],
                    'disk': daily_stats['avg_disk']
                },
                'alerts': daily_stats['alerts'],
                'first_check': daily_stats['first_check'],
                'last_check': daily_stats['last_check'],
                'uptime_percentage': (
                    daily_stats['healthy_checks'] / daily_stats['checks'] * 100
                    if daily_stats['checks'] > 0 else 0
                )
            }
        
        except Exception as e:
            logger.error(f"Failed to get daily report: {e}")
            return {'error': str(e)}
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            health_data = JSONEngine.load_json(self.health_file, {})
            
            # Find and acknowledge alert
            for i, alert in enumerate(health_data.get('alerts', [])):
                # Generate alert ID from timestamp and type
                current_id = f"{alert['timestamp']}_{alert['type']}"
                if current_id == alert_id:
                    health_data['alerts'][i]['acknowledged'] = True
                    health_data['alerts'][i]['acknowledged_at'] = datetime.now().isoformat()
                    break
            
            JSONEngine.save_json(self.health_file, health_data)
            return True
        
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False
    
    async def cleanup_old_data(self, days_to_keep: int = 7) -> int:
        """Cleanup old health data"""
        try:
            health_data = JSONEngine.load_json(self.health_file, {})
            
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date()
            
            # Cleanup health checks
            if 'health_checks' in health_data:
                original_count = len(health_data['health_checks'])
                health_data['health_checks'] = [
                    check for check in health_data['health_checks']
                    if datetime.fromisoformat(check['timestamp']).date() >= cutoff_date
                ]
                removed_checks = original_count - len(health_data['health_checks'])
            
            # Cleanup daily stats
            if 'daily_stats' in health_data:
                dates_to_remove = []
                for date_str in health_data['daily_stats']:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    if date < cutoff_date:
                        dates_to_remove.append(date_str)
                
                for date_str in dates_to_remove:
                    del health_data['daily_stats'][date_str]
            
            # Cleanup old alerts (keep only unacknowledged and recent)
            if 'alerts' in health_data:
                original_alerts = len(health_data['alerts'])
                health_data['alerts'] = [
                    alert for alert in health_data['alerts']
                    if (datetime.fromisoformat(alert['timestamp']).date() >= cutoff_date or
                        not alert.get('acknowledged', False))
                ]
                removed_alerts = original_alerts - len(health_data['alerts'])
            
            health_data['metadata']['updated'] = datetime.now().isoformat()
            JSONEngine.save_json(self.health_file, health_data)
            
            logger.info(f"Cleaned up {removed_checks} old health checks and {removed_alerts} alerts")
            return removed_checks + removed_alerts
        
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    async def schedule_health_checks(self, interval_minutes: int = 5):
        """Schedule regular health checks"""
        self.check_interval = interval_minutes * 60
        logger.info(f"Scheduled health checks every {interval_minutes} minutes")
    
    async def generate_health_report(self) -> str:
        """Generate health status report"""
        try:
            summary = await self.get_health_summary(hours=24)
            
            report_lines = [
                "🏥 **System Health Report**",
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                f"**Period:** Last 24 hours",
                "",
                "📊 **Overall Status**",
                f"• Total Checks: {summary.get('total_checks', 0)}",
                f"• Uptime: {summary.get('uptime_percentage', 0):.1f}%",
                f"• Healthy: {summary.get('status_distribution', {}).get('healthy', 0)}",
                f"• Warnings: {summary.get('status_distribution', {}).get('warning', 0)}",
                f"• Critical: {summary.get('status_distribution', {}).get('critical', 0)}",
                "",
                "📈 **Resource Usage (Average)**",
                f"• CPU: {summary.get('averages', {}).get('cpu', 0):.1f}%",
                f"• Memory: {summary.get('averages', {}).get('memory', 0):.1f}%",
                f"• Disk: {summary.get('averages', {}).get('disk', 0):.1f}%",
                "",
                "🚨 **Recent Alerts**"
            ]
            
            alerts = summary.get('recent_alerts', [])
            if alerts:
                for alert in alerts[-5:]:  # Last 5 alerts
                    level_emoji = '⚠️' if alert.get('level') == 'warning' else '🚨'
                    report_lines.append(
                        f"• {level_emoji} {alert.get('message', 'Unknown alert')}"
                    )
            else:
                report_lines.append("• No recent alerts")
            
            report_lines.extend([
                "",
                "💡 **Recommendations**"
            ])
            
            # Add recommendations based on metrics
            if summary.get('averages', {}).get('cpu', 0) > 70:
                report_lines.append("• Consider optimizing CPU usage")
            
            if summary.get('averages', {}).get('memory', 0) > 75:
                report_lines.append("• Consider reducing memory usage")
            
            if summary.get('averages', {}).get('disk', 0) > 80:
                report_lines.append("• Consider cleaning up disk space")
            
            if not report_lines[-1].startswith("• Consider"):
                report_lines.append("• System is operating within normal parameters")
            
            return "\n".join(report_lines)
        
        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")
            return f"Error generating health report: {e}"