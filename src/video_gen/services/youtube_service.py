from typing import List, Optional, Dict
import os
from datetime import datetime, timedelta
import pytube
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from moviepy.editor import VideoFileClip
import logging

class YouTubeService:
    """Service for fetching and processing YouTube videos."""
    
    def __init__(self, api_key: str):
        """Initialize YouTube service with API key.
        
        Args:
            api_key: YouTube Data API v3 key
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.temp_dir = "temp_videos"
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def search_videos(self, 
                     keywords: str, 
                     max_results: int = 5,
                     max_duration: int = 60,  # 1 minute in seconds
                     min_views: int = 1000,
                     published_after: Optional[datetime] = None) -> List[Dict]:
        """Search for videos matching criteria.
        
        Args:
            keywords: Search keywords
            max_results: Maximum number of results to return
            max_duration: Maximum video duration in seconds
            min_views: Minimum view count
            published_after: Only include videos published after this date
            
        Returns:
            List of video metadata dictionaries
        """
        try:
            # Prepare search request
            search_params = {
                'q': keywords,
                'part': 'snippet',
                'maxResults': max_results,
                'type': 'video',
                'videoDuration': 'short',  # short = under 4 minutes
                'order': 'relevance',
                'relevanceLanguage': 'en'
            }
            
            if published_after:
                search_params['publishedAfter'] = published_after.isoformat() + 'Z'
            
            # Execute search
            search_response = self.youtube.search().list(**search_params).execute()
            
            # Get video IDs
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get detailed video information
            video_response = self.youtube.videos().list(
                part='contentDetails,statistics',
                id=','.join(video_ids)
            ).execute()
            
            # Filter and process results
            valid_videos = []
            for video in video_response['items']:
                # Parse duration (ISO 8601 format)
                duration = video['contentDetails']['duration']
                duration_seconds = self._parse_duration(duration)
                
                # Get view count
                view_count = int(video['statistics'].get('viewCount', 0))
                
                # Apply filters
                if (duration_seconds <= max_duration and 
                    view_count >= min_views):
                    valid_videos.append({
                        'id': video['id'],
                        'title': next(item['snippet']['title'] 
                                    for item in search_response['items'] 
                                    if item['id']['videoId'] == video['id']),
                        'duration': duration_seconds,
                        'views': view_count,
                        'url': f"https://www.youtube.com/watch?v={video['id']}"
                    })
            
            return valid_videos
            
        except HttpError as e:
            logging.error(f"An HTTP error occurred: {e}")
            return []
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return []
    
    def download_video(self, video_url: str, output_path: Optional[str] = None) -> Optional[str]:
        """Download a YouTube video using yt_dlp."""
        try:
            import yt_dlp
            if not output_path:
                video_id = video_url.split("v=")[-1]
                output_path = os.path.join(self.temp_dir, f"{video_id}.mp4")
            
            ydl_opts = {
                'format': 'mp4[height<=720]',
                'outtmpl': output_path,
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            return output_path if os.path.exists(output_path) else None
        except Exception as e:
            logging.error(f"Error downloading video with yt_dlp: {e}")
            return None
    
    def extract_clip(self, 
                    video_path: str, 
                    duration: int = 5,
                    start_time: Optional[int] = None) -> Optional[str]:
        """Extract a clip from a video.
        
        Args:
            video_path: Path to video file
            duration: Duration of clip in seconds
            start_time: Optional start time in seconds
            
        Returns:
            Path to extracted clip or None if failed
        """
        try:
            # Load video
            video = VideoFileClip(video_path)
            
            # Determine start time if not provided
            if start_time is None:
                # Start from middle of video
                start_time = (video.duration - duration) / 2
            
            # Extract clip
            clip = video.subclip(start_time, start_time + duration)
            
            # Generate output path
            output_path = os.path.join(
                self.temp_dir,
                f"clip_{os.path.basename(video_path)}"
            )
            
            # Write clip
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Clean up
            video.close()
            clip.close()
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error extracting clip: {e}")
            return None
    
    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds.
        
        Args:
            duration: ISO 8601 duration string (e.g., 'PT1M30S')
            
        Returns:
            Duration in seconds
        """
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0
            
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir, exist_ok=True)
        except Exception as e:
            logging.error(f"Error cleaning up temporary files: {e}") 