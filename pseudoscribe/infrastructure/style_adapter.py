import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class StyleAdapter:
    """
    StyleAdapter adapts text to match a specific style profile or characteristics.
    
    This class provides functionality to:
    1. Adapt text to match a target style profile
    2. Adapt text to match target style characteristics
    3. Generate prompts for style adaptation
    
    The StyleAdapter uses the StyleProfiler to retrieve profiles, StyleChecker to
    check style matches, and ModelManager to generate adapted text.
    """
    
    def __init__(self, style_profiler, style_checker, model_manager):
        """
        Initialize the StyleAdapter.
        
        Args:
            style_profiler: The style profiler instance used for retrieving profiles
            style_checker: The style checker instance used for checking style matches
            model_manager: The model manager instance used for generating text
        """
        self.style_profiler = style_profiler
        self.style_checker = style_checker
        self.model_manager = model_manager
    
    async def adapt_text_to_profile(self, text: str, profile_id: str) -> Dict[str, Any]:
        """
        Adapt text to match a specific style profile.
        
        Args:
            text: The text to adapt
            profile_id: The ID of the target style profile
            
        Returns:
            Dictionary containing original text, adapted text, and style match info
            
        Raises:
            ValueError: If text is empty or profile not found
        """
        if not text:
            raise ValueError("Text cannot be empty")
            
        logger.info(f"Adapting text to match style profile {profile_id}")
        
        # Retrieve the target profile
        target_profile = await self.style_profiler.retrieve_profile(profile_id)
        if not target_profile:
            raise ValueError(f"Profile with ID {profile_id} not found")
            
        # Check the current style match
        check_result = await self.style_checker.check_style_against_profile(text, profile_id)
        
        # If the match is already high, no need to adapt
        if check_result["overall_match"] > 0.9:
            logger.info("Text already matches the target style profile closely")
            return {
                "original_text": text,
                "adapted_text": text,
                "style_match": check_result["overall_match"],
                "profile_id": profile_id,
                "was_adapted": False
            }
            
        # Generate a prompt for adaptation based on the style suggestions
        adaptation_prompt = self._generate_adaptation_prompt(text, check_result["suggestions"])
        
        # Generate adapted text
        adapted_text = await self.model_manager.generate_text(
            prompt=adaptation_prompt,
            max_tokens=len(text) * 2,  # Allow for some expansion
            temperature=0.7  # Some creativity but not too much
        )
        
        # Check the adapted text's style match
        adapted_check = await self.style_checker.check_style_against_profile(
            adapted_text, profile_id
        )
        
        return {
            "original_text": text,
            "adapted_text": adapted_text,
            "style_match": adapted_check["overall_match"],
            "profile_id": profile_id,
            "was_adapted": True
        }
    
    async def adapt_text_to_characteristics(
        self, text: str, target_characteristics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Adapt text to match target style characteristics.
        
        Args:
            text: The text to adapt
            target_characteristics: The target style characteristics
            
        Returns:
            Dictionary containing original text, adapted text, and style match info
            
        Raises:
            ValueError: If text is empty or target characteristics invalid
        """
        if not text:
            raise ValueError("Text cannot be empty")
            
        if not target_characteristics:
            raise ValueError("Target characteristics cannot be empty")
            
        logger.info("Adapting text to match target style characteristics")
        
        # Check the current style match
        check_result = await self.style_checker.check_style_against_target_characteristics(
            text, target_characteristics
        )
        
        # If the match is already high, no need to adapt
        if check_result["overall_match"] > 0.9:
            logger.info("Text already matches the target style characteristics closely")
            return {
                "original_text": text,
                "adapted_text": text,
                "style_match": check_result["overall_match"],
                "target_characteristics": target_characteristics,
                "was_adapted": False
            }
            
        # Generate a prompt for adaptation based on the style suggestions
        adaptation_prompt = self._generate_adaptation_prompt(text, check_result["suggestions"])
        
        # Generate adapted text
        adapted_text = await self.model_manager.generate_text(
            prompt=adaptation_prompt,
            max_tokens=len(text) * 2,  # Allow for some expansion
            temperature=0.7  # Some creativity but not too much
        )
        
        # Check the adapted text's style match
        adapted_check = await self.style_checker.check_style_against_target_characteristics(
            adapted_text, target_characteristics
        )
        
        return {
            "original_text": text,
            "adapted_text": adapted_text,
            "style_match": adapted_check["overall_match"],
            "target_characteristics": target_characteristics,
            "was_adapted": True
        }
    
    def _generate_adaptation_prompt(self, text: str, suggestions: List[str]) -> str:
        """
        Generate a prompt for the model to adapt text.
        
        Args:
            text: The original text to adapt
            suggestions: List of style suggestions
            
        Returns:
            A prompt string for the model
        """
        prompt = (
            "Please rewrite the following text to match the specified style guidelines. "
            "Maintain the original meaning and content, but adapt the style as described.\n\n"
            "Original text:\n"
            f"{text}\n\n"
            "Style guidelines:\n"
        )
        
        for i, suggestion in enumerate(suggestions, 1):
            prompt += f"{i}. {suggestion}\n"
            
        prompt += (
            "\nRewritten text (maintain the original meaning but follow the style guidelines):"
        )
        
        return prompt
