"""
YouTube Audio Downloader with Comprehensive Features
- Downloads audio in m4a format with 44kHz sampling rate
- Organizes files in individual folders with metadata
- Implements rate limiting and anti-ban measures
- Supports both single videos and entire channels
"""

import yt_dlp
import json
import time
import random
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from mutagen.mp4 import MP4
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_downloader.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Advanced rate limiter with random jitter and exponential backoff"""

    def __init__(self,
                 min_delay: float = 3.0,
                 max_delay: float = 5.0,
                 download_delay_min: float = 5.0,
                 download_delay_max: float = 10.0):
        """
        Initialize rate limiter

        Args:
            min_delay: Minimum delay between API requests (seconds)
            max_delay: Maximum delay between API requests (seconds)
            download_delay_min: Minimum delay between downloads (seconds)
            download_delay_max: Maximum delay between downloads (seconds)
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.download_delay_min = download_delay_min
        self.download_delay_max = download_delay_max
        self.last_request_time = 0
        self.last_download_time = 0
        self.error_count = 0

    def wait_for_request(self):
        """Wait before making next API request with random jitter"""
        delay = random.uniform(self.min_delay, self.max_delay)

        # Add exponential backoff if there were recent errors
        if self.error_count > 0:
            backoff = min(2 ** self.error_count, 60)  # Max 60 seconds
            delay += backoff
            logger.info(f"Adding {backoff}s backoff due to {self.error_count} recent errors")

        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.info(f"Rate limiting: waiting {sleep_time:.2f}s before next request")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def wait_for_download(self):
        """Wait before starting next download with random jitter"""
        delay = random.uniform(self.download_delay_min, self.download_delay_max)

        elapsed = time.time() - self.last_download_time
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.info(f"Download throttling: waiting {sleep_time:.2f}s before next download")
            time.sleep(sleep_time)

        self.last_download_time = time.time()

    def on_error(self, error_code: Optional[int] = None):
        """Handle error and adjust rate limiting"""
        self.error_count += 1

        if error_code == 403:
            # Aggressive backoff for 403 errors
            wait_times = [30, 60, 120]  # Exponential backoff: 30s, 60s, 120s
            wait_time = wait_times[min(self.error_count - 1, len(wait_times) - 1)]
            logger.warning(f"⚠ 403 Error detected! Waiting {wait_time}s before retry (attempt {self.error_count})")
            time.sleep(wait_time)

    def on_success(self):
        """Reset error count on successful request"""
        self.error_count = 0


