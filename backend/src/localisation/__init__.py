"""
EFL Agent Assistant Localisation Module

Provides comprehensive localisation and multi-language support for West African English
speakers in the logistics and shipping domain, with specific focus on Nigerian terminal
operations and cultural communication patterns.

Key Components:
- English language pack with logistics terminology
- West African English accent handling for voice recognition
- Culturally appropriate error messages
- Localisation middleware for dynamic language switching
- Voice command grammar documentation

Usage:
    from backend.src.localisation import english_pack, accent_handler, cultural_handler

    # Get logistics terminology
    status_desc = english_pack.get_status_description(ContainerStatus.AT_TERMINAL)

    # Handle West African pronunciation
    normalized_text, confidence = accent_handler.normalize_west_african_pronunciation(text)

    # Get culturally appropriate error messages
    error_msg = cultural_handler.get_cultural_error_message(ErrorContext.CONTAINER_NOT_FOUND)
"""

from .en import english_pack, EnglishLanguagePack, ContainerStatus, LogisticsTerminology
from .accent_handler import accent_handler, WestAfricanAccentHandler, PronunciationMapping, LocalTerminology
from .cultural_messages import cultural_handler, CulturalMessageHandler, ErrorContext, CulturalTone

__all__ = [
    # Language pack components
    'english_pack',
    'EnglishLanguagePack',
    'ContainerStatus',
    'LogisticsTerminology',

    # Accent handling components
    'accent_handler',
    'WestAfricanAccentHandler',
    'PronunciationMapping',
    'LocalTerminology',

    # Cultural message components
    'cultural_handler',
    'CulturalMessageHandler',
    'ErrorContext',
    'CulturalTone',
]
