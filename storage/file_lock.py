#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - File Lock
Thread-safe file locking mechanism
"""

import threading
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class FileLock:
    """Thread-safe file locking system"""
    
    # Global lock registry
    _locks: Dict[str, threading.RLock] = {}
    _global_lock = threading.RLock()
    
    def __init__(self, file_path: Path, timeout: int = 30):
        self.file_path = Path(file_path)
        self.lock_key = str(self.file_path.absolute())
        self.timeout = timeout
        self.acquired = False
        self.acquire_time = None
        
    @contextmanager
    def lock(self):
        """Context manager for file locking"""
        try:
            self.acquire()
            yield self
        finally:
            self.release()
    
    def acquire(self) -> bool:
        """Acquire lock for the file"""
        try:
            with FileLock._global_lock:
                if self.lock_key not in FileLock._locks:
                    FileLock._locks[self.lock_key] = threading.RLock()
                
                lock_obj = FileLock._locks[self.lock_key]
            
            # Try to acquire lock with timeout
            acquired = lock_obj.acquire(timeout=self.timeout)
            
            if acquired:
                self.acquired = True
                self.acquire_time = time.time()
                logger.debug(f"Lock acquired: {self.file_path}")
                return True
            else:
                logger.warning(f"Lock timeout: {self.file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to acquire lock for {self.file_path}: {e}")
            return False
    
    def release(self):
        """Release the lock"""
        try:
            if self.acquired:
                with FileLock._global_lock:
                    if self.lock_key in FileLock._locks:
                        lock_obj = FileLock._locks[self.lock_key]
                        lock_obj.release()
                
                self.acquired = False
                hold_time = time.time() - (self.acquire_time or time.time())
                logger.debug(f"Lock released: {self.file_path} (held for {hold_time:.2f}s)")
                
        except Exception as e:
            logger.error(f"Failed to release lock for {self.file_path}: {e}")
    
    def is_locked(self) -> bool:
        """Check if file is currently locked"""
        with FileLock._global_lock:
            if self.lock_key in FileLock._locks:
                lock_obj = FileLock._locks[self.lock_key]
                # Try to acquire without waiting to check if locked
                acquired = lock_obj.acquire(blocking=False)
                if acquired:
                    lock_obj.release()
                    return False
                return True
            return False
    
    def get_lock_info(self) -> Dict[str, Any]:
        """Get information about the lock"""
        return {
            'file_path': str(self.file_path),
            'lock_key': self.lock_key,
            'acquired': self.acquired,
            'acquire_time': self.acquire_time,
            'is_locked': self.is_locked(),
            'timeout': self.timeout,
        }
    
    @classmethod
    def cleanup_stale_locks(cls, timeout: int = 3600):
        """Clean up stale locks (not implemented fully)"""
        # In a real implementation, this would track lock acquisition times
        # and release locks that have been held too long
        logger.debug("Lock cleanup called")
    
    @classmethod
    def get_all_locks(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about all active locks"""
        locks_info = {}
        
        with cls._global_lock:
            for lock_key, lock_obj in cls._locks.items():
                # Check if lock is acquired
                acquired = not lock_obj.acquire(blocking=False)
                if not acquired:
                    lock_obj.release()
                
                locks_info[lock_key] = {
                    'lock_key': lock_key,
                    'is_acquired': acquired,
                    'waiting_threads': lock_obj._is_owned() if hasattr(lock_obj, '_is_owned') else None,
                }
        
        return locks_info