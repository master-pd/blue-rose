#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Confidence Engine
Calculate confidence scores for responses
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfidenceEngine:
    """Confidence Scoring Engine"""
    
    def __init__(self):
        # Confidence factors and their weights
        self.factors = {
            'similarity': {
                'weight': 0.25,
                'description': 'Similarity to known patterns',
            },
            'context': {
                'weight': 0.20,
                'description': 'Contextual relevance',
            },
            'frequency': {
                'weight': 0.15,
                'description': 'Frequency of similar queries',
            },
            'recency': {
                'weight': 0.15,
                'description': 'Recency of similar patterns',
            },
            'completeness': {
                'weight': 0.10,
                'description': 'Completeness of information',
            },
            'user_feedback': {
                'weight': 0.10,
                'description': 'Historical user feedback',
            },
            'source_quality': {
                'weight': 0.05,
                'description': 'Quality of information source',
            },
        }
        
        # Minimum confidence thresholds
        self.thresholds = {
            'high_confidence': 0.8,
            'medium_confidence': 0.6,
            'low_confidence': 0.4,
            'minimum_response': 0.3,
        }
        
        # Confidence boost factors
        self.boost_factors = {
            'exact_match': 0.3,
            'previous_success': 0.2,
            'user_preference': 0.15,
            'time_relevance': 0.1,
        }
        
        # Confidence reduction factors
        self.reduction_factors = {
            'contradiction': 0.3,
            'low_frequency': 0.2,
            'outdated': 0.25,
            'user_rejection': 0.4,
        }
    
    async def calculate(self, query: str, response: str, 
                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculate confidence score for a response"""
        try:
            if not query or not response:
                return await self._low_confidence_result("Missing query or response")
            
            context = context or {}
            
            # Calculate individual factor scores
            factor_scores = {}
            
            # 1. Similarity score
            factor_scores['similarity'] = await self._calculate_similarity_score(query, response, context)
            
            # 2. Context score
            factor_scores['context'] = await self._calculate_context_score(query, response, context)
            
            # 3. Frequency score
            factor_scores['frequency'] = await self._calculate_frequency_score(query, response, context)
            
            # 4. Recency score
            factor_scores['recency'] = await self._calculate_recency_score(query, response, context)
            
            # 5. Completeness score
            factor_scores['completeness'] = await self._calculate_completeness_score(response)
            
            # 6. User feedback score
            factor_scores['user_feedback'] = await self._calculate_feedback_score(query, response, context)
            
            # 7. Source quality score
            factor_scores['source_quality'] = await self._calculate_source_score(response, context)
            
            # Calculate weighted total
            total_confidence = 0.0
            for factor, score in factor_scores.items():
                weight = self.factors.get(factor, {}).get('weight', 0.0)
                total_confidence += score * weight
            
            # Apply boosts
            boosts = await self._calculate_boosts(query, response, context)
            for boost_name, boost_value in boosts.items():
                if boost_name in self.boost_factors:
                    total_confidence += boost_value * self.boost_factors[boost_name]
            
            # Apply reductions
            reductions = await self._calculate_reductions(query, response, context)
            for reduction_name, reduction_value in reductions.items():
                if reduction_name in self.reduction_factors:
                    total_confidence -= reduction_value * self.reduction_factors[reduction_name]
            
            # Ensure confidence is between 0 and 1
            total_confidence = max(0.0, min(1.0, total_confidence))
            
            # Determine confidence level
            confidence_level = await self._determine_confidence_level(total_confidence)
            
            # Prepare result
            result = {
                'query': query,
                'response': response,
                'total_confidence': round(total_confidence, 3),
                'confidence_level': confidence_level,
                'factor_scores': {k: round(v, 3) for k, v in factor_scores.items()},
                'boosts': boosts,
                'reductions': reductions,
                'should_respond': total_confidence >= self.thresholds['minimum_response'],
                'calculation_time': datetime.now().isoformat(),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return await self._low_confidence_result(f"Calculation error: {e}")
    
    async def _calculate_similarity_score(self, query: str, response: str, 
                                        context: Dict[str, Any]) -> float:
        """Calculate similarity-based confidence"""
        # This would integrate with the similarity engine
        # For now, use a simple heuristic
        
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Check if response addresses query keywords
        query_words = set(query_lower.split())
        response_words = set(response_lower.split())
        
        if not query_words:
            return 0.5  # Default for empty queries
        
        # Calculate word overlap
        overlap = len(query_words.intersection(response_words))
        overlap_ratio = overlap / len(query_words)
        
        # Boost for question-answer match
        if query_lower.endswith('?') and not response_lower.endswith('?'):
            overlap_ratio = min(1.0, overlap_ratio * 1.2)
        
        return overlap_ratio
    
    async def _calculate_context_score(self, query: str, response: str,
                                     context: Dict[str, Any]) -> float:
        """Calculate context relevance score"""
        # Extract context information
        chat_history = context.get('chat_history', [])
        current_topic = context.get('current_topic', '')
        user_id = context.get('user_id')
        chat_id = context.get('chat_id')
        
        if not chat_history:
            return 0.5  # Default for no context
        
        # Check if response relates to recent conversation
        recent_messages = chat_history[-5:]  # Last 5 messages
        recent_text = ' '.join([msg.get('text', '') for msg in recent_messages])
        
        # Simple keyword matching with recent context
        response_lower = response.lower()
        recent_lower = recent_text.lower()
        
        matching_words = 0
        response_words = response_lower.split()
        
        for word in response_words:
            if len(word) > 3 and word in recent_lower:
                matching_words += 1
        
        # Calculate score
        if not response_words:
            return 0.5
        
        score = matching_words / len(response_words)
        
        # Boost for topic continuity
        if current_topic and any(word in response_lower for word in current_topic.split()):
            score = min(1.0, score * 1.1)
        
        return score
    
    async def _calculate_frequency_score(self, query: str, response: str,
                                       context: Dict[str, Any]) -> float:
        """Calculate frequency-based confidence"""
        # This would check how often similar queries are answered with similar responses
        # For now, use a simple heuristic
        
        query_length = len(query.split())
        response_length = len(response.split())
        
        # Ideal response length depends on query
        if query_length <= 3:  # Short query
            ideal_length = 10
        elif query_length <= 10:  # Medium query
            ideal_length = 20
        else:  # Long query
            ideal_length = 30
        
        # Calculate length similarity
        length_diff = abs(response_length - ideal_length)
        length_score = max(0.0, 1.0 - (length_diff / ideal_length))
        
        return length_score
    
    async def _calculate_recency_score(self, query: str, response: str,
                                     context: Dict[str, Any]) -> float:
        """Calculate recency-based confidence"""
        # Check if response contains recent information
        response_lower = response.lower()
        
        # Time-related words (indicating recency)
        time_words = {
            'today', 'now', 'recent', 'latest', 'current',
            'this week', 'this month', 'this year',
            'just', 'new', 'updated', 'fresh',
        }
        
        # Check for time indicators
        time_indicator_count = sum(1 for word in time_words if word in response_lower)
        
        # Calculate score (more time indicators = higher recency score)
        score = min(1.0, time_indicator_count * 0.2)
        
        # Default score if no time indicators
        if score == 0:
            score = 0.5
        
        return score
    
    async def _calculate_completeness_score(self, response: str) -> float:
        """Calculate completeness of response"""
        if not response:
            return 0.0
        
        response_lower = response.lower()
        
        # Check for completeness indicators
        completeness_indicators = {
            'positive': ['yes', 'no', 'okay', 'sure', 'alright', 'understand'],
            'negative': ['i don\'t know', 'not sure', 'maybe', 'perhaps', 'could be'],
        }
        
        # Check if response seems complete
        sentence_endings = ['.', '!', '?']
        has_ending = any(response.endswith(ending) for ending in sentence_endings)
        
        # Check response length
        word_count = len(response.split())
        
        # Calculate score
        score = 0.5  # Base score
        
        # Boost for sentence ending
        if has_ending:
            score += 0.2
        
        # Adjust for length
        if word_count >= 5:  # Reasonable length
            score += 0.1
        elif word_count <= 2:  # Too short
            score -= 0.2
        
        # Check for vague responses
        for vague in completeness_indicators['negative']:
            if vague in response_lower:
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _calculate_feedback_score(self, query: str, response: str,
                                      context: Dict[str, Any]) -> float:
        """Calculate score based on historical user feedback"""
        # This would check historical feedback for similar responses
        # For now, return a default score
        
        user_id = context.get('user_id')
        chat_id = context.get('chat_id')
        
        # In a real implementation, this would query a feedback database
        # For now, use a default score that can be adjusted based on context
        
        default_score = 0.7
        
        # Adjust based on user interaction history
        user_interaction = context.get('user_interaction_level', 'medium')
        if user_interaction == 'high':
            default_score += 0.1
        elif user_interaction == 'low':
            default_score -= 0.1
        
        return max(0.0, min(1.0, default_score))
    
    async def _calculate_source_score(self, response: str,
                                    context: Dict[str, Any]) -> float:
        """Calculate source quality score"""
        # This would check the source of the information
        # For now, use a simple heuristic
        
        response_lower = response.lower()
        
        # Check for confidence indicators in response
        confidence_indicators = {
            'high': ['certainly', 'definitely', 'absolutely', 'sure', 'confirmed'],
            'medium': ['probably', 'likely', 'perhaps', 'maybe', 'could be'],
            'low': ['unsure', 'not certain', 'don\'t know', 'maybe', 'possibly'],
        }
        
        # Check for source references
        source_indicators = ['according to', 'source:', 'reference:', 'study shows', 'research indicates']
        
        # Calculate base score
        score = 0.5
        
        # Adjust for confidence indicators
        for high_word in confidence_indicators['high']:
            if high_word in response_lower:
                score += 0.1
                break
        
        for low_word in confidence_indicators['low']:
            if low_word in response_lower:
                score -= 0.1
                break
        
        # Adjust for source references
        for source_word in source_indicators:
            if source_word in response_lower:
                score += 0.15
                break
        
        return max(0.0, min(1.0, score))
    
    async def _calculate_boosts(self, query: str, response: str,
                              context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence boost factors"""
        boosts = {}
        
        # 1. Exact match boost
        query_lower = query.lower()
        response_lower = response.lower()
        
        if query_lower in response_lower or response_lower in query_lower:
            boosts['exact_match'] = 1.0
        
        # 2. Previous success boost (from context)
        previous_success = context.get('previous_success_rate', 0.0)
        if previous_success > 0.7:
            boosts['previous_success'] = previous_success
        
        # 3. User preference boost
        user_preferences = context.get('user_preferences', {})
        preferred_topics = user_preferences.get('preferred_topics', [])
        
        response_words = set(response_lower.split())
        topic_matches = sum(1 for topic in preferred_topics if topic.lower() in response_words)
        
        if topic_matches > 0:
            boosts['user_preference'] = min(1.0, topic_matches * 0.3)
        
        # 4. Time relevance boost
        current_hour = datetime.now().hour
        time_relevant = False
        
        # Check if response is time-appropriate
        time_keywords = {
            'morning': range(5, 12),
            'afternoon': range(12, 17),
            'evening': range(17, 21),
            'night': range(21, 24) + list(range(0, 5)),
        }
        
        for time_of_day, hour_range in time_keywords.items():
            if current_hour in hour_range and time_of_day in response_lower:
                time_relevant = True
                break
        
        if time_relevant:
            boosts['time_relevance'] = 0.8
        
        return boosts
    
    async def _calculate_reductions(self, query: str, response: str,
                                  context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence reduction factors"""
        reductions = {}
        
        # 1. Contradiction reduction
        chat_history = context.get('chat_history', [])
        if len(chat_history) >= 2:
            # Check if response contradicts previous bot responses
            previous_bot_responses = [
                msg.get('text', '') for msg in chat_history[-3:] 
                if msg.get('from_bot', False)
            ]
            
            # Simple contradiction detection (would be more sophisticated in real implementation)
            response_lower = response.lower()
            for prev_response in previous_bot_responses:
                prev_lower = prev_response.lower()
                # Check for direct contradictions (yes/no, true/false)
                contradictions = [
                    ('yes', 'no'), ('no', 'yes'),
                    ('true', 'false'), ('false', 'true'),
                    ('right', 'wrong'), ('wrong', 'right'),
                ]
                
                for word1, word2 in contradictions:
                    if word1 in prev_lower and word2 in response_lower:
                        reductions['contradiction'] = 1.0
                        break
        
        # 2. Low frequency reduction
        query_frequency = context.get('query_frequency', 0)
        if query_frequency < 3:  # Rare query
            reductions['low_frequency'] = 0.5
        
        # 3. Outdated information reduction
        response_lower = response.lower()
        outdated_indicators = [
            'last year', 'years ago', 'old', 'outdated',
            'no longer', 'used to', 'previously',
        ]
        
        for indicator in outdated_indicators:
            if indicator in response_lower:
                reductions['outdated'] = 0.7
                break
        
        # 4. User rejection history
        user_rejection_rate = context.get('user_rejection_rate', 0.0)
        if user_rejection_rate > 0.5:  # High rejection rate
            reductions['user_rejection'] = user_rejection_rate
        
        return reductions
    
    async def _determine_confidence_level(self, confidence: float) -> str:
        """Determine confidence level based on score"""
        if confidence >= self.thresholds['high_confidence']:
            return 'high'
        elif confidence >= self.thresholds['medium_confidence']:
            return 'medium'
        elif confidence >= self.thresholds['low_confidence']:
            return 'low'
        else:
            return 'very_low'
    
    async def _low_confidence_result(self, reason: str) -> Dict[str, Any]:
        """Create a low confidence result"""
        return {
            'total_confidence': 0.1,
            'confidence_level': 'very_low',
            'should_respond': False,
            'error_reason': reason,
            'calculation_time': datetime.now().isoformat(),
        }
    
    async def compare_responses(self, query: str, responses: List[str],
                              context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Compare confidence scores for multiple responses"""
        if not query or not responses:
            return []
        
        results = []
        
        for response in responses:
            confidence_result = await self.calculate(query, response, context)
            results.append({
                'response': response,
                **confidence_result
            })
        
        # Sort by confidence (highest first)
        results.sort(key=lambda x: x['total_confidence'], reverse=True)
        
        return results
    
    async def get_best_response(self, query: str, responses: List[str],
                              context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Get the best response based on confidence"""
        if not query or not responses:
            return None
        
        compared = await self.compare_responses(query, responses, context)
        
        if compared and compared[0]['should_respond']:
            return compared[0]
        
        return None
    
    async def adjust_confidence(self, response_id: str, adjustment: float,
                              reason: str, user_id: Optional[int] = None):
        """Adjust confidence based on user feedback"""
        # This would update confidence in a database
        # For now, just log the adjustment
        
        logger.info(f"Confidence adjusted for response {response_id}: {adjustment} "
                   f"(reason: {reason}, user: {user_id})")
        
        # In a real implementation, this would update learning models
    
    async def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'factors': {k: v['weight'] for k, v in self.factors.items()},
            'thresholds': self.thresholds,
            'boost_factors': self.boost_factors,
            'reduction_factors': self.reduction_factors,
            'total_factors': len(self.factors),
        }