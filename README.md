# VidGen: Modular Video Generation Project

VidGen is a modular, extensible Python project for generating videos from images, with support for script and voiceover generation, transitions, and flexible configuration. The project is structured for maintainability and follows Python best practices.

## Features
- Fetch images from Google Custom Search API or use test images
- Generate videos with smooth transitions and zoom/pan effects
- Support for horizontal (16:9) and vertical (9:16) video formats
- Modular architecture: core, services, and utilities
- Type-annotated, PEP8-compliant codebase
- Easily extendable for script and voiceover generation (OpenAI, ElevenLabs)
- Command-line interface for flexible usage

## Project Structure
```
VidGen/
├── src/
│   └── video_gen/
│       ├── core/
│       │   └── generator.py
│       ├── services/
│       │   ├── image_service.py
│       │   └── video_service.py
│       ├── utils/
│       │   └── config.py
│       ├── __main__.py
│       ├── __init__.py
│       └── ...
├── requirements.txt
├── README.md
└── ...
```

## Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd VidGen
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the video generator from the command line:
```bash
python3 -m src.video_gen --mode test --format horizontal --max-images 3 --output test_output.mp4
```

### Command-Line Options
- `--mode`         : `test` (default) or `production` (use API)
- `--format`       : `horizontal` (16:9) or `vertical` (9:16)
- `--keywords`     : Search keywords for images
- `--max-images`   : Maximum number of images to use (default: 5)
- `--output`       : Output video file path (default: output.mp4)
- `--duration`     : Duration per image in seconds (default: 2.0)
- `--transition`   : Transition duration in seconds (default: 1.0)

### Example
```bash
python3 -m src.video_gen --mode test --format vertical --keywords "wizard of oz" --max-images 5 --output myvideo.mp4
```

## Environment Variables
For production mode (fetching images from Google):
- `GOOGLE_API_KEY` : Your Google Custom Search API key
- `GOOGLE_CX`      : Your Google Custom Search Engine ID

You can set these in a `.env` file:
```
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CX=your_cx_here
```
As of 2017 (this may be outdated in the future), here are the steps:
1) After getting the API key (under Custom Search API) 
https://console.cloud.google.com/apis/dashboard?inv=1&invt=AbzwVw&project=vidgen-1749190468011
2) Head to CSE home
https://programmablesearchengine.google.com/controlpanel/all
3) Click on Add below Edit Search Engine
4) You'll get a search box, type in www.google.com and then click on Create at the bottom
5) You'll get your cx code (called Search Engine ID) to use with your API key

## Extending Functionality
- **Script Generation**: Implement in `VideoGenerator.generate_script()` (e.g., using OpenAI API)
- **Voiceover Generation**: Implement in `VideoGenerator.generate_voiceover()` (e.g., using ElevenLabs)
- **Video Upload**: Implement in `VideoGenerator.upload_video()`

## Contributing
1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes (follow PEP8 and project structure)
4. Commit and push (`git commit -am 'Add new feature' && git push origin feature/your-feature`)
5. Open a pull request

## Code Style & Rules
- Functions should be under 50 lines
- Files should be under 300 lines
- Use snake_case for functions, PascalCase for classes
- Follow PEP8 import order
- Keep models and views in separate modules
- Limit imports per file for readability

## License
[MIT](LICENSE)

## Authors
- [Your Name]

---
Feel free to open issues or pull requests for improvements or questions! 