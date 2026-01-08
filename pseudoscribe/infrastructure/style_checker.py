import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import time
import re

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

    async def check_realtime(
        self,
        text: str,
        target_characteristics: Dict[str, float],
        granularity: str = "text"
    ) -> Dict[str, Any]:
        """
        Perform real-time style checking with inline deviation detection.

        Args:
            text: The text to check
            target_characteristics: Target style characteristics to match
            granularity: Level of analysis - "text" (whole text) or "sentence" (per sentence)

        Returns:
            Dictionary containing inline deviations with positions and suggestions

        Raises:
            ValueError: If text is empty
        """
        start_time = time.time()

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        inline_deviations = []

        if granularity == "sentence":
            # Analyze at sentence level for better granularity
            sentences = self._split_into_sentences(text)
            current_pos = 0

            for sentence in sentences:
                if not sentence.strip():
                    current_pos += len(sentence)
                    continue

                # Find the start position of this sentence in the original text
                sentence_start = text.find(sentence, current_pos)
                if sentence_start == -1:
                    sentence_start = current_pos
                sentence_end = sentence_start + len(sentence)

                # Analyze this segment
                if hasattr(self.style_profiler, 'analyze_segment'):
                    segment_chars = await self.style_profiler.analyze_segment(sentence)
                else:
                    segment_chars = await self.style_profiler.analyze_text(sentence)

                # Check for deviations in this sentence
                sentence_deviations = self._detect_deviations(
                    target_characteristics,
                    segment_chars,
                    sentence_start,
                    sentence_end,
                    sentence
                )
                inline_deviations.extend(sentence_deviations)

                current_pos = sentence_end
        else:
            # Analyze the whole text at once
            actual_characteristics = await self.style_profiler.analyze_text(text)

            # Detect deviations for the entire text
            inline_deviations = self._detect_deviations(
                target_characteristics,
                actual_characteristics,
                0,
                len(text),
                text
            )

        processing_time_ms = (time.time() - start_time) * 1000

        return {
            "inline_deviations": inline_deviations,
            "processing_time_ms": processing_time_ms
        }

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences for granular analysis.

        Args:
            text: The text to split

        Returns:
            List of sentence strings
        """
        # Simple sentence splitting using regex
        sentence_pattern = r'[^.!?]+[.!?]+'
        sentences = re.findall(sentence_pattern, text)

        # Include any trailing text without punctuation
        remaining = text
        for sentence in sentences:
            remaining = remaining.replace(sentence, '', 1)
        if remaining.strip():
            sentences.append(remaining)

        return sentences

    def _detect_deviations(
        self,
        target: Dict[str, float],
        actual: Dict[str, float],
        start: int,
        end: int,
        text_segment: str
    ) -> List[Dict[str, Any]]:
        """
        Detect style deviations between target and actual characteristics.

        Args:
            target: Target style characteristics
            actual: Actual analyzed characteristics
            start: Start position in original text
            end: End position in original text
            text_segment: The text segment being analyzed

        Returns:
            List of deviation dictionaries with positions and details
        """
        deviations = []
        threshold = 0.1  # Minimum deviation to report

        for key in target:
            if key not in actual:
                continue

            deviation_value = abs(target[key] - actual[key])

            if deviation_value > threshold:
                severity = self.calculate_deviation_severity(deviation_value)
                suggestion = self._get_deviation_suggestion(key, target[key] - actual[key])

                deviations.append({
                    "start": start,
                    "end": end,
                    "type": key,
                    "severity": severity["level"],
                    "severity_score": severity["score"],
                    "deviation": target[key] - actual[key],
                    "message": f"{key.capitalize()} deviation: target {target[key]:.2f}, actual {actual[key]:.2f}",
                    "suggestion": suggestion
                })

        return deviations

    def _get_deviation_suggestion(self, characteristic: str, deviation: float) -> str:
        """
        Get a specific suggestion for a deviation type.

        Args:
            characteristic: The characteristic that deviated
            deviation: The deviation value (positive = target higher)

        Returns:
            Suggestion string
        """
        suggestions = {
            "complexity": {
                "higher": "Use more complex sentence structures and vocabulary.",
                "lower": "Simplify your sentences and use more common vocabulary."
            },
            "formality": {
                "higher": "Use more formal language and avoid contractions.",
                "lower": "Use more casual language and contractions."
            },
            "tone": {
                "higher": "Use more positive and upbeat language.",
                "lower": "Use more neutral or serious language."
            },
            "readability": {
                "higher": "Use shorter sentences and simpler words.",
                "lower": "Use more varied sentence structures and vocabulary."
            }
        }

        if characteristic in suggestions:
            direction = "higher" if deviation > 0 else "lower"
            return suggestions[characteristic][direction]

        return f"Adjust {characteristic} to better match the target style."

    def calculate_deviation_severity(self, deviation: float) -> Dict[str, Any]:
        """
        Calculate severity level and score for a deviation.

        Args:
            deviation: Absolute deviation value (0.0 to 1.0)

        Returns:
            Dictionary with 'level' (str) and 'score' (float)
        """
        # Normalize deviation to a score
        score = min(1.0, deviation / 0.7)  # Normalize so 0.7 deviation = max score

        if score < 0.3:
            level = "low"
        elif score < 0.6:
            level = "medium"
        elif score < 0.8:
            level = "high"
        else:
            level = "critical"

        return {"level": level, "score": score}

    def aggregate_severity(self, deviations: Dict[str, float]) -> Dict[str, Any]:
        """
        Aggregate severity across multiple deviation types.

        Args:
            deviations: Dictionary of characteristic -> deviation value

        Returns:
            Dictionary with overall severity and breakdown
        """
        breakdown = {}
        max_score = 0.0

        for characteristic, deviation in deviations.items():
            severity = self.calculate_deviation_severity(abs(deviation))
            breakdown[characteristic] = severity
            max_score = max(max_score, severity["score"])

        # Overall level based on the highest severity
        if max_score < 0.3:
            overall_level = "low"
        elif max_score < 0.6:
            overall_level = "medium"
        elif max_score < 0.8:
            overall_level = "high"
        else:
            overall_level = "critical"

        return {
            "overall_level": overall_level,
            "overall_score": max_score,
            "breakdown": breakdown
        }

    async def batch_check(
        self,
        content: str,
        profile_id: str
    ) -> Dict[str, Any]:
        """
        Perform batch style checking on content with severity ranking.

        Args:
            content: The content to check (typically a full document)
            profile_id: ID of the style profile to check against

        Returns:
            Dictionary containing issues ranked by severity and summary stats

        Raises:
            ValueError: If content is empty or profile not found
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        # Retrieve the profile
        profile = await self.style_profiler.retrieve_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile with ID {profile_id} not found")

        target_characteristics = profile["characteristics"]

        # Split content into paragraphs/sections for analysis
        paragraphs = self._split_into_paragraphs(content)

        all_issues = []
        overall_scores = []
        current_pos = 0

        for paragraph in paragraphs:
            if not paragraph.strip():
                current_pos += len(paragraph)
                continue

            # Find paragraph position
            para_start = content.find(paragraph, current_pos)
            if para_start == -1:
                para_start = current_pos
            para_end = para_start + len(paragraph)

            # Analyze this paragraph
            if hasattr(self.style_profiler, 'analyze_segment'):
                para_chars = await self.style_profiler.analyze_segment(paragraph)
            else:
                para_chars = await self.style_profiler.analyze_text(paragraph)

            # Calculate match score for this paragraph
            match_score, deviations = self._calculate_style_match(
                target_characteristics, para_chars
            )
            overall_scores.append(match_score)

            # Generate issues for significant deviations
            for char_type, deviation in deviations.items():
                if abs(deviation) > 0.1:  # Threshold for reporting
                    severity = self.calculate_deviation_severity(abs(deviation))
                    suggestions = self._generate_style_suggestions({char_type: deviation})

                    all_issues.append({
                        "location": {
                            "start": para_start,
                            "end": para_end
                        },
                        "severity_score": severity["score"],
                        "severity_level": severity["level"],
                        "type": char_type,
                        "deviation": deviation,
                        "description": f"{char_type.capitalize()} deviation: {deviation:+.2f}",
                        "suggestions": suggestions
                    })

            current_pos = para_end

        # Sort issues by severity (highest first)
        all_issues.sort(key=lambda x: x["severity_score"], reverse=True)

        # Calculate summary statistics
        issues_by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        issues_by_type = {}

        for issue in all_issues:
            level = issue["severity_level"]
            issues_by_severity[level] = issues_by_severity.get(level, 0) + 1

            issue_type = issue["type"]
            issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1

        overall_match = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0

        return {
            "issues": all_issues,
            "summary": {
                "total_issues": len(all_issues),
                "issues_by_severity": issues_by_severity,
                "issues_by_type": issues_by_type,
                "overall_match_score": overall_match
            }
        }

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """
        Split content into paragraphs for batch analysis.

        Args:
            content: The content to split

        Returns:
            List of paragraph strings
        """
        # Split on double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', content)
        return [p for p in paragraphs if p.strip()]
