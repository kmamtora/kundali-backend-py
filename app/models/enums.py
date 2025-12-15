"""
Enumerations for the application.
"""

from enum import Enum


class VoiceCallStatus(str, Enum):
    """Status of a voice call."""
    
    INITIATE_ROOM = "INITIATE_ROOM"
    CALLING = "CALLING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    MISSED = "MISSED"
    CANCELLED = "CANCELLED"
