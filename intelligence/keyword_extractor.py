#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Keyword Extractor
Extract keywords and topics from messages
"""

import re
import logging
from typing import Dict, Any, List, Set, Optional
from collections import Counter

logger = logging.getLogger(__name__)

class KeywordExtractor:
    """Keyword Extraction System"""
    
    def __init__(self):
        # Stop words for different languages
        self.stop_words = {
            'english': {
                'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
                'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
                'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
                'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
                'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
                'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
                'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while',
                'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
                'into', 'through', 'during', 'before', 'after', 'above', 'below',
                'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
                'under', 'again', 'further', 'then', 'once', 'here', 'there',
                'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
                'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
                'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
                's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
            },
            'bangla': {
                'আমি', 'তুমি', 'সে', 'আমরা', 'তোমরা', 'তারা', 'এই', 'যে',
                'কি', 'কেন', 'কখন', 'কোথায়', 'কেমন', 'কে', 'কাকে',
                'এবং', 'বা', 'কিন্তু', 'যদি', 'তবে', 'কারণ', 'যেমন',
                'এর', 'এ', 'ও', 'তে', 'য়ে', 'র', 'টা', 'টি', 'খানা',
                'গুলো', 'গুলি', 'একটি', 'একটা', 'কয়েকটি', 'কয়েকটা',
                'সব', 'সমস্ত', 'কোন', 'কিছু', 'অনেক', 'কিছুনা',
                'হয়', 'হচ্ছে', 'হয়েছে', 'হবে', 'করেছে', 'করছি',
                'করবেন', 'করো', 'কর', 'হও', 'হবেন', 'হয়ো',
            },
            'urdu': {
                'میں', 'تم', 'وہ', 'ہم', 'آپ', 'یہ', 'وہ', 'کہ', 'کیا',
                'کون', 'کس', 'کب', 'کہاں', 'کیوں', 'کیسے', 'اور', 'یا',
                'لیکن', 'اگر', 'تو', 'کیونکہ', 'جیسے', 'کا', 'کی', 'کے',
                'کو', 'پر', 'سے', 'تک', 'تھا', 'تھی', 'تھے', 'ہے', 'ہیں',
                'ہو', 'ہوا', 'ہوئی', 'ہوئے', 'ہوں', 'ہیں', 'ہوگا', 'ہوگی',
                'ہوں گے', 'کر', 'کرتا', 'کرتی', 'کرتے', 'کیا', 'کریں',
            }
        }
        
        # Common phrases and their categories
        self.common_phrases = {
            'greeting': ['hello', 'hi', 'hey', 'সালাম', 'হ্যালো', 'আসসালামুয়ালাইকুম', 'سلام', 'مرحبا'],
            'thanks': ['thanks', 'thank you', 'ধন্যবাদ', 'শুকরিয়া', 'شکریہ', 'شكرا'],
            'bye': ['bye', 'goodbye', 'বিদায়', 'খোদা হাফিজ', 'الوداع', 'خدا حافظ'],
            'help': ['help', 'সাহায্য', 'মদদ', 'مساعدة', 'مدد'],
            'question': ['what', 'why', 'when', 'where', 'how', 'কি', 'কেন', 'কখন', 'কোথায়', 'কেমন'],
        }
        
        # Minimum word length for keywords
        self.min_word_length = 3
        
    async def extract(self, text: str, language: str = 'auto') -> Dict[str, Any]:
        """Extract keywords from text"""
        if not text or not isinstance(text, str):
            return {'keywords': [], 'categories': [], 'entities': []}
        
        # Detect language if auto
        if language == 'auto':
            language = await self._detect_language(text)
        
        # Clean text
        cleaned_text = await self._clean_text(text)
        
        # Extract words
        words = await self._extract_words(cleaned_text, language)
        
        # Remove stop words
        filtered_words = await self._filter_stop_words(words, language)
        
        # Count frequencies
        word_freq = Counter(filtered_words)
        
        # Get top keywords
        top_keywords = await self._get_top_keywords(word_freq)
        
        # Categorize keywords
        categories = await self._categorize_keywords(top_keywords)
        
        # Extract entities (simple version)
        entities = await self._extract_entities(text)
        
        return {
            'original_text': text,
            'language': language,
            'keywords': top_keywords,
            'categories': categories,
            'entities': entities,
            'word_count': len(words),
            'keyword_count': len(top_keywords),
        }
    
    async def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        # Simple character-based detection
        text_lower = text.lower()
        
        # Check for Bangla characters
        bangla_range = range(0x0980, 0x09FF)
        if any(ord(char) in bangla_range for char in text):
            return 'bangla'
        
        # Check for Arabic/Persian/Urdu characters
        arabic_range = range(0x0600, 0x06FF)
        if any(ord(char) in arabic_range for char in text):
            return 'urdu'  # Default to Urdu for Arabic script
        
        # Check for English (default)
        english_chars = sum(1 for char in text if 'a' <= char <= 'z' or 'A' <= char <= 'Z')
        if english_chars > len(text) * 0.3:  # At least 30% English characters
            return 'english'
        
        # Default to English
        return 'english'
    
    async def _clean_text(self, text: str) -> str:
        """Clean text for keyword extraction"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove mentions and hashtags
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove special characters but keep language-specific characters
        # Keep letters, numbers, and spaces
        text = re.sub(r'[^\w\s\u0980-\u09FF\u0600-\u06FF]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text.lower()
    
    async def _extract_words(self, text: str, language: str) -> List[str]:
        """Extract words from text"""
        if not text:
            return []
        
        # Split by whitespace
        words = text.split()
        
        # Filter by minimum length
        filtered_words = [
            word for word in words 
            if len(word) >= self.min_word_length
        ]
        
        return filtered_words
    
    async def _filter_stop_words(self, words: List[str], language: str) -> List[str]:
        """Filter out stop words"""
        if language not in self.stop_words:
            language = 'english'
        
        stop_words_set = self.stop_words.get(language, set())
        
        filtered_words = [
            word for word in words
            if word.lower() not in stop_words_set
        ]
        
        return filtered_words
    
    async def _get_top_keywords(self, word_freq: Counter, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top keywords by frequency"""
        top_items = word_freq.most_common(top_n)
        
        keywords = []
        for word, freq in top_items:
            keywords.append({
                'word': word,
                'frequency': freq,
                'length': len(word),
            })
        
        return keywords
    
    async def _categorize_keywords(self, keywords: List[Dict[str, Any]]) -> List[str]:
        """Categorize keywords"""
        categories = set()
        
        for keyword_info in keywords:
            word = keyword_info['word'].lower()
            
            # Check common phrases
            for category, phrases in self.common_phrases.items():
                if word in phrases or any(phrase in word for phrase in phrases):
                    categories.add(category)
            
            # Additional categorization based on word patterns
            if await self._is_greeting(word):
                categories.add('greeting')
            elif await self._is_question_word(word):
                categories.add('question')
            elif await self._is_emotion_word(word):
                categories.add('emotion')
            elif await self._is_time_word(word):
                categories.add('time')
            elif await self._is_location_word(word):
                categories.add('location')
        
        return list(categories)
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract simple entities from text"""
        entities = []
        
        # Extract potential names (title case words)
        words = text.split()
        for i, word in enumerate(words):
            if word.istitle() and len(word) > 2:
                # Check if it's likely a name (not at start of sentence)
                if i > 0 or not text[0].isupper():
                    entities.append({
                        'text': word,
                        'type': 'person',
                        'position': i,
                    })
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\b', text)
        for num in numbers:
            entities.append({
                'text': num,
                'type': 'number',
            })
        
        # Extract dates (simple patterns)
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, text)
            for date in dates:
                entities.append({
                    'text': date,
                    'type': 'date',
                })
        
        return entities
    
    async def _is_greeting(self, word: str) -> bool:
        """Check if word is a greeting"""
        greeting_words = {'hello', 'hi', 'hey', 'hola', 'namaste', 'salam', 'hiya'}
        return word.lower() in greeting_words
    
    async def _is_question_word(self, word: str) -> bool:
        """Check if word is a question word"""
        question_words = {'what', 'why', 'when', 'where', 'how', 'who', 'whom', 'which'}
        return word.lower() in question_words
    
    async def _is_emotion_word(self, word: str) -> bool:
        """Check if word is emotion-related"""
        emotion_words = {
            'happy', 'sad', 'angry', 'excited', 'bored', 'tired',
            'good', 'bad', 'great', 'awesome', 'terrible',
            'love', 'hate', 'like', 'dislike',
        }
        return word.lower() in emotion_words
    
    async def _is_time_word(self, word: str) -> bool:
        """Check if word is time-related"""
        time_words = {
            'today', 'tomorrow', 'yesterday', 'now', 'later',
            'morning', 'afternoon', 'evening', 'night',
            'day', 'week', 'month', 'year', 'hour', 'minute',
        }
        return word.lower() in time_words
    
    async def _is_location_word(self, word: str) -> bool:
        """Check if word is location-related"""
        location_words = {
            'here', 'there', 'where', 'place', 'location',
            'home', 'office', 'school', 'college',
            'city', 'country', 'world',
        }
        return word.lower() in location_words
    
    async def batch_extract(self, texts: List[str], language: str = 'auto') -> List[Dict[str, Any]]:
        """Extract keywords from multiple texts"""
        results = []
        
        for text in texts:
            result = await self.extract(text, language)
            results.append(result)
        
        return results
    
    async def analyze_conversation_keywords(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze keywords in a conversation"""
        all_keywords = []
        keyword_freq = Counter()
        
        for msg in messages:
            text = msg.get('text', '')
            if text:
                result = await self.extract(text)
                keywords = [kw['word'] for kw in result['keywords']]
                all_keywords.extend(keywords)
        
        # Count overall frequencies
        keyword_freq.update(all_keywords)
        
        # Get most common keywords
        top_keywords = keyword_freq.most_common(20)
        
        # Analyze keyword trends
        keyword_trends = {}
        for keyword, freq in top_keywords:
            # Find when keyword was used
            timestamps = []
            for msg in messages:
                text = msg.get('text', '')
                if text and keyword in text.lower():
                    timestamps.append(msg.get('timestamp'))
            
            keyword_trends[keyword] = {
                'frequency': freq,
                'first_used': min(timestamps) if timestamps else None,
                'last_used': max(timestamps) if timestamps else None,
                'used_count': len(timestamps),
            }
        
        return {
            'total_messages': len(messages),
            'total_keywords': len(all_keywords),
            'unique_keywords': len(keyword_freq),
            'top_keywords': top_keywords,
            'keyword_trends': keyword_trends,
            'keyword_density': len(all_keywords) / max(1, sum(len(msg.get('text', '').split()) for msg in messages)),
        }
    
    async def get_extractor_stats(self) -> Dict[str, Any]:
        """Get extractor statistics"""
        return {
            'languages_supported': list(self.stop_words.keys()),
            'stop_words_count': {lang: len(words) for lang, words in self.stop_words.items()},
            'common_phrases_categories': list(self.common_phrases.keys()),
            'min_word_length': self.min_word_length,
        }