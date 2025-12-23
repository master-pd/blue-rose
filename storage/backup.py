#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Backup Manager
Data backup and snapshot system
"""

import asyncio
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import Config
from .json_engine import JSONEngine

logger = logging.getLogger(__name__)

class BackupManager:
    """Backup Management System"""
    
    def __init__(self):
        self.config = Config
        self.backup_dir = self.config.DATA_DIR / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup rotation settings
        self.max_daily_backups = 7
        self.max_weekly_backups = 4
        self.max_monthly_backups = 6
    
    async def create_backup(self, backup_type: str = "manual",
                          description: str = "") -> Optional[Path]:
        """Create a new backup"""
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}"
            
            if description:
                safe_desc = "".join(c for c in description if c.isalnum() or c in " _-")
                backup_name += f"_{safe_desc}"
            
            backup_path = self.backup_dir / f"{backup_name}.zip"
            
            # Create backup
            success = await self._create_zip_backup(backup_path)
            
            if success:
                # Create backup metadata
                metadata = {
                    'name': backup_name,
                    'path': str(backup_path),
                    'type': backup_type,
                    'description': description,
                    'created_at': datetime.now().isoformat(),
                    'size': backup_path.stat().st_size if backup_path.exists() else 0,
                    'data_files': await self._get_backup_contents(),
                }
                
                metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
                JSONEngine.save_json(metadata_file, metadata)
                
                logger.info(f"Backup created: {backup_path} ({backup_type})")
                
                # Run backup rotation
                await self.rotate_backups()
                
                return backup_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    async def _create_zip_backup(self, backup_path: Path) -> bool:
        """Create ZIP backup of data directory"""
        try:
            # Create ZIP file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all JSON files from data directory
                data_dir = self.config.DATA_DIR
                
                for json_file in data_dir.rglob("*.json"):
                    # Skip backup directory
                    if self.backup_dir in json_file.parents:
                        continue
                    
                    # Add file to ZIP with relative path
                    arcname = json_file.relative_to(data_dir.parent)
                    zipf.write(json_file, arcname)
                    
                    logger.debug(f"Added to backup: {json_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create ZIP backup: {e}")
            
            # Clean up failed backup file
            if backup_path.exists():
                try:
                    backup_path.unlink()
                except:
                    pass
            
            return False
    
    async def _get_backup_contents(self) -> List[str]:
        """Get list of files included in backup"""
        contents = []
        data_dir = self.config.DATA_DIR
        
        for json_file in data_dir.rglob("*.json"):
            if self.backup_dir in json_file.parents:
                continue
            
            relative_path = str(json_file.relative_to(data_dir))
            contents.append(relative_path)
        
        return contents
    
    async def rotate_backups(self):
        """Rotate backups based on retention policy"""
        try:
            # Get all backups
            backups = await self._get_all_backups()
            
            if not backups:
                return
            
            # Separate backups by type and age
            now = datetime.now()
            daily_backups = []
            weekly_backups = []
            monthly_backups = []
            other_backups = []
            
            for backup in backups:
                created_at = datetime.fromisoformat(backup['created_at'])
                age_days = (now - created_at).days
                backup_type = backup.get('type', 'manual')
                
                if backup_type == 'daily':
                    daily_backups.append((age_days, backup))
                elif backup_type == 'weekly':
                    weekly_backups.append((age_days, backup))
                elif backup_type == 'monthly':
                    monthly_backups.append((age_days, backup))
                else:
                    other_backups.append((age_days, backup))
            
            # Sort by age (oldest first)
            daily_backups.sort(key=lambda x: x[0])
            weekly_backups.sort(key=lambda x: x[0])
            monthly_backups.sort(key=lambda x: x[0])
            other_backups.sort(key=lambda x: x[0])
            
            # Remove excess backups
            await self._remove_excess_backups(daily_backups, self.max_daily_backups)
            await self._remove_excess_backups(weekly_backups, self.max_weekly_backups)
            await self._remove_excess_backups(monthly_backups, self.max_monthly_backups)
            
            # Remove old manual backups (older than 30 days)
            for age, backup in other_backups:
                if age > 30:
                    await self._delete_backup(backup)
            
            logger.info("Backup rotation completed")
            
        except Exception as e:
            logger.error(f"Backup rotation failed: {e}")
    
    async def _remove_excess_backups(self, backups: List, max_count: int):
        """Remove excess backups beyond maximum count"""
        if len(backups) > max_count:
            # Remove oldest backups
            for i in range(len(backups) - max_count):
                age, backup = backups[i]
                await self._delete_backup(backup)
    
    async def _delete_backup(self, backup: Dict[str, Any]):
        """Delete a backup and its metadata"""
        try:
            # Delete backup file
            backup_path = Path(backup['path'])
            if backup_path.exists():
                backup_path.unlink()
            
            # Delete metadata file
            metadata_path = self.backup_dir / f"{backup['name']}_metadata.json"
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Deleted old backup: {backup['name']}")
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup['name']}: {e}")
    
    async def _get_all_backups(self) -> List[Dict[str, Any]]:
        """Get all backup metadata"""
        backups = []
        
        for metadata_file in self.backup_dir.glob("*_metadata.json"):
            try:
                metadata = JSONEngine.load_json(metadata_file)
                if metadata:
                    backups.append(metadata)
            except:
                pass
        
        return backups
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = await self._get_all_backups()
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return backups
    
    async def restore_backup(self, backup_name: str) -> bool:
        """Restore from a backup"""
        try:
            # Find backup
            metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
            backup_file = self.backup_dir / f"{backup_name}.zip"
            
            if not metadata_file.exists() or not backup_file.exists():
                logger.error(f"Backup not found: {backup_name}")
                return False
            
            # Load metadata
            metadata = JSONEngine.load_json(metadata_file)
            
            # Create restore directory
            restore_dir = self.config.DATA_DIR / "restore_tmp"
            if restore_dir.exists():
                shutil.rmtree(restore_dir)
            restore_dir.mkdir()
            
            # Extract backup
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(restore_dir)
            
            # Restore files
            data_dir = self.config.DATA_DIR
            
            # Backup current data first
            await self.create_backup("pre_restore", f"Before restoring {backup_name}")
            
            # Copy restored files
            for item in restore_dir.rglob("*"):
                if item.is_file():
                    # Calculate destination path
                    rel_path = item.relative_to(restore_dir)
                    dest_path = data_dir.parent / rel_path
                    
                    # Create destination directory
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(item, dest_path)
                    logger.debug(f"Restored: {dest_path}")
            
            # Cleanup
            shutil.rmtree(restore_dir)
            
            logger.info(f"Restored from backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_name}: {e}")
            return False
    
    async def schedule_automatic_backups(self):
        """Schedule automatic backups"""
        # This would be called during bot startup
        # For now, just log
        logger.info("Automatic backup scheduling enabled")
        
        # Schedule daily backup at 2 AM
        # In a real implementation, this would use asyncio or a scheduling library
        
        return True
    
    async def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics"""
        backups = await self._get_all_backups()
        
        total_size = 0
        by_type = {}
        
        for backup in backups:
            backup_type = backup.get('type', 'unknown')
            size = backup.get('size', 0)
            
            total_size += size
            
            if backup_type not in by_type:
                by_type[backup_type] = {'count': 0, 'size': 0}
            
            by_type[backup_type]['count'] += 1
            by_type[backup_type]['size'] += size
        
        return {
            'total_backups': len(backups),
            'total_size': total_size,
            'size_human': self._format_size(total_size),
            'by_type': by_type,
            'backup_dir': str(self.backup_dir),
            'available_space': await self._get_available_space(),
        }
    
    async def _get_available_space(self) -> int:
        """Get available disk space"""
        try:
            import shutil
            usage = shutil.disk_usage(self.backup_dir)
            return usage.free
        except:
            return 0
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"