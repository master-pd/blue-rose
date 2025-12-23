#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Similarity Engine
Calculate similarity between texts
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from collections import Counter
import math

logger = logging.getLogger(__name__)

class SimilarityEngine:
    """Text Similarity Calculation Engine"""
    
    def __init__(self):
        # Similarity methods
        self.methods = ['cosine', 'jaccard', 'levenshtein', 'combined']
        
        # Weight for combined similarity
        self.weights = {
            'cosine': 0.4,
            'jaccard': 0.3,
            'levenshtein': 0.3,
        }
        
        # Minimum similarity threshold
        self.min_similarity = 0.3
        
        # Cache for frequently calculated similarities
        self.similarity_cache = {}
        self.cache_size = 1000
    
    async def calculate(self, text1: str, text2: str, 
                       method: str = 'combined') -> float:
        """Calculate similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Check cache
        cache_key = f"{text1[:50]}_{text2[:50]}_{method}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # Clean texts
        clean1 = await self._clean_text(text1)
        clean2 = await self._clean_text(text2)
        
        # Calculate similarity based on method
        similarity = 0.0
        
        if method == 'cosine':
            similarity = await self._cosine_similarity(clean1, clean2)
        elif method == 'jaccard':
            similarity = await self._jaccard_similarity(clean1, clean2)
        elif method == 'levenshtein':
            similarity = await self._levenshtein_similarity(clean1, clean2)
        elif method == 'combined':
            similarity = await self._combined_similarity(clean1, clean2)
        else:
            logger.warning(f"Unknown similarity method: {method}")
            similarity = await self._combined_similarity(clean1, clean2)
        
        # Cache result
        self._add_to_cache(cache_key, similarity)
        
        return similarity
    
    async def _clean_text(self, text: str) -> str:
        """Clean text for similarity calculation"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs, mentions, hashtags
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove special characters but keep letters and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity"""
        # Get word frequencies
        vec1 = Counter(text1.split())
        vec2 = Counter(text2.split())
        
        # Get all unique words
        words = set(vec1.keys()) | set(vec2.keys())
        
        # Create vectors
        vec1_list = [vec1.get(word, 0) for word in words]
        vec2_list = [vec2.get(word, 0) for word in words]
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1_list, vec2_list))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1_list))
        magnitude2 = math.sqrt(sum(b * b for b in vec2_list))
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        return similarity
    
    async def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity"""
        # Convert to sets of words
        set1 = set(text1.split())
        set2 = set(text2.split())
        
        # Avoid division by zero
        if not set1 and not set2:
            return 1.0  # Both are empty
        if not set1 or not set2:
            return 0.0  # One is empty
        
        # Calculate intersection and union
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        # Jaccard similarity
        similarity = intersection / union
        
        return similarity
    
    async def _levenshtein_similarity(self, text1: str, text2: str) -> float:
        """Calculate Levenshtein distance-based similarity"""
        # Implementation of Levenshtein distance
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        # Convert to lowercase for case-insensitive comparison
        text1 = text1.lower()
        text2 = text2.lower()
        
        # Initialize matrix
        len1, len2 = len(text1), len(text2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 1.0
        
        # Create matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if text1[i - 1] == text2[j - 1] else 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,      # deletion
                    matrix[i][j - 1] + 1,      # insertion
                    matrix[i - 1][j - 1] + cost  # substitution
                )
        
        # Calculate similarity
        distance = matrix[len1][len2]
        similarity = 1 - (distance / max_len)
        
        return max(0.0, similarity)  # Ensure non-negative
    
    async def _combined_similarity(self, text1: str, text2: str) -> float:
        """Calculate combined similarity using multiple methods"""
        # Calculate individual similarities
        cosine_sim = await self._cosine_similarity(text1, text2)
        jaccard_sim = await self._jaccard_similarity(text1, text2)
        levenshtein_sim = await self._levenshtein_similarity(text1, text2)
        
        # Weighted combination
        combined = (
            self.weights['cosine'] * cosine_sim +
            self.weights['jaccard'] * jaccard_sim +
            self.weights['levenshtein'] * levenshtein_sim
        )
        
        return combined
    
    def _add_to_cache(self, key: str, value: float):
        """Add similarity to cache"""
        # Limit cache size
        if len(self.similarity_cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO)
            if self.similarity_cache:
                oldest_key = next(iter(self.similarity_cache))
                del self.similarity_cache[oldest_key]
        
        self.similarity_cache[key] = value
    
    async def find_similar(self, query: str, texts: List[str], 
                          threshold: float = 0.5) -> List[Tuple[str, float]]:
        """Find texts similar to query"""
        if not query or not texts:
            return []
        
        similarities = []
        
        for text in texts:
            similarity = await self.calculate(query, text, 'combined')
            if similarity >= threshold:
                similarities.append((text, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities
    
    async def find_most_similar(self, query: str, texts: List[str]) -> Optional[Tuple[str, float]]:
        """Find the most similar text to query"""
        if not query or not texts:
            return None
        
        best_similarity = -1.0
        best_text = None
        
        for text in texts:
            similarity = await self.calculate(query, text, 'combined')
            if similarity > best_similarity:
                best_similarity = similarity
                best_text = text
        
        if best_similarity >= self.min_similarity:
            return (best_text, best_similarity)
        
        return None
    
    async def cluster_similar_texts(self, texts: List[str], 
                                  threshold: float = 0.6) -> List[List[str]]:
        """Cluster similar texts together"""
        if not texts:
            return []
        
        clusters = []
        
        for text in texts:
            added = False
            
            # Try to add to existing cluster
            for cluster in clusters:
                # Check similarity with cluster representative (first text)
                if cluster:
                    similarity = await self.calculate(text, cluster[0], 'combined')
                    if similarity >= threshold:
                        cluster.append(text)
                        added = True
                        break
            
            # Create new cluster if not added
            if not added:
                clusters.append([text])
        
        return clusters
    
    async def calculate_similarity_matrix(self, texts: List[str]) -> List[List[float]]:
        """Calculate similarity matrix for multiple texts"""
        n = len(texts)
        matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            matrix[i][i] = 1.0  # Self-similarity
            for j in range(i + 1, n):
                similarity = await self.calculate(texts[i], texts[j], 'combined')
                matrix[i][j] = similarity
                matrix[j][i] = similarity  # Symmetric
        
        return matrix
    
    async def analyze_text_similarities(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze similarities in a set of messages"""
        if not messages:
            return {'error': 'No messages provided'}
        
        # Extract texts
        texts = [msg.get('text', '') for msg in messages if msg.get('text')]
        
        if len(texts) < 2:
            return {
                'total_texts': len(texts),
                'average_similarity': 0.0,
                'similarity_matrix': [],
                'clusters': [],
            }
        
        # Calculate similarity matrix
        matrix = await self.calculate_similarity_matrix(texts)
        
        # Calculate average similarity (excluding diagonal)
        total_similarity = 0.0
        count = 0
        
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                total_similarity += matrix[i][j]
                count += 1
        
        avg_similarity = total_similarity / count if count > 0 else 0.0
        
        # Cluster similar texts
        clusters = await self.cluster_similar_texts(texts, threshold=0.5)
        
        return {
            'total_texts': len(texts),
            'average_similarity': round(avg_similarity, 3),
            'similarity_matrix': matrix,
            'clusters': clusters,
            'cluster_count': len(clusters),
            'largest_cluster': max(len(c) for c in clusters) if clusters else 0,
        }
    
    async def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'methods': self.methods,
            'weights': self.weights,
            'min_similarity': self.min_similarity,
            'cache_size': len(self.similarity_cache),
            'max_cache_size': self.cache_size,
        }