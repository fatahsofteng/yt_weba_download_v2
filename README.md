# YouTube Audio Downloader V2

Automated YouTube audio downloader with comprehensive features for ASR calibration, audio dataset creation, and TTS/VC training.

## 🎯 Features

### ✅ Strict Audio Format Requirements
- **Container Format**: m4a (AAC codec)
- **Sample Rate**: 44kHz (44100 Hz) - STRICTLY ENFORCED
- **Channels**: Mono (1 channel) - automatically converted
- **Quality**: Highest available bitrate

### 📁 Organized File Structure
```
downloads/
  ├── {video_id_1}/
  │   ├── {video_id_1}.m4a          # Audio file (44kHz, mono)
  │   └── {video_id_1}.json         # Complete metadata
  ├── {video_id_2}/
  │   ├── {video_id_2}.m4a
  │   └── {video_id_2}.json
  └── ...
```

### 📊 Comprehensive Metadata
Each video includes complete metadata in JSON format:

**Video Metadata:**
- video_id, title, channel_url, channel_id, channel_name
- upload_date, duration, view_count, like_count
- description, tags, categories

**Audio Metadata:**
- codec, sample_rate, bit_rate, channels
- duration_sec, file_size

### 🛡️ Anti-Ban & Rate Limiting
- **Smart Rate Limiting**: 3-5s delay between API requests with random jitter
- **Download Throttling**: 5-10s delay between downloads
- **Speed Limiting**: Default 500KB/s to avoid triggering rate limits
- **403 Error Handling**: Exponential backoff (30s → 60s → 120s)
- **Automatic Retry**: Up to 3 retries with intelligent backoff

### 🚀 Multiple Download Modes
1. **Single Video**: Download one video at a time
2. **Channel Download**: Download all videos from a channel
3. **Batch Download**: Download from a file containing URLs

## 📋 Requirements

### System Requirements
- Python 3.7+
- FFmpeg (required for audio conversion)

### Python Dependencies
```bash
pip install -r requirements.txt
```

Dependencies:
- `yt-dlp>=2025.11.12` - YouTube downloader
- `mutagen>=1.47.0` - Audio metadata extraction

## 🔧 Installation

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### 3. Verify Installation
```bash
python youtube_downloader.py --help
```

## 🚀 Usage

### Download Single Video
```bash
python youtube_downloader.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download Entire Channel
```bash
python youtube_downloader.py --channel "https://www.youtube.com/@channel_name"
```

### Download from File (Batch)
Create a file `urls.txt` with one URL per line:
```
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
https://www.youtube.com/@channel_name
# Comments start with #
```

Then run:
```bash
python youtube_downloader.py --file urls.txt
```

### Advanced Options
```bash
# Custom output directory
python youtube_downloader.py --file urls.txt --output my_downloads

# Limit download speed (avoid ban)
python youtube_downloader.py --url "..." --speed-limit 300K

# Adjust rate limiting
python youtube_downloader.py --file urls.txt --min-delay 5 --max-delay 10

# Limit number of videos from channel
python youtube_downloader.py --channel "..." --max-videos 50
```

## 📖 Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--url` | Single video URL to download | - |
| `--channel` | Channel URL to download all videos | - |
| `--file` | File containing URLs (one per line) | `urls.txt` |
| `--output` | Output directory | `downloads` |
| `--max-videos` | Max videos to download from channel | All |
| `--speed-limit` | Download speed limit (e.g., 500K, 1M) | `500K` |
| `--min-delay` | Min delay between requests (seconds) | `3.0` |
| `--max-delay` | Max delay between requests (seconds) | `5.0` |

## 📊 Metadata Format

Example `{video_id}.json`:
```json
{
  "video_id": "Jq7llIkbJeA",
  "title": "Video Title",
  "channel_url": "https://www.youtube.com/@channel",
  "channel_id": "UC...",
  "channel_name": "Channel Name",
  "upload_date": "20231119",
  "duration": 512,
  "view_count": 1000000,
  "like_count": 50000,
  "description": "Video description...",
  "tags": ["tag1", "tag2"],
  "categories": ["Entertainment"],

  "audio": {
    "codec": "aac",
    "sample_rate": 44100,
    "bit_rate": 160000,
    "channels": 1,
    "duration_sec": 512.23,
    "file_size": 10485760
  },

  "download_timestamp": "2025-11-19 12:34:56",
  "original_url": "https://www.youtube.com/watch?v=Jq7llIkbJeA"
}
```

## 🎵 Audio Format Specifications

The downloader strictly enforces the following audio specifications:

1. **Container Format**: M4A (MPEG-4 Audio)
2. **Codec**: AAC (Advanced Audio Coding)
3. **Sample Rate**: 44.1 kHz (44100 Hz)
4. **Channels**: Mono (1 channel)
5. **Bitrate**: Highest available (typically 128-192 kbps)

