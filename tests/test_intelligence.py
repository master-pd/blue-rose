#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Intelligence Tests
Tests for intelligence modules
"""

import unittest
from unittest.mock import Mock, patch

from intelligence.question_detector import QuestionDetector
from intelligence.keyword_extractor import KeywordExtractor
from intelligence.similarity_engine import SimilarityEngine

class TestQuestionDetector(unittest.TestCase):
    """Test Question Detector"""
    
    def setUp(self):
        self.detector = QuestionDetector()
    
    async def test_question_detection(self):
        """Test question detection"""
        # English questions
        text = "What is your name?"
        is_question, confidence, q_type = await self.detector.detect(text)
        self.assertTrue(is_question)
        self.assertGreater(confidence, 0.5)
        self.assertEqual(q_type, 'what')
        
        # Bangla questions
        text = "আপনার নাম কি?"
        is_question, confidence, q_type = await self.detector.detect(text)
        self.assertTrue(is_question)
        self.assertGreater(confidence, 0.5)
        
        # Non-questions
        text = "Hello there"
        is_question, confidence, q_type = await self.detector.detect(text)
        self.assertFalse(is_question)
    
    async def test_question_parts_extraction(self):
        """Test question parts extraction"""
        text = "What is the capital of Bangladesh?"
        parts = await self.detector.extract_question_parts(text)
        
        self.assertTrue(parts['is_question'])
        self.assertEqual(parts['question_word'], 'what')
        self.assertEqual(parts['question_type'], 'what')

class TestKeywordExtractor(unittest.TestCase):
    """Test Keyword Extractor"""
    
    def setUp(self):
        self.extractor = KeywordExtractor()
    
    async def test_keyword_extraction(self):
        """Test keyword extraction"""
        text = "The quick brown fox jumps over the lazy dog"
        result = await self.extractor.extract(text, language='english')
        
        self.assertIn('keywords', result)
        self.assertGreater(len(result['keywords']), 0)
        self.assertIn('categories', result)
    
    async def test_bangla_keyword_extraction(self):
        """Test Bangla keyword extraction"""
        text = "আমার সোনার বাংলা আমি তোমায় ভালোবাসি"
        result = await self.extractor.extract(text, language='bangla')
        
        self.assertIn('keywords', result)
        self.assertIn('categories', result)

class TestSimilarityEngine(unittest.TestCase):
    """Test Similarity Engine"""
    
    def setUp(self):
        self.engine = SimilarityEngine()
    
    async def test_similarity_calculation(self):
        """Test similarity calculation"""
        text1 = "The cat sat on the mat"
        text2 = "The cat sat on the rug"
        
        similarity = await self.engine.calculate(text1, text2, method='cosine')
        self.assertGreater(similarity, 0.5)
        self.assertLessEqual(similarity, 1.0)
    
    async def test_find_similar(self):
        """Test finding similar texts"""
        query = "hello world"
        texts = ["hello world", "hi there", "greetings earth"]
        
        similar = await self.engine.find_similar(query, texts, threshold=0.5)
        self.assertGreater(len(similar), 0)
        self.assertEqual(similar[0][0], "hello world")

if __name__ == '__main__':
    unittest.main()