#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Boot Manager
Handles system startup and initialization
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any

from config import Config
from storage.json_engine import JSONEngine
from failsafe.auto_restart import AutoRestart

logger = logging.getLogger(__name__)

class BootManager:
    """System Boot Manager"""
    
    def __init__(self):
        self.config = Config
        self.stages = []
        self.current_stage = 0
        self.boot_successful = False
        self.auto_restart = AutoRestart()
        
    async def boot(self) -> bool:
        """Execute boot sequence"""
        try:
            logger.info("🔧 Starting boot sequence...")
            
            # Define boot stages
            self.stages = [
                self._stage_1_check_dependencies,
                self._stage_2_create_directories,
                self._stage_3_validate_config,
                self._stage_4_load_core_data,
                self._stage_5_initialize_modules,
                self._stage_6_start_services,
                self._stage_7_final_checks,
            ]
            
            # Execute stages
            for stage_num, stage_func in enumerate(self.stages, 1):
                self.current_stage = stage_num
                logger.info(f"⚙️ Boot Stage {stage_num}/{len(self.stages)}...")
                
                if not await stage_func():
                    logger.error(f"Boot failed at stage {stage_num}")
                    return False
            
            self.boot_successful = True
            logger.info("✅ Boot sequence completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Boot sequence failed: {e}", exc_info=True)
            await self.auto_restart.handle_boot_failure(e)
            return False
    
    async def _stage_1_check_dependencies(self) -> bool:
        """Check Python and system dependencies"""
        try:
            logger.info("Checking dependencies...")
            
            # Check Python version
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 12):
                logger.error(f"Python 3.12+ required. Current: {python_version.major}.{python_version.minor}")
                return False
            
            # Check required modules
            required_modules = [
                'telebot',
                'json',
                'asyncio',
                'logging',
                'pathlib',
                'datetime',
            ]
            
            missing_modules = []
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                logger.error(f"Missing modules: {', '.join(missing_modules)}")
                return False
            
            logger.info("✅ Dependencies check passed!")
            return True
            
        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            return False
    
    async def _stage_2_create_directories(self) -> bool:
        """Create necessary directories"""
        try:
            logger.info("Creating directories...")
            
            # Create all directories from config
            for directory in self.config.SUBDIRS:
                directory.mkdir(exist_ok=True, parents=True)
                logger.debug(f"Created/Verified directory: {directory}")
            
            # Create __init__.py files
            init_dirs = [
                self.config.BASE_DIR / "core",
                self.config.BASE_DIR / "engine",
                self.config.BASE_DIR / "storage",
                self.config.BASE_DIR / "data",
                self.config.BASE_DIR / "intelligence",
                self.config.BASE_DIR / "moderation",
                self.config.BASE_DIR / "supremacy",
                self.config.BASE_DIR / "payments",
                self.config.BASE_DIR / "panels",
                self.config.BASE_DIR / "keyboards",
                self.config.BASE_DIR / "analytics",
                self.config.BASE_DIR / "failsafe",
                self.config.DATA_DIR / "bot",
                self.config.DATA_DIR / "groups",
                self.config.DATA_DIR / "users",
                self.config.DATA_DIR / "payments",
                self.config.DATA_DIR / "messages",
                self.config.DATA_DIR / "schedules",
            ]
            
            for dir_path in init_dirs:
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
                    logger.debug(f"Created __init__.py in {dir_path}")
            
            logger.info("✅ Directories created successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            return False
    
    async def _stage_3_validate_config(self) -> bool:
        """Validate configuration"""
        try:
            logger.info("Validating configuration...")
            
            issues = self.config.validate_config()
            
            if issues:
                logger.error("Configuration validation failed!")
                for issue in issues:
                    logger.error(f"  - {issue}")
                return False
            
            logger.info("✅ Configuration validated successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    async def _stage_4_load_core_data(self) -> bool:
        """Load core JSON data"""
        try:
            logger.info("Loading core data...")
            
            # Initialize JSON files if they don't exist
            self.config.initialize_defaults()
            
            # Verify all JSON files exist
            for file_name, file_path in self.config.JSON_PATHS.items():
                if not file_path.exists():
                    logger.error(f"JSON file missing: {file_path}")
                    return False
            
            logger.info("✅ Core data loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load core data: {e}")
            return False
    
    async def _stage_5_initialize_modules(self) -> bool:
        """Initialize core modules"""
        try:
            logger.info("Initializing modules...")
            
            # This will be populated by the kernel
            # Module initialization happens in kernel.start()
            
            logger.info("✅ Modules initialization scheduled!")
            return True
            
        except Exception as e:
            logger.error(f"Module initialization failed: {e}")
            return False
    
    async def _stage_6_start_services(self) -> bool:
        """Start background services"""
        try:
            logger.info("Starting background services...")
            
            # Start auto-restart service
            await self.auto_restart.start()
            
            # Add other background services here
            
            logger.info("✅ Background services started!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            return False
    
    async def _stage_7_final_checks(self) -> bool:
        """Final system checks"""
        try:
            logger.info("Running final checks...")
            
            # Check disk space
            import shutil
            
            disk_usage = shutil.disk_usage(self.config.BASE_DIR)
            free_gb = disk_usage.free / (1024**3)
            
            if free_gb < 1:  # Less than 1GB free
                logger.warning(f"Low disk space: {free_gb:.2f}GB free")
            
            # Check memory
            import psutil
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent > 90:  # More than 90% memory used
                logger.warning(f"High memory usage: {memory_percent}%")
            
            logger.info("✅ Final checks completed!")
            return True
            
        except Exception as e:
            logger.warning(f"Final checks encountered issues: {e}")
            # Don't fail boot for these checks
            return True
    
    async def shutdown(self):
        """Shutdown boot manager"""
        try:
            logger.info("Shutting down boot manager...")
            
            # Stop auto-restart service
            await self.auto_restart.stop()
            
            logger.info("✅ Boot manager shutdown complete!")
            
        except Exception as e:
            logger.error(f"Error shutting down boot manager: {e}")
    
    def get_boot_status(self) -> Dict[str, Any]:
        """Get boot status"""
        return {
            'successful': self.boot_successful,
            'current_stage': self.current_stage,
            'total_stages': len(self.stages),
            'stages_completed': self.current_stage - 1,
            'auto_restart_enabled': self.auto_restart.enabled,
        }