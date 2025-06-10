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
from moviepy.video.VideoClip import ImageClip, ColorClip, TextClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import resize, fadein, fadeout
from moviepy.editor import concatenate_videoclips, vfx, AudioFileClip
from moviepy.editor import VideoFileClip
from pathlib import Path
import os
import time
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
import logging

from ..utils.config import Config


class VideoService:
    """Service for handling video operations."""

    def __init__(self, config: Config, fps: int = 30):
        """Initialize the video service.
        
        Args:
            config: Configuration object
            fps: Frames per second for the video (default: 30)
        """
        self.config = config
        self.fps = fps
        self._setup_dimensions()
        self._setup_ffmpeg()

    def _setup_dimensions(self) -> None:
        """Set up video dimensions based on format."""
        if self.config.format == 'horizontal':
            self.width = 1920  # Full HD width
            self.height = 1080  # Full HD height
        else:  # vertical format
            self.width = 1080
            self.height = 1920

    def _setup_ffmpeg(self):
        """Set up FFmpeg configuration."""
        # ... existing code ...

    def _create_subtitle_clip(self, text: str, duration: float, size: tuple) -> VideoClip:
        """Create a subtitle clip with centered text.
        
        Args:
            text: The subtitle text
            duration: Duration of the subtitle
            size: Size of the video (width, height)
            
        Returns:
            VideoClip: The subtitle clip
        """
        # Calculate font size
        fontsize = int(size[1] * 0.10)  # 10% of video height
        
        # Create text clip
        text_clip = TextClip(
            text,
            fontsize=fontsize,
            color='white',
            font='Impact',
            stroke_color='black',
            stroke_width=3,
            method='caption'
        )
        
        # Center the text both horizontally and vertically
        x_pos = (size[0] - text_clip.w) // 2
        y_pos = (size[1] - text_clip.h) // 2
        
        # Position the clip
        text_clip = text_clip.set_position((x_pos, y_pos))
        text_clip = text_clip.set_duration(duration)
        
        return text_clip

        # Commented out highlight functionality for now
        """
        # Split text into words
        words = text.split()
        word_duration = 0.2  # 200ms per word
        total_time = 0
        
        # First, calculate total width of all words to center the sentence
        word_widths = []
        total_width = 0
        for word in words:
            # Create temporary clip to measure width
            temp_clip = TextClip(
                word,
                fontsize=base_fontsize,
                font='Impact',
                method='caption'
            )
            word_widths.append(temp_clip.w)
            total_width += temp_clip.w
        
        # Add spacing between words
        total_width += (len(words) - 1) * 20  # 20px spacing between words
        
        # Calculate starting x position to center the entire sentence
        start_x = (size[0] - total_width) // 2
        
        # Create clips for each word
        word_clips = []
        current_x = start_x  # Start from the calculated center position
        
        for i, word in enumerate(words):
            # Create normal word clip
            normal_clip = TextClip(
                word,
                fontsize=base_fontsize,
                color='white',
                font='Impact',
                stroke_color='black',
                stroke_width=3,
                method='caption'
            )
            
            # Create highlighted version
            highlight_clip = TextClip(
                word,
                fontsize=highlight_fontsize,
                color='yellow',
                font='Impact',
                stroke_color='black',
                stroke_width=3,
                method='caption'
            )
            
            # Position both clips
            y_pos = size[1] - 200  # 200px from bottom
            normal_clip = normal_clip.set_position((current_x, y_pos))
            highlight_clip = highlight_clip.set_position((current_x, y_pos))
            
            # Update x position for next word
            current_x += word_widths[i] + 20  # Add spacing between words
            
            # Set timing for both clips
            normal_clip = normal_clip.set_start(total_time + word_duration).set_duration(duration)
            highlight_clip = highlight_clip.set_start(total_time).set_duration(word_duration)
            
            # Add both clips to the list
            word_clips.extend([normal_clip, highlight_clip])
            
            # Update total time
            total_time += word_duration
        
        # Create the final composite clip
        final_clip = CompositeVideoClip(word_clips, size=size)
        final_clip = final_clip.set_duration(duration)
        
        return final_clip
        """

    def create_video(self, images: List[str], output_path: str,
                    duration_per_image: float = 2.0,
                    transition_duration: float = 1.0) -> bool:
        """Create video from images with transitions and YouTube clips.
        
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

            # Process images
            processed_images = []
            for img_path in images:
                processed_img = self._process_image(img_path, duration=duration_per_image)
                if processed_img is not None:
                    processed_images.append(processed_img)
            
            if not processed_images:
                print("No valid images to process")
                return False
            
            # Try to add YouTube clips if API key is available
            youtube_clips = []
            youtube_api_key = os.getenv('YOUTUBE_API_KEY')
            
            if youtube_api_key:
                try:
                    print("\nInitializing YouTube service...")
                    # Initialize YouTube service
                    from .youtube_service import YouTubeService
                    youtube_service = YouTubeService(api_key=youtube_api_key)
                    
                    # Search for YouTube videos
                    print("Searching for YouTube videos...")
                    videos = youtube_service.search_videos(
                        keywords="CR7 vacation training",
                        max_results=3,
                        max_duration=60,
                        min_views=1000
                    )
                    
                    print(f"Found {len(videos)} videos")
                    
                    # Print found videos
                    if videos:
                        print("\nFound YouTube videos:")
                        for video in videos:
                            print(f"- {video['title']} ({video['duration']}s, {video['views']} views)")
                            print(f"  URL: {video['url']}")
                        
                        # Download and process YouTube clips
                        print("\nProcessing YouTube clips...")
                        for i, video in enumerate(videos, 1):
                            print(f"\nProcessing video {i}/{len(videos)}")
                            # Download video
                            print(f"Downloading: {video['title']}")
                            video_path = youtube_service.download_video(video['url'])
                            if video_path:
                                print("Download successful")
                                # Extract 5-second clip
                                print("Extracting 5-second clip...")
                                clip_path = youtube_service.extract_clip(
                                    video_path,
                                    duration=5,
                                    start_time=None  # Start from middle
                                )
                                if clip_path:
                                    print("Clip extraction successful")
                                    # Load clip
                                    print("Loading clip...")
                                    clip = VideoFileClip(clip_path)
                                    # Resize to match video dimensions
                                    print("Resizing clip...")
                                    clip = clip.resize(width=processed_images[0].w)
                                    youtube_clips.append(clip)
                                    print("Clip added to final video")
                            else:
                                print("Download failed")
                    
                    # Clean up YouTube temporary files
                    print("\nCleaning up temporary files...")
                    youtube_service.cleanup()
                    
                except Exception as e:
                    print(f"\nWarning: Could not process YouTube videos: {str(e)}")
                    print("Continuing with image-only video...")
            
            # Create video clip using concatenate_videoclips
            video_clip = concatenate_videoclips(processed_images, method="compose")
            
            # Add YouTube clips between images if available
            if youtube_clips:
                final_clips = []
                for i, img_clip in enumerate(processed_images):
                    final_clips.append(img_clip)
                    if i < len(youtube_clips):
                        final_clips.append(youtube_clips[i])
                
                video_clip = concatenate_videoclips(final_clips, method="compose")
            
            # Add audio
            video_clip = self._add_audio(video_clip)
            
            # Create subtitles for each image
            subtitle_clips = []
            duration_per_image = video_clip.duration / len(processed_images)
            
            # Test subtitles for each image
            test_subtitles = [
                "Welcome to the Wonderful World of Oz!",
                "Follow the Yellow Brick Road",
                "Subscribe you bastards"
            ]
            
            # Create subtitle clips
            for i, subtitle in enumerate(test_subtitles):
                start_time = i * duration_per_image
                subtitle_clip = self._create_subtitle_clip(
                    subtitle,
                    duration_per_image,
                    (video_clip.w, video_clip.h)
                )
                subtitle_clip = subtitle_clip.set_start(start_time)
                subtitle_clips.append(subtitle_clip)
            
            # Combine video with subtitles
            final_clip = CompositeVideoClip([video_clip] + subtitle_clips)
            
            # Write video file with verbose=False to suppress MoviePy's output
            final_clip.write_videofile(output_path, 
                                     fps=self.fps,
                                     codec='libx264',
                                     audio_codec='aac',
                                     temp_audiofile='temp-audio.m4a',
                                     remove_temp=True,
                                     verbose=False,
                                     logger=None)
            
            # Close all clips
            for clip in youtube_clips:
                clip.close()
            final_clip.close()
            
            print(f"\nVideo created successfully at: {output_path}")
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

    def _process_image(self, image_path: str, duration: float = 2.0) -> Optional[VideoClip]:
        """Process a single image into a video clip.
        
        Args:
            image_path: Path to the image file
            duration: Duration of the clip in seconds
            
        Returns:
            Optional[VideoClip]: Processed video clip or None if processing fails
        """
        try:
            # Load and process image
            response = requests.get(image_path)
            img = Image.open(BytesIO(response.content))
            
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Resize and crop image
            img = self._resize_and_crop(img)
            
            # Convert to numpy array and create clip
            img_array = np.array(img)
            clip = ImageClip(img_array).set_duration(duration)
            
            # Add zoom effect
            zoom_factor = 1.2
            zoom_duration = duration * 0.8
            
            def zoom(t):
                if t < zoom_duration:
                    return 1 + (zoom_factor - 1) * (t / zoom_duration)
                return zoom_factor
            
            # Apply zoom effect
            clip = clip.resize(lambda t: zoom(t))
            
            # Center the zoomed image
            w, h = clip.size
            zoomed_w = int(w * zoom_factor)
            zoomed_h = int(h * zoom_factor)
            x_offset = (zoomed_w - w) // 2
            y_offset = (zoomed_h - h) // 2
            
            clip = clip.set_position((x_offset, y_offset))
            
            return clip
            
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            return None

    def _resize_and_crop(self, img: Image.Image) -> Image.Image:
        """Resize and crop image to target dimensions.
        
        Args:
            img: PIL Image to process
            
        Returns:
            Processed PIL Image
        """
        # Get current dimensions
        current_width, current_height = img.size
        
        # Calculate target dimensions maintaining aspect ratio
        target_ratio = self.width / self.height
        current_ratio = current_width / current_height
        
        if current_ratio > target_ratio:
            # Image is wider than target
            new_width = int(current_height * target_ratio)
            new_height = current_height
            left = (current_width - new_width) // 2
            top = 0
            right = left + new_width
            bottom = current_height
        else:
            # Image is taller than target
            new_width = current_width
            new_height = int(current_width / target_ratio)
            left = 0
            top = (current_height - new_height) // 2
            right = current_width
            bottom = top + new_height
        
        # Crop and resize
        img = img.crop((left, top, right, bottom))
        img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
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