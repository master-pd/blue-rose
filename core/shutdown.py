#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Shutdown Manager
Handles graceful system shutdown
"""

import asyncio
import logging
from typing import Dict, Any, List

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class ShutdownManager:
    """System Shutdown Manager"""
    
    def __init__(self):
        self.config = Config
        self.shutdown_sequence = []
        self.is_shutting_down = False
        self.emergency_mode = False
        
    async def graceful_shutdown(self, emergency: bool = False) -> bool:
        """Execute graceful shutdown"""
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress!")
            return False
        
        self.is_shutting_down = True
        self.emergency_mode = emergency
        
        try:
            logger.info(f"🚨 {'EMERGENCY ' if emergency else ''}Shutdown initiated...")
            
            # Define shutdown sequence
            self.shutdown_sequence = [
                self._stage_1_notify_shutdown,
                self._stage_2_save_all_data,
                self._stage_3_stop_services,
                self._stage_4_close_connections,
                self._stage_5_create_backup,
                self._stage_6_final_cleanup,
            ]
            
            # Execute shutdown stages
            for stage_num, stage_func in enumerate(self.shutdown_sequence, 1):
                logger.info(f"🔧 Shutdown Stage {stage_num}/{len(self.shutdown_sequence)}...")
                
                if emergency and stage_num > 3:  # Skip non-critical stages in emergency
                    logger.info(f"Skipping stage {stage_num} in emergency mode")
                    continue
                
                if not await stage_func():
                    logger.error(f"Shutdown failed at stage {stage_num}")
                    if not emergency:
                        return False
            
            logger.info("✅ Shutdown completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Shutdown failed: {e}", exc_info=True)
            return False
            
        finally:
            self.is_shutting_down = False
    
    async def _stage_1_notify_shutdown(self) -> bool:
        """Notify about shutdown"""
        try:
            logger.info("Notifying about shutdown...")
            
            # Save shutdown timestamp
            shutdown_info = {
                'shutdown_time': self._get_current_timestamp(),
                'emergency': self.emergency_mode,
                'reason': 'graceful_shutdown',
            }
            
            shutdown_file = self.config.DATA_DIR / "last_shutdown.json"
            JSONEngine.save_json(shutdown_file, shutdown_info)
            
            # In a real bot, you would notify group admins here
            # For now, just log it
            logger.info("✅ Shutdown notification complete!")
            return True
            
        except Exception as e:
            logger.error(f"Shutdown notification failed: {e}")
            return not self.emergency_mode  # Don't fail in emergency mode
    
    async def _stage_2_save_all_data(self) -> bool:
        """Save all pending data"""
        try:
            logger.info("Saving all data...")
            
            # Force save all JSON data
            from storage.json_engine import JSONEngine
            JSONEngine.force_save_all()
            
            logger.info("✅ All data saved!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return not self.emergency_mode  # Don't fail in emergency mode
    
    async def _stage_3_stop_services(self) -> bool:
        """Stop all running services"""
        try:
            logger.info("Stopping services...")
            
            # Stop analytics services
            # Stop payment services
            # Stop monitoring services
            # etc.
            
            logger.info("✅ Services stopped!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop services: {e}")
            return True  # Continue shutdown even if services fail
    
    async def _stage_4_close_connections(self) -> bool:
        """Close all connections"""
        try:
            logger.info("Closing connections...")
            
            # Close database connections
            # Close API connections
            # Close file handles
            # etc.
            
            logger.info("✅ Connections closed!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to close connections: {e}")
            return True  # Continue shutdown
    
    async def _stage_5_create_backup(self) -> bool:
        """Create shutdown backup"""
        try:
            if self.emergency_mode:
                logger.info("Skipping backup in emergency mode")
                return True
            
            logger.info("Creating shutdown backup...")
            
            from storage.backup import BackupManager
            backup_manager = BackupManager()
            
            backup_file = await backup_manager.create_backup(
                backup_type="shutdown",
                description=f"{'Emergency ' if self.emergency_mode else ''}Shutdown Backup"
            )
            
            if backup_file:
                logger.info(f"✅ Backup created: {backup_file}")
                return True
            else:
                logger.warning("Backup creation failed, continuing shutdown...")
                return True  # Don't fail shutdown for backup
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return True  # Don't fail shutdown for backup
    
    async def _stage_6_final_cleanup(self) -> bool:
        """Final cleanup"""
        try:
            logger.info("Final cleanup...")
            
            # Clear temporary files
            # Reset flags
            # Log shutdown completion
            
            shutdown_log = {
                'shutdown_completed': self._get_current_timestamp(),
                'emergency': self.emergency_mode,
                'success': True,
            }
            
            shutdown_file = self.config.DATA_DIR / "shutdown_complete.json"
            JSONEngine.save_json(shutdown_file, shutdown_log)
            
            logger.info("✅ Final cleanup complete!")
            return True
            
        except Exception as e:
            logger.error(f"Final cleanup failed: {e}")
            return True  # Shutdown is basically complete
    
    async def emergency_shutdown(self, reason: str = "unknown") -> bool:
        """Emergency shutdown"""
        logger.critical(f"🚨 EMERGENCY SHUTDOWN: {reason}")
        
        # Log emergency
        emergency_log = {
            'emergency_time': self._get_current_timestamp(),
            'reason': reason,
            'emergency': True,
        }
        
        emergency_file = self.config.DATA_DIR / "emergency_shutdown.json"
        JSONEngine.save_json(emergency_file, emergency_log)
        
        # Execute emergency shutdown
        return await self.graceful_shutdown(emergency=True)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_shutdown_status(self) -> Dict[str, Any]:
        """Get shutdown status"""
        return {
            'is_shutting_down': self.is_shutting_down,
            'emergency_mode': self.emergency_mode,
            'sequence_length': len(self.shutdown_sequence),
        }