These specifications are optimized for:
- ASR (Automatic Speech Recognition) calibration
- TTS (Text-to-Speech) training
- VC (Voice Conversion) training
- Audio dataset creation

## ⚠️ Rate Limiting & Anti-Ban

The downloader includes sophisticated anti-ban measures:

### Request Rate Limiting
- **3-5 seconds** between API requests (with random jitter)
- **5-10 seconds** between actual downloads
- Exponential backoff on errors

### 403 Error Handling
When a 403 (Forbidden) error is detected:
1. **First retry**: Wait 30 seconds
2. **Second retry**: Wait 60 seconds
3. **Third retry**: Wait 120 seconds
4. **After 3 failures**: Skip and continue to next video

### Download Speed Throttling
- Default limit: **500 KB/s**
- Prevents triggering YouTube's bandwidth rate limits
- Customizable via `--speed-limit` argument

### Best Practices
- Use default rate limiting settings for safety
- For large batch downloads, consider running overnight
- If you get persistent 403 errors, increase delays:
  ```bash
  python youtube_downloader.py --min-delay 10 --max-delay 15 --speed-limit 300K
  ```

## 📝 Channel List Support

The tool supports downloading from the provided channel list:
- **創用CC_50個YT頻道.txt**: List of 50 YouTube channels

Usage:
```bash
python youtube_downloader.py --file 創用CC_50個YT頻道.txt
```

The tool will automatically:
1. Detect channel URLs vs video URLs
2. Download all public videos from each channel
3. Skip already downloaded videos
4. Save complete metadata for each video

## 🔍 Logging

All operations are logged to:
- **Console**: Real-time progress
- **youtube_downloader.log**: Complete log file

Log levels:
- `INFO`: Normal operations
- `WARNING`: Non-critical issues (already downloaded, etc.)
- `ERROR`: Download failures, 403 errors, etc.

## 🛠️ Troubleshooting

### FFmpeg Not Found
**Error**: `FFmpeg not found`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from ffmpeg.org and add to PATH
```

### 403 Forbidden Errors
**Error**: `403 Error (Forbidden)`

**Solutions**:
1. Increase rate limiting delays:
   ```bash
   --min-delay 10 --max-delay 15
   ```
2. Reduce download speed:
   ```bash
   --speed-limit 300K
   ```
3. Use cookies for age-restricted videos:
   - Export cookies from browser to `config_cookies.txt`
   - Tool will automatically use them

### Already Downloaded Videos
The tool automatically skips videos that are already downloaded (both audio file and metadata exist).

To re-download:
```bash
# Delete the specific video folder
rm -rf downloads/{video_id}
```

## 📚 Project Structure

```
yt_weba_download_v2/
├── youtube_downloader.py      # Main downloader (NEW - recommended)
├── turboscribe_batch.py       # TurboScribe API downloader (legacy)
├── batch_from_file.py         # Batch processor (legacy)
├── batch_from_file_parallel.py # Parallel batch processor (legacy)
├── requirements.txt           # Python dependencies
├── config_headers.json        # HTTP headers config (for TurboScribe)
├── config_cookies.txt         # Cookies for authentication
├── urls.txt                   # Input URLs file
├── 創用CC_50個YT頻道.txt       # Channel list
├── notes.txt                  # Development notes
├── notion.md                  # Detailed requirements
├── README.md                  # This file
├── downloads/                 # Output directory (created on first run)
│   └── {video_id}/
│       ├── {video_id}.m4a
│       └── {video_id}.json
└── youtube_downloader.log     # Log file (created on first run)
```

## 🎯 Use Cases

### 1. ASR Calibration
Download clean audio samples with consistent format (44kHz, mono) for training speech recognition models.

### 2. TTS/VC Training
Build audio datasets with comprehensive metadata for voice synthesis and conversion models.

### 3. Audio Dataset Creation
Create organized, well-documented audio datasets for machine learning research.

### 4. Channel Archival
Archive entire YouTube channels for research or backup purposes.

## 📄 License

This project follows the Creative Commons (CC) licenses as specified in the channel list.

## 🤝 Contributing

This tool was developed for automated YouTube audio downloading with strict format requirements.

For issues or improvements, please refer to the project documentation.

## 📞 Support

For issues related to:
- **Rate limiting**: Adjust `--min-delay`, `--max-delay`, and `--speed-limit`
- **Audio format**: FFmpeg must be installed and accessible
- **403 errors**: Use cookies or increase rate limiting
- **Metadata**: Check `{video_id}.json` files in download folders

## 🎓 References

- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Audio Format Specifications](notion.md)
- [Development Notes](notes.txt)
