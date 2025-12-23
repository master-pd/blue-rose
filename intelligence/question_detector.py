#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Question Detector
Detect questions in messages
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class QuestionDetector:
    """Question Detection System"""
    
    def __init__(self):
        # Question patterns (Bangla + English)
        self.patterns = {
            'bangla': [
                r'কি\?', r'কেন\?', r'কখন\?', r'কোথায়\?', r'কেমন\?',
                r'কে\?', r'কাকে\?', r'কিসে\?', r'কিসের\?', r'কি ছিল\?',
                r'কি হবে\?', r'কি করতে\?', r'কি করে\?', r'কি বল\?',
                r'কি করা\?', r'কি করব\?', r'কি করবো\?', r'কি করেছ\?',
                r'কি বলছ\?', r'কি হচ্ছ\?', r'কি হলো\?',
                r'কি জান\?', r'কি জানো\?', r'কি জানেন\?',
                r'কি চাও\?', r'কি চান\?', r'কি চাচ্ছ\?',
            ],
            'english': [
                r'what\?', r'why\?', r'when\?', r'where\?', r'how\?',
                r'who\?', r'whom\?', r'which\?', r'whose\?',
                r'is there', r'are there', r'can you', r'could you',
                r'would you', r'should i', r'do you', r'did you',
                r'will you', r'have you', r'has he', r'has she',
                r'does it', r'is it', r'are you', r'am i',
                r'\?$',  # Ends with question mark
            ],
            'urdu': [
                r'کیا\?', r'کیوں\?', r'کب\?', r'کہاں\?', r'کس\?',
                r'کون\?', r'کونسا\?', r'کسے\?',
            ],
            'arabic': [
                r'ماذا\?', r'لماذا\?', r'متى\?', r'أين\?', r'كيف\?',
                r'من\?', r'لمن\?', r'أي\?',
            ]
        }
        
        # Question words without question mark
        self.question_words = {
            'bangla': ['কি', 'কেন', 'কখন', 'কোথায়', 'কেমন', 'কে', 'কাকে'],
            'english': ['what', 'why', 'when', 'where', 'how', 'who', 'whom', 'which'],
            'urdu': ['کیا', 'کیوں', 'کب', 'کہاں', 'کس', 'کون'],
            'arabic': ['ماذا', 'لماذا', 'متى', 'أين', 'كيف', 'من'],
        }
        
        # Confidence scores for different patterns
        self.confidence_scores = {
            'ends_with_question_mark': 0.9,
            'contains_question_word_with_mark': 0.8,
            'contains_question_word': 0.6,
            'question_pattern': 0.7,
            'help_request': 0.5,
        }
    
    async def detect(self, text: str) -> Tuple[bool, float, Optional[str]]:
        """Detect if text contains a question"""
        if not text or not isinstance(text, str):
            return False, 0.0, None
        
        text_lower = text.lower().strip()
        
        # Check if ends with question mark
        if text_lower.endswith('?'):
            confidence = self.confidence_scores['ends_with_question_mark']
            question_type = await self._determine_question_type(text)
            return True, confidence, question_type
        
        # Check for question patterns
        for lang, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    confidence = self.confidence_scores['question_pattern']
                    question_type = await self._determine_question_type(text)
                    return True, confidence, question_type
        
        # Check for question words with question mark in middle
        for lang, words in self.question_words.items():
            for word in words:
                pattern = rf'{word}[^\?]*\?'
                if re.search(pattern, text, re.IGNORECASE):
                    confidence = self.confidence_scores['contains_question_word_with_mark']
                    question_type = await self._determine_question_type(text)
                    return True, confidence, question_type
        
        # Check for question words without question mark
        for lang, words in self.question_words.items():
            for word in words:
                # Check if word appears and sentence seems like a question
                if word in text_lower:
                    # Additional checks for question structure
                    if await self._looks_like_question(text):
                        confidence = self.confidence_scores['contains_question_word']
                        question_type = await self._determine_question_type(text)
                        return True, confidence, question_type
        
        # Check for help requests
        if await self._is_help_request(text):
            confidence = self.confidence_scores['help_request']
            return True, confidence, 'help'
        
        return False, 0.0, None
    
    async def _looks_like_question(self, text: str) -> bool:
        """Check if text looks like a question based on structure"""
        text_lower = text.lower().strip()
        
        # Check for inversion (English)
        english_inversions = [
            ('are you', 'you are'),
            ('is he', 'he is'),
            ('is she', 'she is'),
            ('is it', 'it is'),
            ('do you', 'you do'),
            ('did you', 'you did'),
            ('can you', 'you can'),
            ('could you', 'you could'),
            ('would you', 'you would'),
            ('should i', 'i should'),
            ('have you', 'you have'),
            ('has he', 'he has'),
            ('has she', 'she has'),
        ]
        
        for inversion in english_inversions:
            if inversion[0] in text_lower:
                return True
        
        # Check for Bangla question patterns without question mark
        bangla_patterns = [
            r'কি [ক-হ]*[া-ৌ]*\s',
            r'কেন [ক-হ]*[া-ৌ]*\s',
            r'কখন [ক-হ]*[া-ৌ]*\s',
            r'কোথায় [ক-হ]*[া-ৌ]*\s',
            r'কেমন [ক-হ]*[া-ৌ]*\s',
        ]
        
        for pattern in bangla_patterns:
            if re.search(pattern, text):
                return True
        
        # Check sentence length and structure
        words = text_lower.split()
        if len(words) <= 10:  # Short sentences are more likely to be questions
            # Check for question intonation words
            question_intonation = ['please', 'tell me', 'explain', 'describe']
            for word in question_intonation:
                if word in text_lower:
                    return True
        
        return False
    
    async def _determine_question_type(self, text: str) -> str:
        """Determine the type of question"""
        text_lower = text.lower()
        
        # Information questions
        info_patterns = {
            'what': ['what', 'কি', 'ماذا', 'کیا'],
            'why': ['why', 'কেন', 'لماذا', 'کیوں'],
            'when': ['when', 'কখন', 'متى', 'کب'],
            'where': ['where', 'কোথায়', 'أين', 'کہاں'],
            'how': ['how', 'কেমন', 'كيف'],
            'who': ['who', 'কে', 'من', 'کون'],
        }
        
        for q_type, keywords in info_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return q_type
        
        # Yes/No questions
        yesno_indicators = ['is', 'are', 'am', 'was', 'were', 'do', 'does', 'did',
                           'can', 'could', 'will', 'would', 'should', 'has', 'have']
        
        for indicator in yesno_indicators:
            if f'{indicator} ' in text_lower:
                return 'yesno'
        
        # Choice questions
        choice_indicators = ['or', 'বা', 'أو', 'یا']
        for indicator in choice_indicators:
            if f' {indicator} ' in text_lower:
                return 'choice'
        
        # Default
        return 'general'
    
    async def _is_help_request(self, text: str) -> bool:
        """Check if text is a help request"""
        text_lower = text.lower()
        
        help_keywords = [
            'help', 'সাহায্য', 'مساعدة', 'مدد',
            'assist', 'aid', 'support',
            'how to', 'কিভাবে', 'كيفية',
            'problem', 'issue', 'সমস্যা', 'مشكلة',
            'trouble', 'difficulty', 'কষ্ট',
            'don\'t know', 'জানি না', 'لا أعرف',
            'confused', 'দ্বিধা', 'مشوش',
        ]
        
        for keyword in help_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    async def extract_question_parts(self, text: str) -> Dict[str, Any]:
        """Extract parts of a question"""
        result = {
            'original_text': text,
            'is_question': False,
            'confidence': 0.0,
            'question_type': None,
            'question_word': None,
            'subject': None,
            'main_action': None,
            'is_help_request': False,
        }
        
        # Detect if it's a question
        is_question, confidence, q_type = await self.detect(text)
        
        if not is_question:
            return result
        
        result['is_question'] = True
        result['confidence'] = confidence
        result['question_type'] = q_type
        
        # Check if it's a help request
        result['is_help_request'] = await self._is_help_request(text)
        
        # Extract question word
        text_lower = text.lower()
        
        # Find question words
        all_question_words = []
        for lang_words in self.question_words.values():
            all_question_words.extend(lang_words)
        
        for q_word in all_question_words:
            if q_word in text_lower:
                result['question_word'] = q_word
                break
        
        # Simple subject extraction (for demonstration)
        # In real implementation, use NLP
        words = text.split()
        if len(words) > 1:
            # Try to find subject (word after question word or first noun)
            if result['question_word']:
                try:
                    q_word_index = text_lower.find(result['question_word'])
                    if q_word_index != -1:
                        # Get words after question word
                        after_q = text[q_word_index + len(result['question_word']):].strip()
                        if after_q:
                            result['subject'] = after_q.split()[0]
                except:
                    pass
            
            # If no subject found, use second word as potential subject
            if not result['subject'] and len(words) >= 2:
                result['subject'] = words[1]
        
        # Extract main action/verb (simplified)
        action_words = ['is', 'are', 'do', 'does', 'did', 'can', 'could', 'will', 'would']
        for word in action_words:
            if f' {word} ' in f' {text_lower} ':
                result['main_action'] = word
                break
        
        return result
    
    async def analyze_conversation(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversation for questions"""
        questions = []
        
        for msg in messages:
            text = msg.get('text', '')
            if text:
                is_question, confidence, q_type = await self.detect(text)
                
                if is_question:
                    questions.append({
                        'text': text,
                        'confidence': confidence,
                        'type': q_type,
                        'timestamp': msg.get('timestamp'),
                        'user_id': msg.get('user_id'),
                    })
        
        # Analysis results
        analysis = {
            'total_messages': len(messages),
            'total_questions': len(questions),
            'question_rate': len(questions) / max(1, len(messages)),
            'questions_by_type': {},
            'recent_questions': questions[-10:] if questions else [],
        }
        
        # Group questions by type
        for q in questions:
            q_type = q.get('type', 'unknown')
            analysis['questions_by_type'][q_type] = analysis['questions_by_type'].get(q_type, 0) + 1
        
        return analysis
    
    async def get_detector_stats(self) -> Dict[str, Any]:
        """Get detector statistics"""
        return {
            'patterns_count': sum(len(patterns) for patterns in self.patterns.values()),
            'question_words_count': sum(len(words) for words in self.question_words.values()),
            'languages_supported': list(self.patterns.keys()),
            'confidence_scores': self.confidence_scores,
        }