"""
Blue Rose Bot - Intelligence Module
AI and smart response system
"""

__version__ = "1.0.0"
__author__ = "RANA (MASTER)"

from .message_collector import MessageCollector
from .question_detector import QuestionDetector
from .keyword_extractor import KeywordExtractor
from .similarity_engine import SimilarityEngine
from .confidence_engine import ConfidenceEngine
from .memory_builder import MemoryBuilder
from .memory_decay import MemoryDecay

__all__ = [
    'MessageCollector',
    'QuestionDetector',
    'KeywordExtractor',
    'SimilarityEngine',
    'ConfidenceEngine',
    'MemoryBuilder',
    'MemoryDecay',
]