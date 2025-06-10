"""
Main entry point for the video generator.
"""
from dotenv import load_dotenv
load_dotenv()

import argparse
from pathlib import Path

from .core.generator import VideoGenerator


def main():
    """Main entry point for the video generator."""
    parser = argparse.ArgumentParser(description='Generate videos from images')
    parser.add_argument('--mode', choices=['test', 'production'],
                       default='test', help='Operation mode')
    parser.add_argument('--format', choices=['horizontal', 'vertical'],
                       default='horizontal', help='Video format')
    parser.add_argument('--keywords', type=str,
                       help='Keywords for image search')
    parser.add_argument('--max-images', type=int, default=5,
                       help='Maximum number of images to use')
    parser.add_argument('--output', type=str, default='output.mp4',
                       help='Output video path')
    parser.add_argument('--duration', type=float, default=2.0,
                       help='Duration per image in seconds')
    parser.add_argument('--transition', type=float, default=1.0,
                       help='Transition duration in seconds')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize video generator
    generator = VideoGenerator(mode=args.mode, format=args.format)

    # Fetch images
    if args.keywords:
        images = generator.fetch_images(args.keywords, args.max_images)
    else:
        images = generator.fetch_images("wizard of oz", args.max_images)

    # Create video
    if images:
        success = generator.create_video(
            output_path=str(output_path),
            duration_per_image=args.duration,
            transition_duration=args.transition
        )
        if success:
            print(f"Video created successfully at: {output_path}")
        else:
            print("Failed to create video")
    else:
        print("No images available to create video")


if __name__ == '__main__':
    main() 