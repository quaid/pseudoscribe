import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)

class StyleChecker:
    """
    StyleChecker checks if text matches a specific style profile and provides feedback.
    
    This class provides functionality to:
    1. Check if text matches a target style profile
    2. Identify style inconsistencies or deviations
    3. Provide feedback and suggestions for style improvements
    
    The StyleChecker uses the StyleProfiler to analyze text and compare it against
    target style characteristics or existing style profiles.
    """
    
    def __init__(self, style_profiler):
        """
        Initialize the StyleChecker.
        
        Args:
            style_profiler: The style profiler instance used for analyzing text
        """
        self.style_profiler = style_profiler
    
    async def check_style_against_profile(self, text: str, profile_id: str) -> Dict[str, Any]:
        """
        Check if text matches a specific style profile.
        
        Args:
            text: The text to check
            profile_id: The ID of the target style profile
            
        Returns:
            Dictionary containing match score, deviations, and suggestions
            
        Raises:
            ValueError: If text is empty or profile not found
        """
        if not text:
            raise ValueError("Text cannot be empty")
            
        logger.info(f"Checking text against style profile {profile_id}")
        
        # Retrieve the target profile
        target_profile = await self.style_profiler.retrieve_profile(profile_id)
        if not target_profile:
            raise ValueError(f"Profile with ID {profile_id} not found")
            
        # Get target characteristics
        target_characteristics = target_profile["characteristics"]
        
        # Analyze the text
        actual_characteristics = await self.style_profiler.analyze_text(text)
        
        # Calculate match score and deviations
        match_score, deviations = self._calculate_style_match(
            target_characteristics, actual_characteristics
        )
        
        # Generate suggestions based on deviations
        suggestions = self._generate_style_suggestions(deviations)
        
        return {
            "overall_match": float(match_score),
            "deviations": deviations,
            "suggestions": suggestions
        }
    
    async def check_style_against_target_characteristics(
        self, text: str, target_characteristics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Check if text matches target style characteristics.
        
        Args:
            text: The text to check
            target_characteristics: The target style characteristics
            
        Returns:
            Dictionary containing match score, deviations, and suggestions
            
        Raises:
            ValueError: If text is empty or target characteristics invalid
        """
        if not text:
            raise ValueError("Text cannot be empty")
            
        if not target_characteristics:
            raise ValueError("Target characteristics cannot be empty")
            
        logger.info("Checking text against target style characteristics")
        
        # Analyze the text
        actual_characteristics = await self.style_profiler.analyze_text(text)
        
        # Calculate match score and deviations
        match_score, deviations = self._calculate_style_match(
            target_characteristics, actual_characteristics
        )
        
        # Generate suggestions based on deviations
        suggestions = self._generate_style_suggestions(deviations)
        
        return {
            "overall_match": float(match_score),
            "deviations": deviations,
            "suggestions": suggestions
        }
    
    def _calculate_style_match(
        self, target_characteristics: Dict[str, float], actual_characteristics: Dict[str, float]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate how well the actual characteristics match the target.
        
        Args:
            target_characteristics: The target style characteristics
            actual_characteristics: The actual style characteristics
            
        Returns:
            Tuple of (match_score, deviations)
        """
        # Calculate deviations (positive means target is higher, negative means target is lower)
        deviations = {}
        for key in target_characteristics:
            if key in actual_characteristics:
                deviations[key] = target_characteristics[key] - actual_characteristics[key]
            else:
                logger.warning(f"Characteristic '{key}' not found in actual characteristics")
                deviations[key] = 0.0
                
        # Calculate match score based on deviations
        # Using a simple formula: match = 1 / (1 + sum of squared deviations)
        squared_deviations_sum = sum(deviation**2 for deviation in deviations.values())
        match_score = 1.0 / (1.0 + squared_deviations_sum)
        
        return float(match_score), deviations
    
    def _generate_style_suggestions(self, deviations: Dict[str, float]) -> List[str]:
        """
        Generate style improvement suggestions based on deviations.
        
        Args:
            deviations: Dictionary of style characteristic deviations
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # Only suggest changes for significant deviations
        threshold = 0.1
        
        # Complexity suggestions
        if "complexity" in deviations:
            if deviations["complexity"] > threshold:
                suggestions.append(
                    "Use more complex sentence structures and vocabulary to increase complexity."
                )
            elif deviations["complexity"] < -threshold:
                suggestions.append(
                    "Simplify your sentences and use more common vocabulary to reduce complexity."
                )
                
        # Formality suggestions
        if "formality" in deviations:
            if deviations["formality"] > threshold:
                suggestions.append(
                    "Use more formal language and avoid contractions to increase formality."
                )
            elif deviations["formality"] < -threshold:
                suggestions.append(
                    "Use more casual language and contractions to decrease formality."
                )
                
        # Tone suggestions
        if "tone" in deviations:
            if deviations["tone"] > threshold:
                suggestions.append(
                    "Use more positive and upbeat language to adjust the tone."
                )
            elif deviations["tone"] < -threshold:
                suggestions.append(
                    "Use more neutral or serious language to adjust the tone."
                )
                
        # Readability suggestions
        if "readability" in deviations:
            if deviations["readability"] > threshold:
                suggestions.append(
                    "Use shorter sentences and simpler words to improve readability."
                )
            elif deviations["readability"] < -threshold:
                suggestions.append(
                    "Use more varied sentence structures and vocabulary to decrease readability."
                )
                
        return suggestions
