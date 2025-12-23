#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Crash Handler
Handle system crashes and errors
"""

import asyncio
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class CrashHandler:
    """System Crash Handler"""
    
    def __init__(self):
        self.config = Config
        self.crash_log_file = self.config.DATA_DIR / "failsafe" / "crash_logs.json"
        self.crash_log_file.parent.mkdir(exist_ok=True)
        self.restart_count = 0
        self.max_restarts = 3
    
    async def handle_crash(self, error: Exception, context: Dict[str, Any] = None):
        """Handle a system crash"""
        try:
            crash_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            crash_info = {
                'crash_id': crash_id,
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'context': context or {},
                'restart_count': self.restart_count,
                'bot_version': self.config.BOT_VERSION,
            }
            
            # Log crash
            await self._log_crash(crash_info)
            
            # Notify admin (in real implementation)
            await self._notify_admin(crash_info)
            
            # Check if we should restart
            if self.restart_count < self.max_restarts:
                self.restart_count += 1
                logger.critical(f"Crash #{self.restart_count} handled. Attempting restart...")
                
                # Schedule restart
                asyncio.create_task(self._schedule_restart())
            else:
                logger.critical(f"Max restarts ({self.max_restarts}) reached. Shutting down.")
                await self._emergency_shutdown()
            
            return crash_id
            
        except Exception as e:
            logger.critical(f"Crash handler itself crashed: {e}")
            return None
    
    async def _log_crash(self, crash_info: Dict[str, Any]):
        """Log crash to file"""
        try:
            crashes = JSONEngine.load_json(self.crash_log_file, [])
            crashes.append(crash_info)
            
            # Keep only last 100 crashes
            if len(crashes) > 100:
                crashes = crashes[-100:]
            
            JSONEngine.save_json(self.crash_log_file, crashes)
            
            logger.error(f"Crash logged: {crash_info['crash_id']}")
            
        except Exception as e:
            logger.error(f"Failed to log crash: {e}")
    
    async def _notify_admin(self, crash_info: Dict[str, Any]):
        """Notify bot admin about crash"""
        # In real implementation, send Telegram message to admin
        error_summary = f"""
🚨 <b>Bot Crash Detected</b>

<b>Crash ID:</b> {crash_info['crash_id']}
<b>Time:</b> {crash_info['timestamp']}
<b>Error:</b> {crash_info['error_type']}
<b>Message:</b> {crash_info['error_message'][:200]}

<b>Restart Count:</b> {crash_info['restart_count']}/{self.max_restarts}
        """.strip()
        
        logger.critical(f"Admin notification: {error_summary}")
    
    async def _schedule_restart(self, delay: int = 5):
        """Schedule bot restart"""
        logger.info(f"Scheduling restart in {delay} seconds...")
        await asyncio.sleep(delay)
        
        # In real implementation, this would restart the bot
        logger.info("Restarting bot...")
    
    async def _emergency_shutdown(self):
        """Emergency shutdown procedure"""
        logger.critical("Initiating emergency shutdown...")
        
        # Save emergency state
        emergency_state = {
            'shutdown_time': datetime.now().isoformat(),
            'reason': 'max_restarts_reached',
            'restart_count': self.restart_count,
            'bot_version': self.config.BOT_VERSION,
        }
        
        emergency_file = self.config.DATA_DIR / "failsafe" / "emergency_shutdown.json"
        JSONEngine.save_json(emergency_file, emergency_state)
        
        logger.critical("Emergency shutdown complete.")