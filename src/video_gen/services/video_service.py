"""
Service for handling video-related operations.
"""
import math
import random
from typing import List, Optional
import numpy as np
from PIL import Image
from moviepy.editor import concatenate_audioclips
# Add compatibility layer
if not hasattr(Image, 'Resampling'):
    Image.Resampling = type('Resampling', (), {'LANCZOS': Image.ANTIALIAS})
from io import BytesIO
import requests
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.VideoClip import ImageClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import resize, fadein, fadeout
from moviepy.editor import concatenate_videoclips, vfx, AudioFileClip
from pathlib import Path
import os
import time
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
import logging

from ..utils.config import Config


class VideoService:
    """Service for handling video operations."""

    def __init__(self, config: Config):
        """Initialize the video service.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self._setup_dimensions()

    def _setup_dimensions(self) -> None:
        """Set up video dimensions based on format."""
        if self.config.format == 'horizontal':
            self.width = 1920  # Full HD width
            self.height = 1080  # Full HD height
        else:  # vertical format
            self.width = 1080
            self.height = 1920

    def create_video(self, images: List[str], output_path: str,
                    duration_per_image: float = 2.0,
                    transition_duration: float = 1.0) -> bool:
        """Create video from images with transitions.
        
        Args:
            images: List of image URLs
            output_path: Path to save the output video
            duration_per_image: Duration for each image in seconds
            transition_duration: Duration of transitions in seconds
            
        Returns:
            bool: True if video creation was successful
        """
        try:
            if not images:
                print("No images available to create video")
                return False

            clips = self._create_clips(images, duration_per_image)
            if not clips:
                print("No valid images to create video")
                return False

            # Comment out transitions for now
            # final_clip = self._apply_transitions(clips, transition_duration)
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # Add audio to the video
            final_clip = self._add_audio(final_clip)
            
            self._write_video(final_clip, output_path)
            return True

        except Exception as e:
            print(f"Error creating video: {str(e)}")
            return False

    def _add_audio(self, video_clip: ImageClip) -> ImageClip:
        """Add background music and voice-over to the video.
        
        Args:
            video_clip: The video clip to add audio to
            
        Returns:
            Video clip with audio
        """
        try:
            # Get video duration
            video_duration = video_clip.duration
            
            # Load and process background audio
            bg_audio_path = Path("audio/background_audio/background_audio1.mp3")
            if bg_audio_path.exists():
                bg_audio = AudioFileClip(str(bg_audio_path))
                # Loop if shorter than video
                if bg_audio.duration < video_duration:
                    # Calculate how many times to loop
                    n_loops = int(video_duration / bg_audio.duration) + 1
                    # Create a list of the audio clip repeated n_loops times
                    bg_audio = concatenate_audioclips([bg_audio] * n_loops)
                # Cut if longer than video
                bg_audio = bg_audio.subclip(0, video_duration)
                # Set volume to 50%
                bg_audio = bg_audio.volumex(0.5)
            else:
                print("Warning: Background audio file not found")
                bg_audio = None
            
            # Load and process voice-over
            voice_path = Path("audio/voice_over/voice_over1.mp3")
            if voice_path.exists():
                voice = AudioFileClip(str(voice_path))
                # Loop if shorter than video
                if voice.duration < video_duration:
                    # Calculate how many times to loop
                    n_loops = int(video_duration / voice.duration) + 1
                    # Create a list of the audio clip repeated n_loops times
                    voice = concatenate_audioclips([voice] * n_loops)
                # Cut if longer than video
                voice = voice.subclip(0, video_duration)
            else:
                print("Warning: Voice-over file not found")
                voice = None
            
            # Combine audio tracks
            if bg_audio and voice:
                # Create a composite audio clip
                final_audio = CompositeAudioClip([bg_audio, voice])
                return video_clip.set_audio(final_audio)
            elif bg_audio:
                return video_clip.set_audio(bg_audio)
            elif voice:
                return video_clip.set_audio(voice)
            else:
                return video_clip
            
        except Exception as e:
            print(f"Error adding audio: {str(e)}")
            return video_clip

    def _create_clips(self, images: List[str], duration_per_image: float) -> List[ImageClip]:
        """Create video clips from images.
        
        Args:
            images: List of image URLs
            duration_per_image: Duration for each image in seconds
            
        Returns:
            List of video clips
        """
        clips = []
        for img_url in images:
            try:
                clip = self._process_image(img_url, duration_per_image)
                if clip:
                    clips.append(clip)
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                continue
        return clips

    def _process_image(self, img_url: str, duration: float) -> Optional[ImageClip]:
        """Process a single image into a video clip with zoom and pan effects.
        
        Args:
            img_url: URL of the image
            duration: Duration of the clip in seconds
            
        Returns:
            Processed video clip or None if processing fails
        """
        response = requests.get(img_url)
        img = Image.open(BytesIO(response.content))
        
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        img = self._resize_and_crop(img)
        img_array = np.array(img)
        clip = ImageClip(img_array).set_duration(duration)
        
        # Apply zoom effect
        zoom_factor = 1.1  # Maximum zoom level
        zoom_clip = clip.fx(vfx.resize, lambda t: 1 + (zoom_factor - 1) * t/duration)
        
        # Apply pan effect
        # Randomly choose pan direction
        pan_direction = random.choice(['left', 'right', 'up', 'down'])
        
        if pan_direction in ['left', 'right']:
            # Horizontal pan
            x_offset = lambda t: (t/duration) * (self.width * 0.1) if pan_direction == 'right' else -(t/duration) * (self.width * 0.1)
            y_offset = lambda t: 0
        else:
            # Vertical pan
            x_offset = lambda t: 0
            y_offset = lambda t: (t/duration) * (self.height * 0.1) if pan_direction == 'down' else -(t/duration) * (self.height * 0.1)
        
        # Apply the pan effect
        final_clip = zoom_clip.set_position(lambda t: (x_offset(t), y_offset(t)))
        
        return final_clip

    def _resize_and_crop(self, img: Image.Image) -> Image.Image:
        """Resize and crop image to maintain aspect ratio.
        
        Args:
            img: Input image
            
        Returns:
            Processed image
        """
        img_ratio = img.width / img.height
        target_ratio = self.width / self.height
        
        if img_ratio > target_ratio:  # Image is wider than target ratio
            new_width = int(self.height * img_ratio)
            img = img.resize((new_width, self.height), Image.Resampling.LANCZOS)
            left = (img.width - self.width) // 2
            img = img.crop((left, 0, left + self.width, self.height))
        else:  # Image is taller than target ratio
            new_height = int(self.width / img_ratio)
            img = img.resize((self.width, new_height), Image.Resampling.LANCZOS)
            top = (img.height - self.height) // 2
            img = img.crop((0, top, self.width, top + self.height))
        
        return img

    # def _apply_transitions(self, clips: List[ImageClip], 
    #                      transition_duration: float) -> ImageClip:
    #     """Apply transitions between video clips.
    #     
    #     Args:
    #         clips: List of video clips
    #         transition_duration: Duration of transitions in seconds
    #         
    #     Returns:
    #         Final video clip with transitions
    #     """
    #     transitions = [
    #         lambda c: vfx.fadein(c, transition_duration),
    #         lambda c: vfx.fadeout(c, transition_duration),
    #         lambda c: vfx.fadein(vfx.resize(c, lambda t: 1 + 0.1*t), transition_duration),
    #         lambda c: vfx.fadein(vfx.resize(c, lambda t: 1.1 - 0.1*t), transition_duration),
    #     ]
    #     
    #     final_clips = [clips[0]]
    #     for clip in clips[1:]:
    #         transition_func = random.choice(transitions)
    #         clip_with_transition = transition_func(clip)
    #         final_clips.append(clip_with_transition)
    #     
    #     return concatenate_videoclips(final_clips, method="compose")

    def _write_video(self, final_clip: ImageClip, output_path: str) -> None:
        """Write the final video to file.
        
        Args:
            final_clip: Final video clip
            output_path: Path to save the video
        """
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio=True,  # Enable audio
            threads=4,
            preset='medium'
        )
        print(f"Video created successfully at: {output_path}") 