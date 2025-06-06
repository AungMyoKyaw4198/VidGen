"""
Configuration settings for the video generator.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass
class Config:
    """Configuration settings for video generation."""
    
    mode: Literal['test', 'production'] = 'test'
    format: Literal['horizontal', 'vertical'] = 'horizontal'
    duration_per_image: float = 2.0
    transition_duration: float = 1.0
    output_fps: int = 24
    video_codec: str = 'libx264'
    video_preset: str = 'medium'
    threads: int = 4 