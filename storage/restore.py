#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Restore Manager
Data restoration and recovery system
"""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import Config
from .json_engine import JSONEngine
from .backup import BackupManager

logger = logging.getLogger(__name__)

class RestoreManager:
    """Data Restoration Manager"""
    
    def __init__(self):
        self.config = Config
        self.backup_manager = BackupManager()
        self.restore_history = []
        
    async def restore_from_backup(self, backup_name: str, 
                                verify_only: bool = False) -> Dict[str, Any]:
        """Restore data from a backup"""
        try:
            # Find backup
            backup_info = await self._find_backup(backup_name)
            if not backup_info:
                return {
                    'success': False,
                    'error': f"Backup not found: {backup_name}",
                }
            
            if verify_only:
                # Just verify backup without restoring
                is_valid = await self._verify_backup(backup_info)
                return {
                    'success': is_valid,
                    'verified': is_valid,
                    'backup_info': backup_info,
                    'message': 'Backup verification completed' if is_valid else 'Backup verification failed',
                }
            
            # Create pre-restore backup
            pre_restore = await self.backup_manager.create_backup(
                "pre_restore", 
                f"Before restoring {backup_name}"
            )
            
            if not pre_restore:
                logger.warning("Failed to create pre-restore backup, continuing anyway")
            
            # Perform restoration
            success = await self.backup_manager.restore_backup(backup_name)
            
            if success:
                # Log restoration
                restore_log = {
                    'backup_name': backup_name,
                    'restored_at': datetime.now().isoformat(),
                    'pre_restore_backup': str(pre_restore) if pre_restore else None,
                    'backup_info': backup_info,
                }
                
                self.restore_history.append(restore_log)
                await self._save_restore_history()
                
                # Verify restoration
                verification = await self._verify_restoration(backup_info)
                
                return {
                    'success': True,
                    'backup_name': backup_name,
                    'restored_at': restore_log['restored_at'],
                    'verification': verification,
                    'message': 'Data restoration completed successfully',
                }
            else:
                return {
                    'success': False,
                    'error': 'Restoration failed',
                    'backup_name': backup_name,
                }
                
        except Exception as e:
            logger.error(f"Restoration failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def _find_backup(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Find backup by name"""
        backups = await self.backup_manager.list_backups()
        
        for backup in backups:
            if backup['name'] == backup_name:
                return backup
        
        # Try partial match
        for backup in backups:
            if backup_name in backup['name']:
                return backup
        
        return None
    
    async def _verify_backup(self, backup_info: Dict[str, Any]) -> bool:
        """Verify backup integrity"""
        try:
            backup_path = Path(backup_info['path'])
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Check file size
            expected_size = backup_info.get('size', 0)
            actual_size = backup_path.stat().st_size
            
            if expected_size > 0 and actual_size < expected_size * 0.9:
                logger.warning(f"Backup file size mismatch: expected ~{expected_size}, got {actual_size}")
                # Don't fail for size mismatch, just warn
            
            # Try to open as ZIP
            import zipfile
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Check if ZIP is valid
                test_result = zipf.testzip()
                if test_result is not None:
                    logger.error(f"Backup ZIP corrupted: {test_result}")
                    return False
                
                # Check for essential files
                file_list = zipf.namelist()
                essential_files = [
                    'data/bot/bot_info.json',
                    'data/bot/bot_settings.json',
                ]
                
                for essential in essential_files:
                    if essential not in file_list:
                        logger.warning(f"Missing essential file in backup: {essential}")
            
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    async def _verify_restoration(self, backup_info: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that restoration was successful"""
        verification = {
            'success': True,
            'checks': [],
            'issues': [],
        }
        
        try:
            # Check essential files
            essential_files = [
                self.config.JSON_PATHS['bot_info'],
                self.config.JSON_PATHS['bot_settings'],
                self.config.JSON_PATHS['groups'],
            ]
            
            for file_path in essential_files:
                if file_path.exists():
                    verification['checks'].append({
                        'file': str(file_path),
                        'exists': True,
                        'valid_json': JSONEngine.validate_json(file_path),
                    })
                    
                    if not JSONEngine.validate_json(file_path):
                        verification['issues'].append(f"Invalid JSON: {file_path}")
                        verification['success'] = False
                else:
                    verification['checks'].append({
                        'file': str(file_path),
                        'exists': False,
                        'valid_json': False,
                    })
                    verification['issues'].append(f"Missing file: {file_path}")
                    verification['success'] = False
            
            # Check data consistency
            await self._check_data_consistency(verification)
            
        except Exception as e:
            verification['success'] = False
            verification['issues'].append(f"Verification error: {e}")
        
        return verification
    
    async def _check_data_consistency(self, verification: Dict[str, Any]):
        """Check data consistency after restoration"""
        try:
            # Check bot info
            bot_info = JSONEngine.load_json(self.config.JSON_PATHS['bot_info'], {})
            if not bot_info:
                verification['issues'].append("Bot info is empty")
            
            # Check groups
            groups = JSONEngine.load_json(self.config.JSON_PATHS['groups'], {})
            if not isinstance(groups, dict):
                verification['issues'].append("Groups data is invalid")
            
            verification['checks'].append({
                'check': 'data_consistency',
                'bot_info_exists': bool(bot_info),
                'groups_count': len(groups) if isinstance(groups, dict) else 0,
            })
            
        except Exception as e:
            verification['issues'].append(f"Consistency check error: {e}")
    
    async def _save_restore_history(self):
        """Save restoration history"""
        try:
            history_file = self.config.DATA_DIR / "restore_history.json"
            
            # Load existing history
            existing = JSONEngine.load_json(history_file, [])
            
            # Add new entries
            existing.extend(self.restore_history[-10:])  # Keep last 10 entries
            
            # Save
            JSONEngine.save_json(history_file, existing)
            
        except Exception as e:
            logger.error(f"Failed to save restore history: {e}")
    
    async def load_restore_history(self):
        """Load restoration history"""
        try:
            history_file = self.config.DATA_DIR / "restore_history.json"
            
            if history_file.exists():
                self.restore_history = JSONEngine.load_json(history_file, [])
            else:
                self.restore_history = []
                
        except Exception as e:
            logger.error(f"Failed to load restore history: {e}")
            self.restore_history = []
    
    async def get_restore_options(self) -> List[Dict[str, Any]]:
        """Get available restore options"""
        backups = await self.backup_manager.list_backups()
        
        options = []
        for backup in backups:
            options.append({
                'name': backup['name'],
                'type': backup.get('type', 'unknown'),
                'created_at': backup.get('created_at'),
                'description': backup.get('description', ''),
                'size': backup.get('size', 0),
                'size_human': self._format_size(backup.get('size', 0)),
                'verified': await self._verify_backup(backup),
            })
        
        return options
    
    async def emergency_restore(self) -> Dict[str, Any]:
        """Perform emergency restoration from latest backup"""
        try:
            # Get latest backup
            backups = await self.backup_manager.list_backups()
            
            if not backups:
                return {
                    'success': False,
                    'error': 'No backups available',
                }
            
            latest_backup = backups[0]
            
            logger.critical(f"Performing emergency restore from: {latest_backup['name']}")
            
            # Perform restoration
            result = await self.restore_from_backup(latest_backup['name'])
            
            if result['success']:
                logger.critical("Emergency restoration successful!")
            else:
                logger.critical(f"Emergency restoration failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.critical(f"Emergency restoration failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def partial_restore(self, backup_name: str, 
                            files_to_restore: List[str]) -> Dict[str, Any]:
        """Restore specific files from backup"""
        try:
            # Find backup
            backup_info = await self._find_backup(backup_name)
            if not backup_info:
                return {
                    'success': False,
                    'error': f"Backup not found: {backup_name}",
                }
            
            backup_path = Path(backup_info['path'])
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f"Backup file not found: {backup_path}",
                }
            
            # Create temporary directory
            import tempfile
            temp_dir = Path(tempfile.mkdtemp())
            
            try:
                # Extract specific files
                import zipfile
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    # Extract all files first
                    zipf.extractall(temp_dir)
                    
                    # Restore specific files
                    restored_files = []
                    for file_pattern in files_to_restore:
                        # Find matching files
                        for extracted_file in temp_dir.rglob(file_pattern):
                            if extracted_file.is_file():
                                # Calculate destination
                                rel_path = extracted_file.relative_to(temp_dir)
                                dest_path = self.config.DATA_DIR.parent / rel_path
                                
                                # Create directory
                                dest_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                # Backup original if exists
                                if dest_path.exists():
                                    backup_copy = dest_path.with_suffix(dest_path.suffix + '.backup')
                                    shutil.copy2(dest_path, backup_copy)
                                
                                # Copy file
                                shutil.copy2(extracted_file, dest_path)
                                restored_files.append(str(dest_path))
                
                # Cleanup
                shutil.rmtree(temp_dir)
                
                return {
                    'success': True,
                    'restored_files': restored_files,
                    'backup_name': backup_name,
                    'message': f"Restored {len(restored_files)} files from backup",
                }
                
            except Exception as e:
                # Cleanup on error
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                raise e
                
        except Exception as e:
            logger.error(f"Partial restore failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    async def get_restore_status(self) -> Dict[str, Any]:
        """Get restore manager status"""
        await self.load_restore_history()
        
        return {
            'restore_history_count': len(self.restore_history),
            'latest_restore': self.restore_history[-1] if self.restore_history else None,
            'available_backups': len(await self.backup_manager.list_backups()),
            'last_verified': datetime.now().isoformat(),
        }