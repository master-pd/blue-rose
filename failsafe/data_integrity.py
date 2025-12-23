#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Data Integrity Checker
Ensures JSON file integrity and auto-repair
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import hashlib

from config import Config

logger = logging.getLogger(__name__)

class DataIntegrity:
    """Data Integrity Manager"""
    
    def __init__(self):
        self.config = Config
        self.backup_dir = Path("backups/integrity")
        self.backup_dir.mkdir(exist_ok=True, parents=True)
    
    async def check_all_files(self) -> Dict[str, Any]:
        """Check integrity of all JSON files"""
        results = {
            'total_files': 0,
            'valid_files': 0,
            'corrupted_files': 0,
            'repaired_files': 0,
            'details': {}
        }
        
        for file_name, file_path in self.config.JSON_PATHS.items():
            if file_path.exists():
                results['total_files'] += 1
                status = await self._check_file(file_path)
                results['details'][file_name] = status
                
                if status['valid']:
                    results['valid_files'] += 1
                else:
                    results['corrupted_files'] += 1
                    if status['repaired']:
                        results['repaired_files'] += 1
        
        return results
    
    async def _check_file(self, file_path: Path) -> Dict[str, Any]:
        """Check and repair single file"""
        result = {
            'path': str(file_path),
            'valid': False,
            'repaired': False,
            'size': 0,
            'error': None,
            'backup_created': False
        }
        
        try:
            # Get file size
            result['size'] = file_path.stat().st_size
            
            if result['size'] == 0:
                result['error'] = "Empty file"
                await self._repair_file(file_path)
                result['repaired'] = True
                return result
            
            # Read and parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse
            try:
                data = json.loads(content)
                # Verify it's a dict or list
                if not isinstance(data, (dict, list)):
                    result['error'] = "Not a JSON object or array"
                    await self._repair_file(file_path)
                    result['repaired'] = True
                else:
                    result['valid'] = True
            except json.JSONDecodeError as e:
                result['error'] = f"JSON decode error: {e}"
                await self._repair_file(file_path)
                result['repaired'] = True
            
            # Create backup if valid
            if result['valid']:
                await self._create_backup(file_path)
                result['backup_created'] = True
        
        except Exception as e:
            result['error'] = f"Unexpected error: {e}"
            logger.error(f"Error checking {file_path}: {e}")
        
        return result
    
    async def _repair_file(self, file_path: Path):
        """Repair corrupted JSON file"""
        try:
            # Create backup before repair
            backup_path = self.backup_dir / f"{file_path.name}.corrupted"
            if file_path.exists():
                file_path.rename(backup_path)
            
            # Determine default structure based on filename
            default_data = self._get_default_structure(file_path.name)
            
            # Write default structure
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Repaired file: {file_path.name}")
        
        except Exception as e:
            logger.error(f"Failed to repair {file_path}: {e}")
    
    def _get_default_structure(self, filename: str) -> Dict[str, Any]:
        """Get default structure for JSON file"""
        defaults = {
            'bot_info.json': Config.get_bot_info(),
            'bot_admins.json': {
                'owner_id': Config.BOT_OWNER_ID,
                'admins': Config.BOT_ADMIN_IDS,
                'added_at': "2024-01-01T00:00:00"
            },
            'bot_settings.json': {
                'features': Config.FEATURES,
                'rate_limits': Config.RATE_LIMITS,
                'moderation': Config.MODERATION,
                'security': Config.SECURITY
            },
            'groups.json': {},
            'group_status.json': {},
            'users.json': {},
            'plans.json': Config.PAYMENT_PLANS,
            'payment_requests.json': {},
            'memory_store.json': {}
        }
        
        return defaults.get(filename, {})
    
    async def _create_backup(self, file_path: Path):
        """Create backup of valid file"""
        try:
            import datetime
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            import shutil
            shutil.copy2(file_path, backup_path)
            
            # Keep only last 5 backups
            self._cleanup_old_backups(file_path.stem)
        
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
    
    def _cleanup_old_backups(self, stem: str, keep: int = 5):
        """Cleanup old backup files"""
        try:
            backups = list(self.backup_dir.glob(f"{stem}_*"))
            if len(backups) > keep:
                backups.sort(key=lambda x: x.stat().st_mtime)
                for old_backup in backups[:-keep]:
                    old_backup.unlink()
        
        except Exception as e:
            logger.error(f"Failed to cleanup backups: {e}")
    
    async def verify_hash(self, file_path: Path) -> str:
        """Calculate file hash for verification"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    async def schedule_integrity_checks(self, interval_hours: int = 24):
        """Schedule regular integrity checks"""
        import asyncio
        
        while True:
            logger.info("Running scheduled integrity check...")
            results = await self.check_all_files()
            
            if results['corrupted_files'] > 0:
                logger.warning(
                    f"Found {results['corrupted_files']} corrupted files. "
                    f"Repaired {results['repaired_files']}"
                )
            
            await asyncio.sleep(interval_hours * 3600)