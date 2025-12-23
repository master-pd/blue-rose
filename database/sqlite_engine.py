#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - SQLite Engine
SQLite database management
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)

class SQLiteEngine:
    """SQLite Database Engine"""
    
    def __init__(self):
        self.config = Config
        self.db_path = self.config.SQLITE_DB_PATH
        self.connection = None
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with tables"""
        try:
            # Create database directory if it doesn't exist
            self.db_path.parent.mkdir(exist_ok=True)
            
            # Connect to database
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            
            # Create tables
            self._create_tables()
            
            logger.info(f"SQLite database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT,
            is_bot BOOLEAN,
            is_premium BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            total_messages INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 0,
            is_global_admin BOOLEAN DEFAULT FALSE,
            metadata TEXT
        )
        ''')
        
        # Groups table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY,
            title TEXT,
            type TEXT,
            username TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_at TIMESTAMP,
            plan TEXT DEFAULT 'free',
            plan_active BOOLEAN DEFAULT FALSE,
            expiry_date TIMESTAMP,
            bot_is_admin BOOLEAN DEFAULT FALSE,
            total_members INTEGER DEFAULT 0,
            total_messages INTEGER DEFAULT 0,
            settings TEXT,
            metadata TEXT
        )
        ''')
        
        # Group admins table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            role TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES groups(chat_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(chat_id, user_id)
        )
        ''')
        
        # Messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER,
            chat_id INTEGER,
            user_id INTEGER,
            text TEXT,
            message_type TEXT,
            timestamp TIMESTAMP,
            replied_to INTEGER,
            has_media BOOLEAN DEFAULT FALSE,
            media_type TEXT,
            is_deleted BOOLEAN DEFAULT FALSE,
            metadata TEXT,
            PRIMARY KEY (chat_id, message_id),
            FOREIGN KEY (chat_id) REFERENCES groups(chat_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Warnings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            reason TEXT,
            warned_by INTEGER,
            warning_level INTEGER DEFAULT 1,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (chat_id) REFERENCES groups(chat_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Mutes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mutes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            reason TEXT,
            muted_by INTEGER,
            muted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            unmute_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (chat_id) REFERENCES groups(chat_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Bans table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            reason TEXT,
            banned_by INTEGER,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            unban_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (chat_id) REFERENCES groups(chat_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Payment requests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            plan TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            rejection_reason TEXT,
            metadata TEXT,
            FOREIGN KEY (chat_id) REFERENCES groups(chat_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Analytics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT,
            metric_value TEXT,
            chat_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            period TEXT,
            metadata TEXT,
            FOREIGN KEY (chat_id) REFERENCES groups(chat_id)
        )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_warnings_user ON warnings(user_id, chat_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_group_admins ON group_admins(chat_id, user_id)')
        
        self.connection.commit()
        cursor.close()
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                results = [dict(row) for row in cursor.fetchall()]
            else:
                self.connection.commit()
                results = []
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            self.connection.rollback()
            raise
    
    def insert_user(self, user_data: Dict[str, Any]) -> bool:
        """Insert or update user"""
        try:
            query = '''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, language_code, is_bot, is_premium, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            params = (
                user_data.get('id'),
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'),
                user_data.get('language_code'),
                user_data.get('is_bot', False),
                user_data.get('is_premium', False),
                datetime.now().isoformat(),
            )
            
            self.execute_query(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert user: {e}")
            return False
    
    def insert_message(self, message_data: Dict[str, Any]) -> bool:
        """Insert message"""
        try:
            query = '''
            INSERT INTO messages 
            (message_id, chat_id, user_id, text, message_type, timestamp, replied_to, has_media, media_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            text = message_data.get('text') or message_data.get('caption') or ''
            message_type = 'text'
            
            if message_data.get('photo'):
                message_type = 'photo'
            elif message_data.get('video'):
                message_type = 'video'
            elif message_data.get('document'):
                message_type = 'document'
            elif message_data.get('audio'):
                message_type = 'audio'
            elif message_data.get('voice'):
                message_type = 'voice'
            elif message_data.get('sticker'):
                message_type = 'sticker'
            
            params = (
                message_data.get('message_id'),
                message_data.get('chat', {}).get('id'),
                message_data.get('from', {}).get('id'),
                text,
                message_type,
                datetime.fromtimestamp(message_data.get('date', 0)).isoformat(),
                message_data.get('reply_to_message', {}).get('message_id'),
                bool(message_type != 'text'),
                message_type if message_type != 'text' else None,
            )
            
            self.execute_query(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert message: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            query = 'SELECT * FROM users WHERE user_id = ?'
            results = self.execute_query(query, (user_id,))
            
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    def get_group(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get group by ID"""
        try:
            query = 'SELECT * FROM groups WHERE chat_id = ?'
            results = self.execute_query(query, (chat_id,))
            
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Failed to get group: {e}")
            return None
    
    def update_group_plan(self, chat_id: int, plan: str, expiry_date: Optional[str] = None) -> bool:
        """Update group subscription plan"""
        try:
            query = '''
            UPDATE groups 
            SET plan = ?, plan_active = TRUE, expiry_date = ?
            WHERE chat_id = ?
            '''
            
            self.execute_query(query, (plan, expiry_date, chat_id))
            return True
            
        except Exception as e:
            logger.error(f"Failed to update group plan: {e}")
            return False
    
    def get_recent_messages(self, chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages for a chat"""
        try:
            query = '''
            SELECT * FROM messages 
            WHERE chat_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            '''
            
            return self.execute_query(query, (chat_id, limit))
            
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []
    
    def backup_database(self, backup_path: Optional[Path] = None) -> bool:
        """Create database backup"""
        try:
            if backup_path is None:
                backup_path = self.config.DATA_DIR / "backups" / f"database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            backup_path.parent.mkdir(exist_ok=True)
            
            # Create backup connection
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Backup main database
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        try:
            if self.connection:
                self.connection.close()
                logger.info("Database connection closed")
                
        except Exception as e:
            logger.error(f"Failed to close database: {e}")