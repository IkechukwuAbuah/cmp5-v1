"""
West African English Accent Handler for Voice Recognition
Handles pronunciation variations, local vocabulary, and cultural communication patterns
specific to West African English speakers, particularly in the Nigerian logistics context.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PronunciationMapping:
    """Mapping for pronunciation variations in West African English."""
    standard_form: str
    west_african_variants: List[str]
    confidence_boost: float = 1.0


@dataclass
class LocalTerminology:
    """Local terminology and their standard equivalents."""
    local_term: str
    standard_terms: List[str]
    context: str
    usage_frequency: float = 1.0


class WestAfricanAccentHandler:
    """Handles West African English accent variations for voice recognition."""

    def __init__(self):
        self.pronunciation_mappings = self._initialize_pronunciation_mappings()
        self.local_terminology = self._initialize_local_terminology()
        self.cultural_patterns = self._initialize_cultural_patterns()

    def _initialize_pronunciation_mappings(self) -> Dict[str, PronunciationMapping]:
        """Initialize pronunciation mappings for common logistics terms."""
        return {
            "container": PronunciationMapping(
                standard_form="container",
                west_african_variants=["containah", "containa", "konteyna"],
                confidence_boost=1.3
            ),
            "terminal": PronunciationMapping(
                standard_form="terminal",
                west_african_variants=["terminah", "terminali", "taminal"],
                confidence_boost=1.2
            ),
            "bill_of_lading": PronunciationMapping(
                standard_form="bill of lading",
                west_african_variants=["bill of laden", "bill of ladin", "BL"],
                confidence_boost=1.4
            ),
            "clearance": PronunciationMapping(
                standard_form="clearance",
                west_african_variants=["clearans", "klearans", "clear"],
                confidence_boost=1.2
            ),
            "examination": PronunciationMapping(
                standard_form="examination",
                west_african_variants=["examinashun", "examine", "exam"],
                confidence_boost=1.3
            ),
            "shipment": PronunciationMapping(
                standard_form="shipment",
                west_african_variants=["shipmont", "shipmenti", "ship"],
                confidence_boost=1.2
            ),
            "vessel": PronunciationMapping(
                standard_form="vessel",
                west_african_variants=["vessah", "vesseh", "ship"],
                confidence_boost=1.2
            ),
            "freight": PronunciationMapping(
                standard_form="freight",
                west_african_variants=["frait", "freit", "cargo"],
                confidence_boost=1.1
            ),
            "customs": PronunciationMapping(
                standard_form="customs",
                west_african_variants=["kustoms", "custom", "customi"],
                confidence_boost=1.3
            ),
            "documentation": PronunciationMapping(
                standard_form="documentation",
                west_african_variants=["dokyumentashun", "documents", "papers"],
                confidence_boost=1.2
            ),
        }

    def _initialize_local_terminology(self) -> Dict[str, LocalTerminology]:
        """Initialize local West African terminology mappings."""
        return {
            # Container and shipping terms
            "containah": LocalTerminology(
                local_term="containah",
                standard_terms=["container"],
                context="shipping",
                usage_frequency=0.9
            ),
            "bill of laden": LocalTerminology(
                local_term="bill of laden",
                standard_terms=["bill_of_lading", "bl"],
                context="documentation",
                usage_frequency=0.8
            ),
            "terminah": LocalTerminology(
                local_term="terminah",
                standard_terms=["terminal"],
                context="location",
                usage_frequency=0.9
            ),
            "kustoms": LocalTerminology(
                local_term="kustoms",
                standard_terms=["customs"],
                context="clearance",
                usage_frequency=0.95
            ),
            "clearans": LocalTerminology(
                local_term="clearans",
                standard_terms=["clearance"],
                context="clearance",
                usage_frequency=0.85
            ),
            "examinashun": LocalTerminology(
                local_term="examinashun",
                standard_terms=["examination"],
                context="inspection",
                usage_frequency=0.9
            ),
            # Local expressions
            "i dey find": LocalTerminology(
                local_term="i dey find",
                standard_terms=["i_am_looking_for", "track", "search"],
                context="query",
                usage_frequency=0.7
            ),
            "wetin be": LocalTerminology(
                local_term="wetin be",
                standard_terms=["what_is", "status"],
                context="query",
                usage_frequency=0.6
            ),
            "how far": LocalTerminology(
                local_term="how far",
                standard_terms=["hello", "status_update"],
                context="greeting",
                usage_frequency=0.8
            ),
            # Numbers and identifiers
            "EFLU": LocalTerminology(
                local_term="EFLU",
                standard_terms=["EFLU", "container_prefix"],
                context="container_id",
                usage_frequency=1.0
            ),
            "ABCD": LocalTerminology(
                local_term="ABCD",
                standard_terms=["ABCD", "bl_prefix"],
                context="bl_number",
                usage_frequency=1.0
            ),
        }

    def _initialize_cultural_patterns(self) -> Dict[str, Dict[str, float]]:
        """Initialize cultural communication patterns and their likelihoods."""
        return {
            "politeness_markers": {
                "please": 0.9,
                "sir": 0.7,
                "ma": 0.6,
                "oga": 0.8,
                "thank_you": 0.85,
                "god_bless": 0.5,
            },
            "indirect_requests": {
                "can_you_help_me": 0.8,
                "i_want_to_know": 0.7,
                "please_check": 0.75,
                "i_need_information": 0.6,
            },
            "repetition_patterns": {
                "double_confirmation": 0.8,  # "Yes, yes" pattern
                "slow_delivery": 0.6,       # Slower speech rate
                "emphasis_through_repetition": 0.7,
            }
        }

    def normalize_west_african_pronunciation(self, text: str, confidence_score: float = 1.0) -> Tuple[str, float]:
        """
        Normalize West African English pronunciation variations to standard forms.

        Args:
            text: Input text from speech recognition
            confidence_score: Original confidence score from speech recognition

        Returns:
            Tuple of (normalized_text, adjusted_confidence_score)
        """
        original_text = text.lower().strip()
        normalized_text = original_text
        confidence_adjustment = 0.0

        # Apply pronunciation mappings
        for standard_form, mapping in self.pronunciation_mappings.items():
            for variant in mapping.west_african_variants:
                if variant in normalized_text:
                    normalized_text = normalized_text.replace(variant, standard_form)
                    confidence_adjustment += mapping.confidence_boost * 0.1
                    logger.info(f"Pronunciation mapping applied: {variant} -> {standard_form}")

        # Apply local terminology mappings
        for local_term, terminology in self.local_terminology.items():
            if local_term in normalized_text:
                # Replace with most likely standard term
                best_match = max(
                    terminology.standard_terms,
                    key=lambda x: len(x) if x in normalized_text else 0
                )
                if best_match:
                    normalized_text = normalized_text.replace(local_term, best_match)
                    confidence_adjustment += terminology.usage_frequency * 0.15
                    logger.info(f"Local terminology mapping: {local_term} -> {best_match}")

        # Handle number sequences and container IDs
        normalized_text = self._normalize_container_ids(normalized_text)

        # Apply cultural pattern adjustments
        cultural_boost = self._apply_cultural_confidence_boost(normalized_text)
        confidence_adjustment += cultural_boost

        # Ensure confidence doesn't exceed 1.0
        adjusted_confidence = min(confidence_score + confidence_adjustment, 1.0)

        return normalized_text, adjusted_confidence

    def _normalize_container_ids(self, text: str) -> str:
        """Normalize container ID formats to standard forms."""
        # Handle EFL container format: EFL U 789 6543
        eflu_pattern = r'efl\s*u\s*(\d{3})\s*(\d{4})'
        text = re.sub(eflu_pattern, r'EFLU\1\2', text, flags=re.IGNORECASE)

        # Handle other common container formats
        container_patterns = [
            (r'([A-Z]{4})\s*(\d{7})', r'\1\2'),  # ABCD1234567
            (r'([A-Z]{3})\s*(\d{7})', r'\1\2'),   # ABC1234567
        ]

        for pattern, replacement in container_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def _apply_cultural_confidence_boost(self, text: str) -> float:
        """Apply confidence boost based on cultural communication patterns."""
        boost = 0.0
        text_lower = text.lower()

        # Politeness markers boost confidence
        for marker, weight in self.cultural_patterns["politeness_markers"].items():
            if marker in text_lower:
                boost += weight * 0.06  # Increased from 0.05

        # Indirect requests boost confidence (shows natural communication)
        for pattern, weight in self.cultural_patterns["indirect_requests"].items():
            if pattern.replace("_", " ") in text_lower:
                boost += weight * 0.04  # Increased from 0.03

        return boost

    def extract_container_numbers(self, text: str) -> List[str]:
        """Extract container numbers from West African English speech patterns."""
        containers = []

        # Standard EFL format: EFLU followed by 7 digits
        eflu_matches = re.findall(r'EFLU\s*(\d{7})', text, re.IGNORECASE)
        containers.extend([f"EFLU{match}" for match in eflu_matches])

        # EFL format with spaces: EFL U 789 6543 (word boundary to avoid partial matches)
        eflu_spaced_matches = re.findall(r'\bEFL\s*[Uu]\s*(\d{3})\s*(\d{4})\b', text, re.IGNORECASE)
        containers.extend([f"EFLU{match1}{match2}" for match1, match2 in eflu_spaced_matches])

        # Other container formats (with word boundaries to avoid partial matches)
        other_formats = [
            r'\b([A-Z]{4})(\d{7})\b',  # ABCD1234567
            r'\b([A-Z]{3})(\d{7})\b',  # ABC1234567
        ]

        for pattern in other_formats:
            matches = re.findall(pattern, text, re.IGNORECASE)
            containers.extend([f"{prefix}{number}" for prefix, number in matches])

        return list(set(containers))  # Remove duplicates

    def extract_bl_numbers(self, text: str) -> List[str]:
        """Extract BL numbers from West African English speech patterns."""
        bl_numbers = []

        # Common BL patterns - look for word boundaries to avoid partial matches
        bl_patterns = [
            r'BL\s+([A-Z0-9]{10,})',      # BL ABC1234567 (with space)
            r'BLN\s+([A-Z0-9]{10,})',     # BLN ABC1234567 (with space)
            r'\b([A-Z]{4})(\d{7})\b',     # ABCD1234567 (word boundary)
            r'\b([A-Z]{3})(\d{7})\b',     # ABC1234567 (word boundary)
        ]

        for pattern in bl_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, str):
                        # Single match (like BL ABC1234567)
                        bl_numbers.append(match)
                    elif len(match) == 2:
                        # Two-part match (like ABCD and 1234567)
                        bl_numbers.append(f"{match[0]}{match[1]}")

        return list(set(bl_numbers))  # Remove duplicates

    def detect_cultural_context(self, text: str) -> Dict[str, float]:
        """Detect cultural context indicators in the speech."""
        context_scores = {
            "west_african_english": 0.0,
            "nigerian_english": 0.0,
            "politeness_level": 0.0,
            "formality_level": 0.0,
        }

        text_lower = text.lower()

        # West African English indicators
        wa_indicators = [
            "containah", "terminah", "kustoms", "clearans",
            "examinashun", "shipmont", "dokyumentashun"
        ]

        for indicator in wa_indicators:
            if indicator in text_lower:
                context_scores["west_african_english"] += 0.3

        # Nigerian English specific indicators
        ng_indicators = [
            "oga", "how far", "i dey", "wetin", "no wahala",
            "god bless", "sir", "ma"
        ]

        for indicator in ng_indicators:
            if indicator in text_lower:
                context_scores["nigerian_english"] += 0.4

        # Politeness indicators
        politeness_markers = ["please", "sir", "ma", "thank you", "god bless"]
        for marker in politeness_markers:
            if marker in text_lower:
                context_scores["politeness_level"] += 0.2

        # Formality indicators
        formal_indicators = ["good day", "i would like", "could you please"]
        for indicator in formal_indicators:
            if indicator in text_lower:
                context_scores["formality_level"] += 0.15

        return context_scores

    def get_accent_specific_grammar_hints(self, cultural_context: Dict[str, float]) -> List[str]:
        """Get grammar hints based on detected cultural context."""
        hints = []

        if cultural_context.get("west_african_english", 0) > 0.5:
            hints.extend([
                "Expect pronunciation variations for logistics terms",
                "Local terminology may be used for containers and documents",
                "Politeness markers increase confidence",
            ])

        if cultural_context.get("nigerian_english", 0) > 0.6:
            hints.extend([
                "Nigerian Pidgin elements may be present",
                "High politeness context expected",
                "Container IDs may have EFL prefix pronunciation variations",
            ])

        return hints


# Singleton instance for easy import
accent_handler = WestAfricanAccentHandler()
