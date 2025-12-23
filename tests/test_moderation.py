#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Moderation Tests
Tests for moderation modules
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from moderation.anti_spam import AntiSpam
from moderation.auto_warn import AutoWarn

class TestAntiSpam(unittest.TestCase):
    """Test Anti-Spam system"""
    
    def setUp(self):
        self.anti_spam = AntiSpam()
    
    async def test_spam_detection(self):
        """Test spam detection"""
        message = {
            'chat': {'id': -1001234567890},
            'from': {'id': 123456},
            'text': 'BUY NOW!!! FREE MONEY $$$ http://spam.com'
        }
        
        result = await self.anti_spam.check_message(message)
        self.assertTrue(result['is_spam'])
        self.assertGreater(result['score'], 50)
    
    async def test_false_positive(self):
        """Test false positive prevention"""
        message = {
            'chat': {'id': -1001234567890},
            'from': {'id': 123456},
            'text': 'Hello everyone, how are you?'
        }
        
        result = await self.anti_spam.check_message(message)
        self.assertFalse(result['is_spam'])

class TestAutoWarn(unittest.TestCase):
    """Test Auto-Warn system"""
    
    def setUp(self):
        self.auto_warn = AutoWarn()
    
    @patch('moderation.auto_warn.JSONEngine')
    async def test_warning_issuance(self, mock_json):
        """Test warning issuance"""
        mock_json.load_json.return_value = {}
        mock_json.save_json.return_value = True
        
        result = await self.auto_warn.issue_warning(
            user_id=123456,
            chat_id=-1001234567890,
            reason='Spamming',
            warned_by=654321
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['total_warnings'], 1)

if __name__ == '__main__':
    unittest.main()