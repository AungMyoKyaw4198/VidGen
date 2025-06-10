import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def test_youtube_api():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key:
        print("Error: YOUTUBE_API_KEY not found in .env file")
        return False
    
    print(f"Found API key: {api_key[:10]}...")  # Only show first 10 chars for security
    
    try:
        # Build YouTube service
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Try a simple search request
        request = youtube.search().list(
            part='snippet',
            q='CR7 vacation training',
            maxResults=1,
            type='video'
        )
        
        # Execute request
        response = request.execute()
        
        if response['items']:
            video = response['items'][0]
            print("\nAPI Test Successful!")
            print(f"Found video: {video['snippet']['title']}")
            print(f"Video ID: {video['id']['videoId']}")
            return True
        else:
            print("API Test Successful but no videos found")
            return True
            
    except HttpError as e:
        print(f"\nAPI Error: {e}")
        if 'quota' in str(e).lower():
            print("This might be due to exceeded API quota")
        elif 'invalid' in str(e).lower():
            print("This might be due to invalid API key")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing YouTube API connection...")
    test_youtube_api() 