class YouTubeDownloader:
    """YouTube audio downloader with comprehensive features"""

    def __init__(self,
                 output_dir: str = "downloads",
                 rate_limiter: Optional[RateLimiter] = None,
                 max_retries: int = 3,
                 speed_limit: str = "500K"):
        """
        Initialize YouTube downloader

        Args:
            output_dir: Base output directory
            rate_limiter: Rate limiter instance
            max_retries: Maximum number of retries for failed downloads
            speed_limit: Download speed limit (e.g., "500K" for 500KB/s)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.max_retries = max_retries
        self.speed_limit = speed_limit

        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

    def _get_ydl_opts(self, video_id: str) -> Dict:
        """
        Get yt-dlp options for downloading

        Args:
            video_id: Video ID for output path

        Returns:
            Dictionary of yt-dlp options
        """
        video_dir = self.output_dir / video_id
        video_dir.mkdir(exist_ok=True, parents=True)

        return {
            # Output settings
            'outtmpl': str(video_dir / f'{video_id}.%(ext)s'),

            # Audio format settings - STRICT REQUIREMENTS
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '192',
            }, {
                'key': 'FFmpegMetadata',
            }],

            # Audio processing - Convert to 44kHz mono
            'postprocessor_args': [
                '-ar', '44000',  # Sample rate: 44kHz EXACTLY (STRICT REQUIREMENT)
                '-ac', '1',      # Channels: Mono (convert to 1 channel)
            ],

            # Download settings
            'ratelimit': self._parse_speed_limit(self.speed_limit),
            'retries': self.max_retries,
            'fragment_retries': self.max_retries,

            # Metadata and info
            'writethumbnail': False,
            'writesubtitles': False,
            'writeinfojson': False,  # We'll write our own custom metadata

            # Other settings
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,

            # Cookie support (for age-restricted videos)
            'cookiefile': 'config_cookies.txt' if Path('config_cookies.txt').exists() else None,
        }

    def _parse_speed_limit(self, limit_str: str) -> int:
        """
        Parse speed limit string to bytes/second

        Args:
            limit_str: Speed limit string (e.g., "500K", "1M")

        Returns:
            Speed limit in bytes/second
        """
        limit_str = limit_str.upper().strip()
        if limit_str.endswith('K'):
            return int(float(limit_str[:-1]) * 1024)
        elif limit_str.endswith('M'):
            return int(float(limit_str[:-1]) * 1024 * 1024)
        else:
            return int(limit_str)

    def _extract_audio_metadata(self, audio_file: Path) -> Dict:
        """
        Extract audio metadata from m4a file

        Args:
            audio_file: Path to audio file

        Returns:
            Dictionary containing audio metadata
        """
        try:
            audio = MP4(str(audio_file))

            return {
                'codec': 'aac',  # m4a typically uses AAC codec
                'sample_rate': audio.info.sample_rate,
                'bit_rate': audio.info.bitrate,
                'channels': audio.info.channels,
                'duration_sec': round(audio.info.length, 2),
                'file_size': audio_file.stat().st_size
            }
        except Exception as e:
            logger.error(f"Failed to extract audio metadata: {e}")
            return {
                'codec': 'unknown',
                'sample_rate': 0,
                'bit_rate': 0,
                'channels': 0,
                'duration_sec': 0,
                'file_size': audio_file.stat().st_size if audio_file.exists() else 0
            }

    def _save_metadata(self, video_id: str, video_info: Dict, audio_metadata: Dict):
        """
        Save comprehensive metadata to JSON file

        Args:
            video_id: Video ID
            video_info: Video information from yt-dlp
            audio_metadata: Extracted audio metadata
        """
        video_dir = self.output_dir / video_id
        metadata_file = video_dir / f'{video_id}.json'

        metadata = {
            # Video metadata
            'video_id': video_id,
            'title': video_info.get('title', 'Unknown'),
            'channel_url': video_info.get('channel_url', ''),
            'channel_id': video_info.get('channel_id', ''),
            'channel_name': video_info.get('channel', ''),
            'uploader': video_info.get('uploader', ''),
            'upload_date': video_info.get('upload_date', ''),
            'duration': video_info.get('duration', 0),
            'view_count': video_info.get('view_count', 0),
            'like_count': video_info.get('like_count', 0),
            'description': video_info.get('description', ''),
            'tags': video_info.get('tags', []),
            'categories': video_info.get('categories', []),

            # Audio metadata
            'audio': audio_metadata,

            # Download metadata
            'download_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'original_url': video_info.get('webpage_url', ''),
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ Metadata saved: {metadata_file}")

    def download_video(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Download audio from a single YouTube video

        Args:
            url: YouTube video URL

        Returns:
            Tuple of (success, video_id)
        """
        self.stats['total'] += 1

        try:
            # Wait before making request (rate limiting)
            self.rate_limiter.wait_for_request()

            # Extract video info first
            logger.info(f"Extracting info for: {url}")
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                video_info = ydl.extract_info(url, download=False)
                video_id = video_info['id']

            # Check if already downloaded
            video_dir = self.output_dir / video_id
            audio_file = video_dir / f'{video_id}.m4a'
            metadata_file = video_dir / f'{video_id}.json'

            if audio_file.exists() and metadata_file.exists():
                logger.info(f"⊘ Already downloaded: {video_id} - {video_info.get('title', 'Unknown')}")
                self.stats['skipped'] += 1
                return True, video_id

            # Wait before downloading (additional throttling)
            self.rate_limiter.wait_for_download()

            # Download audio
            logger.info(f"Downloading: {video_id} - {video_info.get('title', 'Unknown')}")
            ydl_opts = self._get_ydl_opts(video_id)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Extract audio metadata
            audio_metadata = self._extract_audio_metadata(audio_file)

            # Verify strict requirements
            if audio_metadata['sample_rate'] != 44000:
                logger.warning(f"⚠ Sample rate is {audio_metadata['sample_rate']}Hz, expected 44000Hz")
            if audio_metadata['channels'] != 1:
                logger.warning(f"⚠ Channels: {audio_metadata['channels']}, expected 1 (mono)")

            # Save metadata
            self._save_metadata(video_id, video_info, audio_metadata)

            logger.info(f"✓ Success: {video_id} - Audio: {audio_metadata['sample_rate']}Hz, {audio_metadata['channels']}ch")

            self.stats['success'] += 1
            self.rate_limiter.on_success()

            return True, video_id

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)

            # Check for 403 errors
            if '403' in error_msg or 'Forbidden' in error_msg:
                logger.error(f"✗ 403 Error (Forbidden): {url}")
                self.rate_limiter.on_error(403)
            else:
                logger.error(f"✗ Download error: {url} - {error_msg}")
                self.rate_limiter.on_error()

            self.stats['failed'] += 1
            return False, None

        except Exception as e:
            logger.error(f"✗ Unexpected error: {url} - {str(e)}")
            self.rate_limiter.on_error()
            self.stats['failed'] += 1
            return False, None

    def download_channel(self, channel_url: str, max_videos: Optional[int] = None) -> List[Tuple[bool, Optional[str]]]:
        """
        Download all videos from a YouTube channel

        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to download (None = all)

        Returns:
            List of (success, video_id) tuples
        """
        logger.info(f"Fetching videos from channel: {channel_url}")

        try:
            # Extract channel info and video list
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                channel_info = ydl.extract_info(channel_url, download=False)

                if 'entries' not in channel_info:
                    logger.error("No videos found in channel")
                    return []

                videos = channel_info['entries']
                total_videos = len(videos)

                if max_videos:
                    videos = videos[:max_videos]
                    logger.info(f"Downloading {len(videos)} of {total_videos} videos from channel")
                else:
                    logger.info(f"Downloading all {total_videos} videos from channel")

            # Download each video
            results = []
            for idx, video in enumerate(videos, 1):
                if video is None:
                    continue

                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                logger.info(f"\n{'='*60}")
                logger.info(f"Progress: {idx}/{len(videos)}")
                logger.info(f"{'='*60}")

                result = self.download_video(video_url)
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Failed to fetch channel videos: {e}")
            return []

    def download_from_file(self, urls_file: str) -> List[Tuple[bool, Optional[str]]]:
        """
        Download videos from a file containing URLs (one per line)

        Args:
            urls_file: Path to file containing URLs

        Returns:
            List of (success, video_id) tuples
        """
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            logger.info(f"Found {len(urls)} URLs in {urls_file}")

            results = []
            for idx, url in enumerate(urls, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"Progress: {idx}/{len(urls)}")
                logger.info(f"{'='*60}")

                # Determine if it's a channel or video URL
                if '/channel/' in url or '/@' in url or '/c/' in url or '/user/' in url:
                    logger.info(f"Detected channel URL: {url}")
                    channel_results = self.download_channel(url)
                    results.extend(channel_results)
                else:
                    result = self.download_video(url)
                    results.append(result)

            return results

        except FileNotFoundError:
            logger.error(f"File not found: {urls_file}")
            return []

    def print_summary(self):
        """Print download summary statistics"""
        print("\n" + "="*60)
        print("DOWNLOAD SUMMARY")
        print("="*60)
        print(f"Total URLs processed: {self.stats['total']}")
        print(f"✓ Successful:        {self.stats['success']}")
        print(f"⊘ Skipped (exists):  {self.stats['skipped']}")
        print(f"✗ Failed:            {self.stats['failed']}")
        print("="*60)

        # Calculate success rate
        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            print(f"Success rate: {success_rate:.1f}%")

        print("="*60 + "\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='YouTube Audio Downloader')
    parser.add_argument('--url', help='Single video URL to download')
    parser.add_argument('--channel', help='Channel URL to download all videos from')
    parser.add_argument('--file', default='urls.txt', help='File containing URLs (default: urls.txt)')
    parser.add_argument('--output', default='downloads', help='Output directory (default: downloads)')
    parser.add_argument('--max-videos', type=int, help='Maximum videos to download from channel')
    parser.add_argument('--speed-limit', default='500K', help='Download speed limit (default: 500K)')
    parser.add_argument('--min-delay', type=float, default=3.0, help='Minimum delay between requests (default: 3s)')
    parser.add_argument('--max-delay', type=float, default=5.0, help='Maximum delay between requests (default: 5s)')

    args = parser.parse_args()

    # Create rate limiter
    rate_limiter = RateLimiter(
        min_delay=args.min_delay,
        max_delay=args.max_delay
    )

    # Create downloader
    downloader = YouTubeDownloader(
        output_dir=args.output,
        rate_limiter=rate_limiter,
        speed_limit=args.speed_limit
    )

    # Download based on arguments
    if args.url:
        logger.info(f"Downloading single video: {args.url}")
        downloader.download_video(args.url)
    elif args.channel:
        logger.info(f"Downloading channel: {args.channel}")
        downloader.download_channel(args.channel, max_videos=args.max_videos)
    else:
        logger.info(f"Downloading from file: {args.file}")
        downloader.download_from_file(args.file)

    # Print summary
    downloader.print_summary()


if __name__ == "__main__":
    main()
