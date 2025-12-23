#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Auto Restart System
Automatic crash detection and restart
"""

import asyncio
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class AutoRestart:
    """Automatic Restart Manager"""
    
    def __init__(self):
        self.config = Config
        self.crash_log_file = self.config.DATA_DIR / "crashes" / "crash_log.json"
        self.crash_log_file.parent.mkdir(exist_ok=True)
        
        self.restart_log_file = self.config.DATA_DIR / "crashes" / "restart_log.json"
        
        # Restart settings
        self.max_restarts_per_hour = 3
        self.max_restarts_per_day = 10
        self.restart_delay = 5  # seconds
        self.cooldown_period = 300  # 5 minutes after 3 restarts
        
        # State
        self.restart_count = 0
        self.last_restart_time = None
        self.is_restarting = False
        self.enabled = True
        
        # Load restart history
        self._load_restart_history()
    
    def _load_restart_history(self):
        """Load restart history from file"""
        try:
            if self.restart_log_file.exists():
                history = JSONEngine.load_json(self.restart_log_file, {})
                self.restart_count = history.get('total_restarts', 0)
                last_restart = history.get('last_restart')
                if last_restart:
                    self.last_restart_time = datetime.fromisoformat(last_restart)
        except Exception as e:
            logger.error(f"Failed to load restart history: {e}")
    
    def _save_restart_history(self):
        """Save restart history to file"""
        try:
            history = {
                'total_restarts': self.restart_count,
                'last_restart': datetime.now().isoformat() if self.last_restart_time else None,
                'settings': {
                    'max_per_hour': self.max_restarts_per_hour,
                    'max_per_day': self.max_restarts_per_day,
                    'delay': self.restart_delay,
                    'cooldown': self.cooldown_period
                },
                'enabled': self.enabled,
                'updated': datetime.now().isoformat()
            }
            
            JSONEngine.save_json(self.restart_log_file, history)
        except Exception as e:
            logger.error(f"Failed to save restart history: {e}")
    
    async def log_crash(self, error: Exception, context: Optional[Dict] = None):
        """Log a crash event"""
        try:
            # Load existing crash log
            if self.crash_log_file.exists():
                crash_log = JSONEngine.load_json(self.crash_log_file, {})
            else:
                crash_log = {
                    'metadata': {
                        'description': 'Bot crash log',
                        'version': '1.0.0',
                        'created': datetime.now().isoformat()
                    },
                    'crashes': []
                }
            
            # Create crash entry
            crash_entry = {
                'id': self._generate_crash_id(),
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {},
                'traceback': self._get_traceback(error),
                'system_info': self._get_system_info(),
                'restart_attempted': False,
                'resolved': False
            }
            
            # Add to crash log
            crash_log['crashes'].append(crash_entry)
            
            # Keep only last 100 crashes
            if len(crash_log['crashes']) > 100:
                crash_log['crashes'] = crash_log['crashes'][-100:]
            
            crash_log['metadata']['updated'] = datetime.now().isoformat()
            
            # Save crash log
            JSONEngine.save_json(self.crash_log_file, crash_log)
            
            logger.error(f"Crash logged: {type(error).__name__}: {str(error)}")
            
            return crash_entry['id']
        
        except Exception as e:
            logger.error(f"Failed to log crash: {e}")
            return None
    
    async def handle_boot_failure(self, error: Exception):
        """Handle boot sequence failure"""
        try:
            logger.critical(f"Boot failure detected: {error}")
            
            context = {
                'failure_type': 'boot',
                'boot_stage': 'unknown',
                'system_state': 'pre_init'
            }
            
            crash_id = await self.log_crash(error, context)
            
            # Check if we should attempt restart
            if await self.should_restart():
                await self.restart_bot()
            else:
                logger.critical("Maximum restart attempts reached. Manual intervention required.")
            
            return crash_id
        
        except Exception as e:
            logger.error(f"Failed to handle boot failure: {e}")
            return None
    
    async def handle_runtime_crash(self, error: Exception):
        """Handle runtime crash"""
        try:
            logger.critical(f"Runtime crash detected: {error}")
            
            context = {
                'failure_type': 'runtime',
                'system_state': 'running',
                'uptime': await self._get_bot_uptime()
            }
            
            crash_id = await self.log_crash(error, context)
            
            # Check if we should attempt restart
            if await self.should_restart():
                await self.restart_bot()
            else:
                logger.critical("Maximum restart attempts reached. Manual intervention required.")
            
            return crash_id
        
        except Exception as e:
            logger.error(f"Failed to handle runtime crash: {e}")
            return None
    
    async def should_restart(self) -> bool:
        """Determine if auto-restart should be attempted"""
        if not self.enabled:
            logger.info("Auto-restart is disabled")
            return False
        
        # Check restart limits
        current_time = datetime.now()
        
        # Check hourly limit
        hourly_count = self._get_restart_count_since(current_time - timedelta(hours=1))
        if hourly_count >= self.max_restarts_per_hour:
            logger.warning(f"Hourly restart limit reached ({hourly_count}/{self.max_restarts_per_hour})")
            
            # Check if we're in cooldown
            if self.last_restart_time:
                time_since_last = (current_time - self.last_restart_time).total_seconds()
                if time_since_last < self.cooldown_period:
                    logger.info(f"In cooldown period. {self.cooldown_period - time_since_last:.0f}s remaining")
                    return False
            
            return False
        
        # Check daily limit
        daily_count = self._get_restart_count_since(current_time - timedelta(days=1))
        if daily_count >= self.max_restarts_per_day:
            logger.warning(f"Daily restart limit reached ({daily_count}/{self.max_restarts_per_day})")
            return False
        
        return True
    
    def _get_restart_count_since(self, since_time: datetime) -> int:
        """Get number of restarts since specified time"""
        try:
            if not self.restart_log_file.exists():
                return 0
            
            history = JSONEngine.load_json(self.restart_log_file, {})
            restarts = history.get('restart_history', [])
            
            count = 0
            for restart in restarts:
                restart_time = datetime.fromisoformat(restart.get('timestamp', ''))
                if restart_time >= since_time:
                    count += 1
            
            return count
        
        except Exception as e:
            logger.error(f"Failed to get restart count: {e}")
            return 0
    
    async def restart_bot(self):
        """Restart the bot"""
        if self.is_restarting:
            logger.warning("Restart already in progress")
            return
        
        try:
            self.is_restarting = True
            self.restart_count += 1
            self.last_restart_time = datetime.now()
            
            # Log restart attempt
            await self._log_restart_attempt()
            
            logger.warning(f"Attempting auto-restart #{self.restart_count}...")
            
            # Notify admins (if bot is running)
            await self._notify_admins_of_restart()
            
            # Add delay before restart
            logger.info(f"Waiting {self.restart_delay} seconds before restart...")
            await asyncio.sleep(self.restart_delay)
            
            # Save restart history
            self._save_restart_history()
            
            # Determine restart method
            restart_method = self._determine_restart_method()
            
            logger.warning(f"Executing restart via {restart_method}...")
            
            # Execute restart
            if restart_method == 'sys_exit':
                sys.exit(1)  # Exit with error code to trigger restart by supervisor
            elif restart_method == 'subprocess':
                await self._restart_via_subprocess()
            elif restart_method == 'asyncio':
                await self._restart_via_asyncio()
            else:
                logger.error(f"Unknown restart method: {restart_method}")
                sys.exit(1)
        
        except Exception as e:
            logger.error(f"Failed to restart bot: {e}")
            self.is_restarting = False
    
    async def _log_restart_attempt(self):
        """Log restart attempt to history"""
        try:
            if self.restart_log_file.exists():
                history = JSONEngine.load_json(self.restart_log_file, {})
            else:
                history = {
                    'metadata': {
                        'description': 'Bot restart history',
                        'version': '1.0.0',
                        'created': datetime.now().isoformat()
                    },
                    'restart_history': [],
                    'total_restarts': 0
                }
            
            restart_entry = {
                'id': self._generate_restart_id(),
                'timestamp': datetime.now().isoformat(),
                'count': self.restart_count,
                'method': 'auto',
                'reason': 'crash_recovery',
                'success': False  # Will be updated if restart succeeds
            }
            
            if 'restart_history' not in history:
                history['restart_history'] = []
            
            history['restart_history'].append(restart_entry)
            history['total_restarts'] = self.restart_count
            history['metadata']['updated'] = datetime.now().isoformat()
            
            # Keep only last 50 restarts
            if len(history['restart_history']) > 50:
                history['restart_history'] = history['restart_history'][-50:]
            
            JSONEngine.save_json(self.restart_log_file, history)
        
        except Exception as e:
            logger.error(f"Failed to log restart attempt: {e}")
    
    async def _notify_admins_of_restart(self):
        """Notify admins about restart"""
        try:
            # This would be implemented to send Telegram messages to admins
            # For now, just log
            logger.info("Notifying admins of restart...")
            
            # Load admin list
            bot_admins_path = self.config.JSON_PATHS['bot_admins']
            if bot_admins_path.exists():
                bot_admins = JSONEngine.load_json(bot_admins_path, {})
                admin_ids = bot_admins.get('admins', [])
                
                # Add owner
                owner_id = bot_admins.get('owner_id')
                if owner_id:
                    admin_ids.append(owner_id)
                
                logger.info(f"Would notify {len(admin_ids)} admins of restart")
        
        except Exception as e:
            logger.error(f"Failed to notify admins: {e}")
    
    def _determine_restart_method(self) -> str:
        """Determine the best restart method based on environment"""
        try:
            # Check if running in supervisor (systemd, docker, etc.)
            if 'SUPERVISOR_ENABLED' in os.environ:
                return 'sys_exit'
            
            # Check if running in Docker
            if Path('/.dockerenv').exists():
                return 'sys_exit'
            
            # Check if running as systemd service
            if 'INVOCATION_ID' in os.environ:  # systemd sets this
                return 'sys_exit'
            
            # Default to subprocess for standalone
            return 'subprocess'
        
        except Exception:
            return 'sys_exit'  # Fallback
    
    async def _restart_via_subprocess(self):
        """Restart via subprocess"""
        try:
            # Get current Python executable and script
            python_exec = sys.executable
            script_path = Path(sys.argv[0]).absolute()
            
            # Build command
            cmd = [python_exec, str(script_path)]
            
            # Add original arguments
            cmd.extend(sys.argv[1:])
            
            logger.info(f"Restarting with command: {' '.join(cmd)}")
            
            # Start new process
            subprocess.Popen(cmd)
            
            # Exit current process
            sys.exit(0)
        
        except Exception as e:
            logger.error(f"Failed to restart via subprocess: {e}")
            sys.exit(1)
    
    async def _restart_via_asyncio(self):
        """Restart within asyncio event loop"""
        try:
            # This is a soft restart - reload modules
            logger.info("Performing soft restart (module reload)...")
            
            # Import main module
            import importlib
            import main
            
            # Reload main module
            importlib.reload(main)
            
            # Restart main function
            asyncio.create_task(main.main())
        
        except Exception as e:
            logger.error(f"Failed to restart via asyncio: {e}")
            sys.exit(1)
    
    def _generate_crash_id(self) -> str:
        """Generate unique crash ID"""
        import uuid
        return f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    def _generate_restart_id(self) -> str:
        """Generate unique restart ID"""
        import uuid
        return f"restart_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    def _get_traceback(self, error: Exception) -> str:
        """Get traceback as string"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            import platform
            import psutil
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'process_id': os.getpid(),
                'script_path': sys.argv[0],
                'arguments': sys.argv[1:]
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}
    
    async def _get_bot_uptime(self) -> float:
        """Get bot uptime in seconds"""
        # This should be implemented to track actual bot startup time
        # For now, return placeholder
        return 0.0
    
    async def start(self):
        """Start auto-restart monitoring"""
        try:
            logger.info("Starting auto-restart monitor...")
            
            # Schedule periodic health checks
            asyncio.create_task(self._periodic_health_check())
            
            # Schedule cleanup of old crash logs
            asyncio.create_task(self._periodic_cleanup())
            
            logger.info("Auto-restart monitor started")
        
        except Exception as e:
            logger.error(f"Failed to start auto-restart monitor: {e}")
    
    async def stop(self):
        """Stop auto-restart monitoring"""
        try:
            logger.info("Stopping auto-restart monitor...")
            self.enabled = False
            logger.info("Auto-restart monitor stopped")
        
        except Exception as e:
            logger.error(f"Failed to stop auto-restart monitor: {e}")
    
    async def _periodic_health_check(self):
        """Periodic health check to detect frozen state"""
        try:
            check_interval = 300  # 5 minutes
            
            while self.enabled:
                await asyncio.sleep(check_interval)
                
                # Check if bot is responsive
                if not await self._is_bot_responsive():
                    logger.warning("Bot appears unresponsive. Considering restart...")
                    
                    if await self.should_restart():
                        await self._handle_unresponsive()
        
        except asyncio.CancelledError:
            logger.info("Health check stopped")
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    async def _is_bot_responsive(self) -> bool:
        """Check if bot is responsive"""
        # Implement actual responsiveness check
        # For now, always return True
        return True
    
    async def _handle_unresponsive(self):
        """Handle unresponsive bot state"""
        try:
            logger.critical("Bot is unresponsive. Forcing restart...")
            
            error = Exception("Bot became unresponsive (possible freeze)")
            context = {
                'failure_type': 'unresponsive',
                'system_state': 'frozen',
                'detection_method': 'health_check'
            }
            
            await self.log_crash(error, context)
            await self.restart_bot()
        
        except Exception as e:
            logger.error(f"Failed to handle unresponsive state: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old crash logs"""
        try:
            cleanup_interval = 3600  # 1 hour
            
            while self.enabled:
                await asyncio.sleep(cleanup_interval)
                await self.cleanup_old_data()
        
        except asyncio.CancelledError:
            logger.info("Cleanup stopped")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Cleanup old crash and restart logs"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Cleanup crash log
            if self.crash_log_file.exists():
                crash_log = JSONEngine.load_json(self.crash_log_file, {})
                
                if 'crashes' in crash_log:
                    original_count = len(crash_log['crashes'])
                    crash_log['crashes'] = [
                        crash for crash in crash_log['crashes']
                        if datetime.fromisoformat(crash['timestamp']) >= cutoff_date
                    ]
                    removed = original_count - len(crash_log['crashes'])
                    
                    if removed > 0:
                        logger.info(f"Cleaned up {removed} old crash records")
                        
                        crash_log['metadata']['updated'] = datetime.now().isoformat()
                        JSONEngine.save_json(self.crash_log_file, crash_log)
            
            # Cleanup restart log
            if self.restart_log_file.exists():
                restart_log = JSONEngine.load_json(self.restart_log_file, {})
                
                if 'restart_history' in restart_log:
                    original_count = len(restart_log['restart_history'])
                    restart_log['restart_history'] = [
                        restart for restart in restart_log['restart_history']
                        if datetime.fromisoformat(restart['timestamp']) >= cutoff_date
                    ]
                    removed = original_count - len(restart_log['restart_history'])
                    
                    if removed > 0:
                        logger.info(f"Cleaned up {removed} old restart records")
                        
                        restart_log['metadata']['updated'] = datetime.now().isoformat()
                        JSONEngine.save_json(self.restart_log_file, restart_log)
        
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get auto-restart status"""
        return {
            'enabled': self.enabled,
            'restart_count': self.restart_count,
            'last_restart_time': self.last_restart_time.isoformat() if self.last_restart_time else None,
            'is_restarting': self.is_restarting,
            'settings': {
                'max_restarts_per_hour': self.max_restarts_per_hour,
                'max_restarts_per_day': self.max_restarts_per_day,
                'restart_delay': self.restart_delay,
                'cooldown_period': self.cooldown_period
            },
            'limits': {
                'hourly_used': self._get_restart_count_since(datetime.now() - timedelta(hours=1)),
                'hourly_max': self.max_restarts_per_hour,
                'daily_used': self._get_restart_count_since(datetime.now() - timedelta(days=1)),
                'daily_max': self.max_restarts_per_day
            }
        }
    
    async def emergency_stop(self):
        """Emergency stop - disable auto-restart"""
        try:
            logger.critical("EMERGENCY STOP: Disabling auto-restart")
            self.enabled = False
            self._save_restart_history()
            
            # Notify admins
            await self._notify_emergency_stop()
        
        except Exception as e:
            logger.error(f"Failed to emergency stop: {e}")
    
    async def _notify_emergency_stop(self):
        """Notify admins of emergency stop"""
        try:
            logger.critical("Notifying admins of emergency stop...")
            # Implementation for Telegram notifications would go here
        except Exception as e:
            logger.error(f"Failed to notify emergency stop: {e}")

# Import os for environment checks
import os