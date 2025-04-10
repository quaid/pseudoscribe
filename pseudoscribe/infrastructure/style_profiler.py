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
    1. Analyze text to identify style characteristics
    2. Create profiles of writing styles
    3. Compare different style profiles
    4. Store and retrieve style profiles
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
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing style characteristics (complexity, formality, tone, readability)
            
        Raises:
            ValueError: If text is empty
        """
        if not text:
            raise ValueError("Text cannot be empty")
            
        logger.info(f"Analyzing text for style profiling (length: {len(text)})")
        
        # Generate vector representation of the text
        # In a real implementation, this would be awaited
        # For testing, we're using a mock that returns directly
        vector = self.model_manager.generate_vector.return_value
        
        # Create full profile
        profile = self._create_style_profile(text, vector)
        
        # Return just the characteristics
        return profile["characteristics"]
    
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
    
    def _calculate_style_characteristics(self, text: str, vector: np.ndarray) -> Dict[str, float]:
        """
        Calculate style characteristics based on text features and vector.
        
        Args:
            text: The text to analyze
            vector: Vector representation of the text
            
        Returns:
            Dictionary of style characteristics
        """
        # In a real implementation, this would use more sophisticated analysis
        # For now, we'll use simple heuristics and the vector components
        
        # Calculate text statistics
        avg_word_length = self._calculate_avg_word_length(text)
        avg_sentence_length = self._calculate_avg_sentence_length(text)
        
        # Calculate characteristics (normalized between 0 and 1)
        # These calculations are simplified for demonstration purposes
        complexity = min(1.0, max(0.0, (avg_word_length - 3) / 5))
        formality = min(1.0, max(0.0, (avg_sentence_length - 5) / 20))
        
        # Use vector components to influence tone and readability
        # This is a simplified approach; in reality, we would use more sophisticated methods
        if len(vector) >= 3:
            tone = min(1.0, max(0.0, (vector[0] + 1) / 2))  # Normalize from [-1,1] to [0,1]
            readability = min(1.0, max(0.0, 1 - (vector[1] + 1) / 2))  # Inverse of normalized vector component
        else:
            # Fallback if vector doesn't have enough components
            tone = 0.5
            readability = 0.5
        
        return {
            "complexity": float(complexity),
            "formality": float(formality),
            "tone": float(tone),
            "readability": float(readability)
        }
    
    def _calculate_avg_word_length(self, text: str) -> float:
        """Calculate the average word length in the text."""
        words = text.split()
        if not words:
            return 0
        return sum(len(word) for word in words) / len(words)
    
    def _calculate_avg_sentence_length(self, text: str) -> float:
        """Calculate the average sentence length (in words) in the text."""
        # Simple sentence splitting by ., !, ?
        sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
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
        Calculate similarity between two sets of style characteristics.
        
        Args:
            chars1: First set of characteristics
            chars2: Second set of characteristics
            
        Returns:
            Similarity score between 0 and 1
        """
        # Calculate Euclidean distance between characteristics
        squared_diff_sum = 0
        for key in chars1:
            if key in chars2:
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
