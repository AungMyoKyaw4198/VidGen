import os
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import requests
import time
import json
import numpy as np
import math
import random

# Workaround for MoviePy's use of deprecated PIL.Image.ANTIALIAS
Image.ANTIALIAS = Image.Resampling.LANCZOS
# Load environment variables
load_dotenv()

class VideoGenerator:
    def __init__(self, mode='test', format='horizontal'):
        self.script = ""
        self.images = []
        self.audio_path = ""
        self.video_path = ""
        self.mode = mode
        self.format = format  # 'horizontal' for 16:9, 'vertical' for 9:16
        self.test_images = [
            "https://i0.wp.com/www.thejudyroom.com/wp-content/uploads/2023/06/Munchkinland-Set-1-FX.jpg?ssl=1",
            "https://c8.alamy.com/comp/DWEEG0/judy-garland-on-set-of-the-film-the-wizard-of-oz-1939-DWEEG0.jpg",
            "http://farm4.staticflickr.com/3417/4626284019_9215b506bb_z.jpg"
        ]
        
    def fetch_images(self, keywords: str, max_results: int = 5) -> list[str]:
        """Fetch images using Google Custom Search API or return test images"""
        if self.mode == 'test':
            print("Using test mode with predefined images...")
            self.images = self.test_images[:max_results]
            for idx, url in enumerate(self.images, 1):
                print(f"{idx}. URL: {url}\n")
            print(f"Successfully loaded {len(self.images)} test images")
            return self.images
            
        try:
            # Get API credentials from environment
            api_key = os.getenv('GOOGLE_API_KEY')
            cx = os.getenv('GOOGLE_CX')
            
            if not api_key or not cx:
                print("Error: Google API credentials not found in environment variables")
                return []
            
            # Construct the API URL
            base_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': keywords,
                'searchType': 'image',
                'num': max_results,
                'safe': 'medium',
                'imgSize': 'large'
            }
            
            # Make the request
            print(f"Searching for '{keywords}'...")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            # Parse results
            results = response.json()
            if 'items' not in results:
                print("No images found")
                return []
            
            # Store image URLs
            self.images = []
            for idx, item in enumerate(results['items'], 1):
                print(f"{idx}. Title: {item['title']}")
                print(f"   URL: {item['link']}\n")
                self.images.append(item['link'])
            
            print(f"Successfully fetched {len(self.images)} images")
            return self.images
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing response: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return []
    
    def generate_script(self, prompt):
        # TODO: Implement OpenAI script generation
        pass
    
    def generate_voiceover(self, script):
        # TODO: Implement ElevenLabs voice generation
        pass
    
    def create_video(self, output_path="output.mp4", duration_per_image=2, transition_duration=1.0):
        """Create a video from the fetched images with random transitions"""
        try:
            import random
            from moviepy.editor import ImageClip, concatenate_videoclips, CompositeVideoClip, vfx
            
            if not self.images:
                print("No images available to create video")
                return False
                
            # Set dimensions based on format
            if self.format == 'horizontal':
                # 16:9 aspect ratio
                width = 1920  # Full HD width
                height = 1080  # Full HD height
            else:  # vertical format
                # 9:16 aspect ratio (TikTok)
                width = 1080
                height = 1920
            
            # Create video clips from images
            clips = []
            for img_url in self.images:
                try:
                    # Download and process image
                    response = requests.get(img_url)
                    img = Image.open(BytesIO(response.content))
                    
                    # Convert to RGB if image is in RGBA mode
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    
                    # Resize and crop image to maintain aspect ratio
                    img_ratio = img.width / img.height
                    target_ratio = width / height
                    
                    if img_ratio > target_ratio:  # Image is wider than target ratio
                        new_width = int(height * img_ratio)
                        img = img.resize((new_width, height), Image.Resampling.LANCZOS)
                        left = (img.width - width) // 2
                        img = img.crop((left, 0, left + width, height))
                    else:  # Image is taller than target ratio
                        new_height = int(width / img_ratio)
                        img = img.resize((width, new_height), Image.Resampling.LANCZOS)
                        top = (img.height - height) // 2
                        img = img.crop((0, top, width, top + height))
                    
                    # Convert PIL Image to numpy array for MoviePy
                    img_array = np.array(img)
                    
                    # Create video clip
                    clip = ImageClip(img_array)
                    
                    def zoom_pan_effect(get_frame, t):
                        img = Image.fromarray(get_frame(t))
                        base_size = img.size
                        
                        # Random zoom parameters - slower zoom effect
                        zoom_start = 1.0
                        zoom_end = 1.15  # Reduced zoom range for smoother effect
                        zoom_ratio = zoom_start + (zoom_end - zoom_start) * (t / duration_per_image)
                        
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
                        
                        # Random pan direction (top-left to bottom-right or reverse)
                        pan_start_x = 0 if random.random() < 0.5 else (new_size[0] - base_size[0])
                        pan_start_y = 0 if random.random() < 0.5 else (new_size[1] - base_size[1])
                        pan_end_x = (new_size[0] - base_size[0]) if pan_start_x == 0 else 0
                        pan_end_y = (new_size[1] - base_size[1]) if pan_start_y == 0 else 0
                        
                        # Calculate current pan position
                        current_x = pan_start_x + (pan_end_x - pan_start_x) * (t / duration_per_image)
                        current_y = pan_start_y + (pan_end_y - pan_start_y) * (t / duration_per_image)
                        
                        # Crop the image at current pan position
                        img = img.crop([
                            int(current_x), int(current_y),
                            int(current_x + base_size[0]), int(current_y + base_size[1])
                        ]).resize(base_size, Image.Resampling.LANCZOS)
                        
                        result = np.array(img)
                        img.close()
                        return result
                    
                    # Apply zoom and pan effect
                    clip = clip.fl(zoom_pan_effect).set_duration(duration_per_image)
                    
                    clips.append(clip)
                    
                except Exception as e:
                    print(f"Error processing image: {str(e)}")
                    continue
            
            if not clips:
                print("No valid images to create video")
                return False
            
            # Define available transitions
            transitions = [
                lambda c: c.crossfadein(transition_duration),
                lambda c: c.fadein(transition_duration),
                lambda c: c.fadeout(transition_duration),
                lambda c: c.resize(lambda t: 1 + 0.1*t).crossfadein(transition_duration),  # Zoom in + fade
                lambda c: c.resize(lambda t: 1.1 - 0.1*t).crossfadein(transition_duration),  # Zoom out + fade
            ]
            
            # Apply random transitions to clips
            final_clips = [clips[0]]
            for clip in clips[1:]:
                # Choose random transition
                transition_func = random.choice(transitions)
                # Apply transition
                clip_with_transition = transition_func(clip)
                final_clips.append(clip_with_transition)
            
            # Concatenate all clips
            final_clip = concatenate_videoclips(final_clips, method="compose")
            
            # Write the video file
            final_clip.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio=False,
                threads=4,
                preset='medium'
            )
            
            self.video_path = output_path
            print(f"Video created successfully at: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error creating video: {str(e)}")
            return False
    
    def upload_video(self):
        # TODO: Implement video upload to platforms
        pass

def main():
    print("Hello World! Video Generator is starting up...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create horizontal video (16:9)
    # print("\nGenerating horizontal video (16:9)...")
    # generator_horizontal = VideoGenerator(mode='test', format='horizontal')
    # images = generator_horizontal.fetch_images("The Wizard of Oz movie set", max_results=3)
    # if images:
    #     output_path = os.path.join(current_dir, "wizard_of_oz_horizontal.mp4")
    #     generator_horizontal.create_video(output_path=output_path, duration_per_image=2)
    
    # Create vertical video (9:16)
    print("\nGenerating vertical video (9:16)...")
    generator_vertical = VideoGenerator(mode='test', format='vertical')
    images = generator_vertical.fetch_images("The Wizard of Oz movie set", max_results=3)
    if images:
        output_path = os.path.join(current_dir, "wizard_of_oz_vertical.mp4")
        generator_vertical.create_video(output_path=output_path, duration_per_image=5)

if __name__ == "__main__":
    main()