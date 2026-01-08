import logging
import uuid
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, UTC

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

    def _calculate_semantic_similarity(
        self, vec1: np.ndarray, vec2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0

        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(max(0.0, min(1.0, similarity)))

    async def adapt_with_quality_check(
        self, text: str, profile_id: str
    ) -> Dict[str, Any]:
        """
        Adapt text to match a style profile with quality validation.

        This method performs style adaptation and validates that:
        1. Semantic meaning is preserved
        2. Style matches target profile
        3. Output is natural and flows well

        Args:
            text: The text to adapt
            profile_id: The ID of the target style profile

        Returns:
            Dictionary containing adapted text, quality metrics, and validation status

        Raises:
            ValueError: If text is empty or profile not found
        """
        start_time = time.time()

        if not text:
            raise ValueError("Text cannot be empty")

        logger.info(f"Adapting text with quality check for profile {profile_id}")

        # Retrieve the target profile
        target_profile = await self.style_profiler.retrieve_profile(profile_id)
        if not target_profile:
            raise ValueError(f"Profile with ID {profile_id} not found")

        target_characteristics = target_profile["characteristics"]

        # Check the current style match
        check_result = await self.style_checker.check_style_against_profile(text, profile_id)

        # If the match is already high, no need to adapt
        if check_result["overall_match"] > 0.9:
            processing_time = (time.time() - start_time) * 1000
            return {
                "original_text": text,
                "adapted_text": text,
                "style_match": check_result["overall_match"],
                "semantic_similarity": 1.0,
                "naturalness_score": 1.0,
                "quality_passed": True,
                "quality_issues": {},
                "profile_id": profile_id,
                "was_adapted": False,
                "processing_time_ms": processing_time
            }

        # Generate adaptation prompt and adapt
        adaptation_prompt = self._generate_adaptation_prompt(text, check_result["suggestions"])
        adapted_text = await self.model_manager.generate_text(
            prompt=adaptation_prompt,
            max_tokens=len(text) * 2,
            temperature=0.7
        )

        # Get embeddings for semantic similarity check
        original_embedding = await self.model_manager.generate_vectors(text)
        adapted_embedding = await self.model_manager.generate_vectors(adapted_text)

        semantic_similarity = self._calculate_semantic_similarity(
            original_embedding, adapted_embedding
        )

        # Check adapted text style match
        adapted_check = await self.style_checker.check_style_against_profile(
            adapted_text, profile_id
        )

        # Calculate naturalness score (based on readability similarity)
        naturalness_score = self._calculate_naturalness(text, adapted_text)

        # Determine if quality passes
        quality_issues = {}
        quality_passed = True

        if semantic_similarity < 0.5:
            quality_issues["semantic_similarity"] = semantic_similarity
            quality_passed = False

        if adapted_check["overall_match"] < 0.7:
            quality_issues["style_match"] = adapted_check["overall_match"]
            quality_passed = False

        if naturalness_score < 0.5:
            quality_issues["naturalness"] = naturalness_score
            quality_passed = False

        processing_time = (time.time() - start_time) * 1000

        return {
            "original_text": text,
            "adapted_text": adapted_text,
            "style_match": adapted_check["overall_match"],
            "semantic_similarity": semantic_similarity,
            "naturalness_score": naturalness_score,
            "quality_passed": quality_passed,
            "quality_issues": quality_issues,
            "profile_id": profile_id,
            "was_adapted": True,
            "processing_time_ms": processing_time
        }

    def _calculate_naturalness(self, original: str, adapted: str) -> float:
        """
        Calculate a naturalness score for adapted text.

        Assesses how natural the adapted text flows compared to the original.

        Args:
            original: Original text
            adapted: Adapted text

        Returns:
            Naturalness score (0.0 to 1.0)
        """
        # Simple heuristics for naturalness:
        # 1. Similar length (not too much expansion/contraction)
        # 2. Similar sentence count
        # 3. No excessive punctuation or unusual patterns

        original_len = len(original)
        adapted_len = len(adapted)

        # Length ratio (penalize extreme changes)
        if original_len == 0:
            return 0.5

        length_ratio = min(original_len, adapted_len) / max(original_len, adapted_len)

        # Sentence count comparison
        original_sentences = original.count('.') + original.count('!') + original.count('?')
        adapted_sentences = adapted.count('.') + adapted.count('!') + adapted.count('?')

        if max(original_sentences, adapted_sentences) > 0:
            sentence_ratio = min(original_sentences + 1, adapted_sentences + 1) / max(original_sentences + 1, adapted_sentences + 1)
        else:
            sentence_ratio = 1.0

        # Combined naturalness score
        naturalness = (length_ratio * 0.6 + sentence_ratio * 0.4)

        return float(max(0.0, min(1.0, naturalness)))

    async def validate_quality(
        self,
        original_text: str,
        adapted_text: str,
        target_characteristics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Validate the quality of an adapted text.

        Args:
            original_text: The original text before adaptation
            adapted_text: The adapted text to validate
            target_characteristics: Target style characteristics

        Returns:
            Dictionary containing quality validation results
        """
        # Get style match
        style_result = await self.style_checker.check_style_against_target_characteristics(
            adapted_text, target_characteristics
        )
        style_match = style_result["overall_match"]

        # Get semantic similarity
        original_embedding = await self.model_manager.generate_vectors(original_text)
        adapted_embedding = await self.model_manager.generate_vectors(adapted_text)
        semantic_similarity = self._calculate_semantic_similarity(
            original_embedding, adapted_embedding
        )

        # Calculate naturalness
        naturalness_score = self._calculate_naturalness(original_text, adapted_text)

        # Calculate overall quality (weighted average)
        overall_quality = (
            style_match * 0.4 +
            semantic_similarity * 0.4 +
            naturalness_score * 0.2
        )

        # Determine if quality passes thresholds
        passed = (
            style_match >= 0.7 and
            semantic_similarity >= 0.5 and
            naturalness_score >= 0.4
        )

        return {
            "style_match": style_match,
            "semantic_similarity": semantic_similarity,
            "naturalness_score": naturalness_score,
            "overall_quality": overall_quality,
            "passed": passed
        }

    async def iterative_adapt(
        self,
        text: str,
        profile_id: str,
        max_iterations: int = 3,
        quality_threshold: float = 0.85
    ) -> Dict[str, Any]:
        """
        Iteratively adapt text until quality threshold is met or max iterations reached.

        Args:
            text: The text to adapt
            profile_id: The ID of the target style profile
            max_iterations: Maximum number of adaptation attempts
            quality_threshold: Quality score to achieve before stopping

        Returns:
            Dictionary containing final adapted text and iteration details

        Raises:
            ValueError: If text is empty or profile not found
        """
        if not text:
            raise ValueError("Text cannot be empty")

        # Retrieve the target profile
        target_profile = await self.style_profiler.retrieve_profile(profile_id)
        if not target_profile:
            raise ValueError(f"Profile with ID {profile_id} not found")

        target_characteristics = target_profile["characteristics"]

        current_text = text
        best_result = None
        best_quality = 0.0
        iterations_used = 0
        early_stopped = False

        for i in range(max_iterations):
            iterations_used = i + 1

            # Check current style match
            check_result = await self.style_checker.check_style_against_profile(
                current_text, profile_id
            )
            current_quality = check_result["overall_match"]

            # Track best result
            if current_quality > best_quality:
                best_quality = current_quality
                best_result = current_text

            # Check if we've met the threshold
            if current_quality >= quality_threshold:
                early_stopped = True
                break

            # Generate adaptation
            adaptation_prompt = self._generate_adaptation_prompt(
                current_text, check_result["suggestions"]
            )
            adapted_text = await self.model_manager.generate_text(
                prompt=adaptation_prompt,
                max_tokens=len(current_text) * 2,
                temperature=0.7
            )

            # Verify semantic similarity is maintained
            original_embedding = await self.model_manager.generate_vectors(text)
            adapted_embedding = await self.model_manager.generate_vectors(adapted_text)
            semantic_similarity = self._calculate_semantic_similarity(
                original_embedding, adapted_embedding
            )

            # Only use adaptation if meaning is preserved
            if semantic_similarity >= 0.5:
                current_text = adapted_text

        # Final quality check
        final_check = await self.style_checker.check_style_against_profile(
            current_text, profile_id
        )
        final_quality = final_check["overall_match"]

        if final_quality > best_quality:
            best_result = current_text
            best_quality = final_quality

        return {
            "original_text": text,
            "adapted_text": best_result or text,
            "iterations_used": iterations_used,
            "early_stopped": early_stopped,
            "final_quality": best_quality,
            "profile_id": profile_id
        }

    # Feedback and learning storage (in-memory for now, would use persistence in production)
    _feedback_store: Dict[str, Dict[str, Any]] = {}
    _adaptation_stats: Dict[str, Dict[str, Any]] = {}

    async def record_feedback(
        self,
        adaptation_id: str,
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record feedback for an adaptation.

        Args:
            adaptation_id: ID of the adaptation
            feedback: Feedback dictionary containing ratings and comments

        Returns:
            Confirmation of recorded feedback
        """
        StyleAdapter._feedback_store[adaptation_id] = {
            "feedback": feedback,
            "recorded_at": datetime.now(UTC).isoformat()
        }

        logger.info(f"Recorded feedback for adaptation {adaptation_id}")

        return {
            "recorded": True,
            "adaptation_id": adaptation_id
        }

    async def get_adaptation_stats(
        self,
        profile_id: str
    ) -> Dict[str, Any]:
        """
        Get adaptation statistics for a profile.

        Args:
            profile_id: The profile ID to get stats for

        Returns:
            Dictionary containing adaptation statistics
        """
        # Aggregate stats from feedback store
        total_adaptations = len(StyleAdapter._feedback_store)

        quality_ratings = [
            f["feedback"].get("quality_rating", 3)
            for f in StyleAdapter._feedback_store.values()
            if "feedback" in f and "quality_rating" in f["feedback"]
        ]

        average_quality = sum(quality_ratings) / len(quality_ratings) if quality_ratings else 0.0
        success_count = len([r for r in quality_ratings if r >= 4])
        success_rate = success_count / len(quality_ratings) if quality_ratings else 0.0

        return {
            "profile_id": profile_id,
            "total_adaptations": total_adaptations,
            "average_quality": average_quality,
            "success_rate": success_rate
        }

    async def get_adaptation_context(
        self,
        profile_id: str
    ) -> Dict[str, Any]:
        """
        Get learned adaptation context for a profile.

        Args:
            profile_id: The profile ID to get context for

        Returns:
            Dictionary containing learned preferences and context
        """
        # Analyze feedback to extract learned preferences
        positive_feedback = [
            f for f in StyleAdapter._feedback_store.values()
            if f.get("feedback", {}).get("quality_rating", 0) >= 4
        ]

        learned_preferences = {
            "prompt_effectiveness": len(positive_feedback) / max(len(StyleAdapter._feedback_store), 1),
            "preferred_styles": []
        }

        return {
            "profile_id": profile_id,
            "learned_preferences": learned_preferences,
            "feedback_count": len(StyleAdapter._feedback_store)
        }
