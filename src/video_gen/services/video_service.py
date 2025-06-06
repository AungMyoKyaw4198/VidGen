"""
Service for handling video-related operations.
"""
import math
import random
from typing import List, Optional
import numpy as np
from PIL import Image
# Add compatibility layer
if not hasattr(Image, 'Resampling'):
    Image.Resampling = type('Resampling', (), {'LANCZOS': Image.ANTIALIAS})
from io import BytesIO
import requests
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import resize, fadein, fadeout
from moviepy.editor import concatenate_videoclips, vfx

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

            final_clip = self._apply_transitions(clips, transition_duration)
            self._write_video(final_clip, output_path)
            return True

        except Exception as e:
            print(f"Error creating video: {str(e)}")
            return False

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
        """Process a single image into a video clip.
        
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
        clip = ImageClip(img_array)
        
        return clip.fl(self._create_zoom_pan_effect).set_duration(duration)

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

    def _create_zoom_pan_effect(self, get_frame, t: float) -> np.ndarray:
        """Create zoom and pan effect for video frames.
        
        Args:
            get_frame: Function to get frame at time t
            t: Current time in seconds
            
        Returns:
            Processed frame as numpy array
        """
        img = Image.fromarray(get_frame(t))
        base_size = img.size
        
        # Slower zoom parameters
        zoom_start = 1.0
        zoom_end = 1.05  # Reduced zoom range for smoother effect
        zoom_ratio = zoom_start + (zoom_end - zoom_start) * (t / self.config.duration_per_image)
        
        # Calculate new size with zoom
        new_size = [
            math.ceil(img.size[0] * zoom_ratio),
            math.ceil(img.size[1] * zoom_ratio)
        ]
        
        # Ensure dimensions are even
        new_size[0] = new_size[0] + (new_size[0] % 2)
        new_size[1] = new_size[1] + (new_size[1] % 2)
        
        # Resize image with zoom
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Slower pan direction
        pan_start_x = 0 if random.random() < 0.5 else (new_size[0] - base_size[0])
        pan_start_y = 0 if random.random() < 0.5 else (new_size[1] - base_size[1])
        pan_end_x = (new_size[0] - base_size[0]) if pan_start_x == 0 else 0
        pan_end_y = (new_size[1] - base_size[1]) if pan_start_y == 0 else 0
        
        # Calculate current pan position with smoother interpolation
        current_x = pan_start_x + (pan_end_x - pan_start_x) * (t / self.config.duration_per_image)
        current_y = pan_start_y + (pan_end_y - pan_start_y) * (t / self.config.duration_per_image)
        
        # Crop the image at current pan position
        img = img.crop([
            int(current_x), int(current_y),
            int(current_x + base_size[0]), int(current_y + base_size[1])
        ]).resize(base_size, Image.Resampling.LANCZOS)
        
        result = np.array(img)
        img.close()
        return result

    def _apply_transitions(self, clips: List[ImageClip], 
                         transition_duration: float) -> ImageClip:
        """Apply transitions between video clips.
        
        Args:
            clips: List of video clips
            transition_duration: Duration of transitions in seconds
            
        Returns:
            Final video clip with transitions
        """
        transitions = [
            lambda c: vfx.fadein(c, transition_duration),
            lambda c: vfx.fadeout(c, transition_duration),
            lambda c: vfx.fadein(vfx.resize(c, lambda t: 1 + 0.1*t), transition_duration),
            lambda c: vfx.fadein(vfx.resize(c, lambda t: 1.1 - 0.1*t), transition_duration),
        ]
        
        final_clips = [clips[0]]
        for clip in clips[1:]:
            transition_func = random.choice(transitions)
            clip_with_transition = transition_func(clip)
            final_clips.append(clip_with_transition)
        
        return concatenate_videoclips(final_clips, method="compose")

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
            audio=False,
            threads=4,
            preset='medium'
        )
        print(f"Video created successfully at: {output_path}") 