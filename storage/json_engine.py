#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - JSON Engine
JSON file management with atomic writes and locking
"""

import json
import os
import logging
import threading
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)

class JSONEngine:
    """JSON File Management Engine"""
    
    # Thread lock for file operations
    _file_locks = {}
    _global_lock = threading.RLock()
    
    @staticmethod
    def load_json(file_path: Union[str, Path], default: Any = None) -> Any:
        """Load JSON file with error handling"""
        try:
            file_path = Path(file_path)
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists
            if not file_path.exists():
                if default is not None:
                    # Save default value
                    JSONEngine.save_json(file_path, default)
                    return default
                return {} if isinstance(default, type(None)) else default
            
            # Get file lock
            with JSONEngine._get_file_lock(file_path):
                # Read file
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                logger.debug(f"Loaded JSON: {file_path}")
                return data
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            # Try to backup corrupted file
            JSONEngine._backup_corrupted_file(file_path, e)
            
            if default is not None:
                # Save default and return it
                JSONEngine.save_json(file_path, default)
                return default
            return {} if isinstance(default, type(None)) else default
            
        except Exception as e:
            logger.error(f"Failed to load JSON {file_path}: {e}")
            if default is not None:
                return default
            return {} if isinstance(default, type(None)) else default
    
    @staticmethod
    def save_json(file_path: Union[str, Path], data: Any, 
                 indent: int = 2, ensure_ascii: bool = False) -> bool:
        """Save data to JSON file with atomic write"""
        try:
            file_path = Path(file_path)
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get file lock
            with JSONEngine._get_file_lock(file_path):
                # Create temporary file
                temp_fd, temp_path = tempfile.mkstemp(
                    prefix=f"{file_path.stem}_",
                    suffix=".tmp",
                    dir=file_path.parent
                )
                
                try:
                    # Write to temporary file
                    with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, 
                                 default=JSONEngine._json_serializer)
                    
                    # Atomic replace
                    os.replace(temp_path, file_path)
                    
                    logger.debug(f"Saved JSON: {file_path}")
                    return True
                    
                except Exception as e:
                    # Clean up temp file on error
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    raise e
                    
        except Exception as e:
            logger.error(f"Failed to save JSON {file_path}: {e}")
            return False
    
    @staticmethod
    def update_json(file_path: Union[str, Path], updates: Dict[str, Any], 
                   create_if_missing: bool = True) -> bool:
        """Update JSON file with specific fields"""
        try:
            file_path = Path(file_path)
            
            # Load existing data
            if file_path.exists():
                existing_data = JSONEngine.load_json(file_path, {})
            else:
                if not create_if_missing:
                    return False
                existing_data = {}
            
            # Update data
            JSONEngine._deep_update(existing_data, updates)
            
            # Save updated data
            return JSONEngine.save_json(file_path, existing_data)
            
        except Exception as e:
            logger.error(f"Failed to update JSON {file_path}: {e}")
            return False
    
    @staticmethod
    def append_to_list(file_path: Union[str, Path], item: Any, 
                      max_items: Optional[int] = None) -> bool:
        """Append item to a JSON list"""
        try:
            file_path = Path(file_path)
            
            # Load existing list
            if file_path.exists():
                data = JSONEngine.load_json(file_path, [])
                if not isinstance(data, list):
                    logger.error(f"{file_path} does not contain a list")
                    return False
            else:
                data = []
            
            # Append item
            data.append(item)
            
            # Limit items if specified
            if max_items is not None and len(data) > max_items:
                data = data[-max_items:]
            
            # Save updated list
            return JSONEngine.save_json(file_path, data)
            
        except Exception as e:
            logger.error(f"Failed to append to JSON list {file_path}: {e}")
            return False
    
    @staticmethod
    def get_value(file_path: Union[str, Path], key_path: str, 
                 default: Any = None) -> Any:
        """Get value from JSON using dot notation key path"""
        try:
            data = JSONEngine.load_json(file_path, {})
            
            # Split key path
            keys = key_path.split('.')
            
            # Navigate through nested structure
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            
            return current
            
        except Exception as e:
            logger.error(f"Failed to get value from {file_path}: {e}")
            return default
    
    @staticmethod
    def set_value(file_path: Union[str, Path], key_path: str, 
                 value: Any) -> bool:
        """Set value in JSON using dot notation key path"""
        try:
            # Load existing data
            data = JSONEngine.load_json(file_path, {})
            
            # Split key path
            keys = key_path.split('.')
            
            # Navigate to parent
            current = data
            for i, key in enumerate(keys[:-1]):
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]
            
            # Set value
            current[keys[-1]] = value
            
            # Save updated data
            return JSONEngine.save_json(file_path, data)
            
        except Exception as e:
            logger.error(f"Failed to set value in {file_path}: {e}")
            return False
    
    @staticmethod
    def delete_key(file_path: Union[str, Path], key_path: str) -> bool:
        """Delete key from JSON using dot notation"""
        try:
            # Load existing data
            data = JSONEngine.load_json(file_path, {})
            
            # Split key path
            keys = key_path.split('.')
            
            # Navigate to parent
            current = data
            for i, key in enumerate(keys[:-1]):
                if key not in current:
                    return True  # Key doesn't exist
                current = current[key]
            
            # Delete key
            if keys[-1] in current:
                del current[keys[-1]]
                return JSONEngine.save_json(file_path, data)
            
            return True  # Key doesn't exist
            
        except Exception as e:
            logger.error(f"Failed to delete key from {file_path}: {e}")
            return False
    
    @staticmethod
    def _deep_update(target: Dict, updates: Dict):
        """Deep update dictionary"""
        for key, value in updates.items():
            if (key in target and isinstance(target[key], dict) 
                and isinstance(value, dict)):
                JSONEngine._deep_update(target[key], value)
            else:
                target[key] = value
    
    @staticmethod
    def _json_serializer(obj):
        """Custom JSON serializer for unsupported types"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
    
    @staticmethod
    def _get_file_lock(file_path: Path) -> threading.RLock:
        """Get or create lock for a file"""
        lock_key = str(file_path.absolute())
        
        with JSONEngine._global_lock:
            if lock_key not in JSONEngine._file_locks:
                JSONEngine._file_locks[lock_key] = threading.RLock()
            
            return JSONEngine._file_locks[lock_key]
    
    @staticmethod
    def _backup_corrupted_file(file_path: Path, error: Exception):
        """Backup corrupted JSON file"""
        try:
            if file_path.exists():
                # Create backup directory
                backup_dir = Config.DATA_DIR / "corrupted_backups"
                backup_dir.mkdir(exist_ok=True)
                
                # Create backup filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = backup_dir / f"{file_path.stem}_corrupted_{timestamp}.json"
                
                # Copy corrupted file
                import shutil
                shutil.copy2(file_path, backup_file)
                
                # Log the corruption
                corruption_log = {
                    'original_file': str(file_path),
                    'backup_file': str(backup_file),
                    'error': str(error),
                    'timestamp': datetime.now().isoformat(),
                }
                
                log_file = backup_dir / "corruption_log.json"
                logs = JSONEngine.load_json(log_file, [])
                logs.append(corruption_log)
                JSONEngine.save_json(log_file, logs)
                
                logger.warning(f"Backed up corrupted file: {file_path} -> {backup_file}")
                
        except Exception as e:
            logger.error(f"Failed to backup corrupted file {file_path}: {e}")
    
    @staticmethod
    def get_all_files(directory: Union[str, Path], pattern: str = "*.json") -> List[Path]:
        """Get all JSON files in a directory"""
        try:
            directory = Path(directory)
            
            if not directory.exists():
                return []
            
            return list(directory.glob(pattern))
            
        except Exception as e:
            logger.error(f"Failed to get files from {directory}: {e}")
            return []
    
    @staticmethod
    def force_save_all():
        """Force save all pending changes (placeholder)"""
        # In a real implementation, this would save all cached data
        logger.debug("Force save all called")
        return True
    
    @staticmethod
    def validate_json(file_path: Union[str, Path]) -> bool:
        """Validate JSON file without loading it"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            
            return True
            
        except:
            return False
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get information about a JSON file"""
        try:
            file_path = Path(file_path)
            
            info = {
                'exists': file_path.exists(),
                'path': str(file_path),
                'size': 0,
                'modified': None,
                'valid_json': False,
            }
            
            if file_path.exists():
                info['size'] = file_path.stat().st_size
                info['modified'] = datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
                info['valid_json'] = JSONEngine.validate_json(file_path)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return {'exists': False, 'path': str(file_path)}