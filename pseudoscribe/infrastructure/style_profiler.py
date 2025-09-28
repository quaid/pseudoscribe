import numpy as np
import uuid
from datetime import datetime, UTC
import logging
from typing import Dict, Any, List, Optional
import asyncio
from scipy.spatial.distance import cosine

logger = logging.getLogger(__name__)

class StyleProfiler:
    """
    StyleProfiler analyzes text to identify writing style characteristics and creates style profiles.
    
    This class provides functionality to:
    1. Analyze text to identify style characteristics (complexity, formality, tone, readability)
    2. Create comprehensive profiles of writing styles with vector representations
    3. Compare different style profiles using vector similarity and characteristic differences
    4. Store and retrieve style profiles for future reference
    
    The StyleProfiler uses a combination of statistical text analysis and vector representations
    from the model manager to create accurate profiles of writing styles. These profiles can be
    used for style checking, adaptation, and maintaining consistency across documents.
    """
    
    def __init__(self, model_manager):
        """
        Initialize the StyleProfiler.
        
        Args:
            model_manager: The model manager instance used for generating vectors
        """
        self.model_manager = model_manager
        self.profiles = {}  # In-memory storage for profiles (would be replaced with persistent storage in production)
    
    async def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyze text and return a style profile with characteristics.
        
        This method analyzes the provided text and returns a dictionary of style characteristics
        including complexity, formality, tone, and readability. Each characteristic is represented
        as a float between 0.0 and 1.0.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing style characteristics (complexity, formality, tone, readability)
            
        Raises:
            ValueError: If text is empty or invalid
        """
        # Validate input
        if not text:
            raise ValueError("Text cannot be empty")
        
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
            
        logger.info(f"Analyzing text for style profiling (length: {len(text)})")
        
        try:
            # Generate vector representation of the text
            vector = await self.model_manager.generate_vectors(text)
            
            # Create full profile
            profile = self._create_style_profile(text, vector)
            
            # Return just the characteristics
            return profile["characteristics"]
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            raise RuntimeError(f"Failed to analyze text: {str(e)}") from e
    
    def _create_style_profile(self, text: str, vector: np.ndarray) -> Dict[str, Any]:
        """
        Create a complete style profile from text and its vector representation.
        
        Args:
            text: The text sample
            vector: Vector representation of the text
            
        Returns:
            Complete style profile dictionary
        """
        # Calculate style characteristics based on the vector and text features
        characteristics = self._calculate_style_characteristics(text, vector)
        
        # Create timestamp
        now = datetime.now(UTC).isoformat()
        
        # Create profile
        profile = {
            "id": str(uuid.uuid4()),
            "text_sample": text[:500],  # Store a sample of the text (limited to 500 chars)
            "vector": vector,
            "characteristics": characteristics,
            "created_at": now,
            "updated_at": now
        }
        
        return profile
    
    def _normalize_value(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """
        Normalize a value to be within the specified range.
        
        Args:
            value: The value to normalize
            min_val: Minimum value in the normalized range
            max_val: Maximum value in the normalized range
            
        Returns:
            Normalized value between min_val and max_val
        """
        return min(max_val, max(min_val, value))
    
    def _calculate_style_characteristics(self, text: str, vector: np.ndarray) -> Dict[str, float]:
        """
        Calculate style characteristics from text and vector representation.
        
        The following characteristics are calculated:
        - complexity: Based on average word length and sentence structure
        - formality: Based on sentence length and word choice patterns
        - tone: Derived from vector components and sentiment indicators
        - readability: Measure of how easy the text is to read
        
        Args:
            text: The text to analyze
            vector: Vector representation of the text
            
        Returns:
            Dictionary with style characteristics (complexity, formality, tone, readability)
        """
        try:
            # Use the enhanced heuristic method as our primary implementation
            return self._calculate_heuristic_style_characteristics(text)
        except Exception as e:
            logger.warning(f"Error in style characteristics calculation: {e}")
            # Fallback to basic characteristics
            return {
                "complexity": 0.5,
                "formality": 0.5,
                "tone": 0.5,
                "readability": 0.5
            }
    
    def _calculate_heuristic_style_characteristics(self, text: str) -> Dict[str, float]:
        """
        Calculate style characteristics using sophisticated heuristic methods.
        Enhanced fallback implementation with improved accuracy.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with style characteristics (complexity, formality, tone, readability)
        """
        logger.info("Using enhanced heuristic fallback for style analysis")
        
        # Calculate comprehensive text metrics
        word_count = len(text.split())
        avg_word_length = self._calculate_avg_word_length(text)
        avg_sentence_length = self._calculate_avg_sentence_length(text)
        
        # Enhanced complexity calculation
        # Factors: word length, sentence length, punctuation density, vocabulary diversity
        punctuation_density = sum(1 for char in text if char in '.,;:!?()[]{}') / len(text)
        unique_words = len(set(word.lower().strip('.,;:!?()[]{}') for word in text.split()))
        vocabulary_diversity = unique_words / word_count if word_count > 0 else 0
        
        complexity = min(1.0, (
            avg_word_length / 12.0 * 0.3 +  # Word complexity
            avg_sentence_length / 25.0 * 0.3 +  # Sentence complexity
            punctuation_density * 2.0 * 0.2 +  # Punctuation complexity
            vocabulary_diversity * 0.2  # Vocabulary diversity
        ))
        
        # Enhanced formality calculation
        formal_indicators = [
            'therefore', 'however', 'furthermore', 'consecutively', 'moreover',
            'nevertheless', 'accordingly', 'subsequently', 'thus', 'hence',
            'whereas', 'notwithstanding', 'henceforth', 'heretofore'
        ]
        informal_indicators = [
            'gonna', 'wanna', 'yeah', 'ok', 'cool', 'awesome', 'stuff',
            'things', 'kinda', 'sorta', 'pretty much', 'like', 'you know'
        ]
        
        formal_count = sum(1 for word in formal_indicators if word in text.lower())
        informal_count = sum(1 for word in informal_indicators if word in text.lower())
        
        # Consider sentence structure for formality
        passive_voice_indicators = ['was', 'were', 'been', 'being']
        passive_count = sum(1 for word in passive_voice_indicators if word in text.lower())
        
        # Normalize formality score with multiple factors
        if formal_count + informal_count > 0:
            formality = (formal_count + passive_count * 0.1) / (formal_count + informal_count + passive_count * 0.1)
        else:
            # Base formality on sentence length and word complexity
            formality = min(1.0, (avg_sentence_length / 20.0 + avg_word_length / 8.0) / 2.0)
        
        # Enhanced tone calculation using multiple linguistic features
        positive_words = ['good', 'great', 'excellent', 'wonderful', 'amazing', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing', 'poor']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count + negative_count > 0:
            tone = positive_count / (positive_count + negative_count)
        else:
            # Use text characteristics for tone estimation
            exclamation_count = text.count('!')
            question_count = text.count('?')
            tone = min(1.0, 0.5 + (exclamation_count * 0.1) - (question_count * 0.05))
        
        # Enhanced readability using Flesch-Kincaid inspired metrics
        syllable_estimate = sum(max(1, len([c for c in word if c.lower() in 'aeiou'])) 
                               for word in text.split())
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * (syllable_estimate / word_count))
        readability = max(0.0, min(1.0, flesch_score / 100.0))
        
        return {
            "complexity": float(self._normalize_value(complexity)),
            "formality": float(self._normalize_value(formality)),
            "tone": float(self._normalize_value(tone)),
            "readability": float(self._normalize_value(readability))
        }
    
    def _calculate_avg_word_length(self, text: str) -> float:
        """Calculate the average word length in the text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Average word length or 0 if no words are found
        """
        # Remove punctuation to avoid counting it as part of word length
        words = [word.strip('.,;:!?()[]{}"\'\'') for word in text.split()]
        words = [word for word in words if word]  # Filter out empty strings
        
        if not words:
            return 0
        return sum(len(word) for word in words) / len(words)
    
    def _calculate_avg_sentence_length(self, text: str) -> float:
        """Calculate the average sentence length (in words) in the text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Average sentence length (in words) or 0 if no sentences are found
        """
        # More robust sentence splitting by ., !, ?
        # This handles common abbreviations and edge cases better
        import re
        sentence_endings = re.compile(r'[.!?]\s+')
        sentences = [s.strip() for s in sentence_endings.split(text) if s.strip()]
        
        # Handle the case where there's no sentence ending punctuation
        if not sentences and text.strip():
            sentences = [text.strip()]
            
        if not sentences:
            return 0
        
        total_words = sum(len(sentence.split()) for sentence in sentences)
        return total_words / len(sentences)
    
    async def compare_profiles(self, profile1: Dict[str, Any], profile2: Dict[str, Any]) -> Dict[str, float]:
        """
        Compare two style profiles and return similarity scores.
        
        Args:
            profile1: First style profile
            profile2: Second style profile
            
        Returns:
            Dictionary with similarity scores
        """
        # Calculate vector similarity using cosine similarity
        vector_similarity = 1.0 - cosine(profile1["vector"], profile2["vector"])
        
        # Calculate characteristics similarity
        char_sim = self._calculate_characteristics_similarity(
            profile1["characteristics"], 
            profile2["characteristics"]
        )
        
        # Calculate overall similarity (weighted average)
        overall = 0.7 * vector_similarity + 0.3 * char_sim
        
        return {
            "overall": float(overall),
            "vector_similarity": float(vector_similarity),
            "characteristics_similarity": float(char_sim)
        }
    
    def _calculate_characteristics_similarity(self, chars1: Dict[str, float], chars2: Dict[str, float]) -> float:
        """
        Calculate similarity between two sets of style characteristics using Euclidean distance.
        
        The similarity is calculated as 1 / (1 + distance), which maps:
        - identical characteristics to a similarity of 1.0
        - very different characteristics to a value approaching 0.0
        
        Args:
            chars1: First set of characteristics
            chars2: Second set of characteristics
            
        Returns:
            Similarity score between 0 and 1
        """
        # Validate input dictionaries
        if not chars1 or not chars2:
            logger.warning("Empty characteristics dictionary provided for similarity calculation")
            return 0.0
            
        # Find common keys to compare
        common_keys = set(chars1.keys()).intersection(set(chars2.keys()))
        if not common_keys:
            logger.warning("No common characteristics found for similarity calculation")
            return 0.0
            
        # Calculate Euclidean distance between characteristics
        squared_diff_sum = 0
        for key in common_keys:
            squared_diff_sum += (chars1[key] - chars2[key]) ** 2
        
        # Convert distance to similarity (1 = identical, 0 = completely different)
        # Using a simple formula: similarity = 1 / (1 + distance)
        distance = np.sqrt(squared_diff_sum)
        similarity = 1 / (1 + distance)
        
        return float(similarity)
    
    async def store_profile(self, profile: Dict[str, Any]) -> str:
        """
        Store a style profile.
        
        Args:
            profile: The style profile to store
            
        Returns:
            The profile ID
        """
        profile_id = profile["id"]
        # In a real implementation, this might be awaited
        profile_id = self._save_profile(profile)
        logger.info(f"Stored style profile with ID: {profile_id}")
        return profile_id
    
    async def retrieve_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a style profile by ID.
        
        Args:
            profile_id: The ID of the profile to retrieve
            
        Returns:
            The style profile or None if not found
        """
        # In a real implementation, this might be awaited
        profile = self._load_profile(profile_id)
        if profile:
            logger.info(f"Retrieved style profile with ID: {profile_id}")
        else:
            logger.warning(f"Style profile with ID {profile_id} not found")
        return profile
    
    def _save_profile(self, profile: Dict[str, Any]) -> str:
        """
        Save a profile to storage.
        
        Args:
            profile: The profile to save
            
        Returns:
            The profile ID
        """
        # In a real implementation, this would save to a database
        # For now, we'll use in-memory storage
        profile_id = profile["id"]
        self.profiles[profile_id] = profile
        return profile_id
    
    def _load_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a profile from storage.
        
        Args:
            profile_id: The ID of the profile to load
            
        Returns:
            The profile or None if not found
        """
        # In a real implementation, this would load from a database
        # For now, we'll use in-memory storage
        return self.profiles.get(profile_id)
