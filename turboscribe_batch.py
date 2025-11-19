import requests
import json
import time
from typing import List, Dict, Optional
import logging
from pathlib import Path
from html.parser import HTMLParser
import html
import zstandard as zstd

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioLinkExtractor(HTMLParser):
    """從 HTML 中提取音訊下載連結的解析器"""
    
    def __init__(self):
        super().__init__()
        self.audio_link = None
        self.found = False
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a' and not self.found:
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value and 'mime=audio%2Fwebm' in attr_value:
                    # 找到音訊連結，解碼 HTML 實體
                    self.audio_link = html.unescape(attr_value)
                    self.found = True
                    break


class TurboScribeBatch:
    """批量呼叫 TurboScribe API 的類別"""
    
    def __init__(self, delay: float = 1.0, 
                 headers_file: str = "config_headers.json",
                 cookies_file: str = "config_cookies.txt"):
        """
        初始化
        
        Args:
            delay: 每次請求之間的延遲時間（秒）
            headers_file: Headers 設定檔路徑
            cookies_file: Cookies 設定檔路徑
        """
        self.api_url = "https://turboscribe.ai/_htmx/NCN20gAEkZMBzQPXkQc"
        self.delay = delay
        self.session = requests.Session()
        
        # 從檔案載入 headers
        self._load_headers(headers_file)
        
        # 從檔案載入 cookies
        self._load_cookies(cookies_file)
    
    def _load_headers(self, headers_file: str):
        """
        從 JSON 檔案載入 headers
        
        Args:
            headers_file: Headers 檔案路徑
        """
        try:
            headers_path = Path(headers_file)
            if headers_path.exists():
                with open(headers_path, 'r', encoding='utf-8') as f:
                    headers = json.load(f)
                    self.session.headers.update(headers)
                    logger.info(f"✓ 已載入 headers 從 {headers_file}")
            else:
                logger.warning(f"⚠ Headers 檔案不存在: {headers_file}，使用預設 headers")
                # 使用預設 headers
                self.session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Content-Type': 'application/json',
                    'Accept': '*/*'
                })
        except Exception as e:
            logger.error(f"✗ 載入 headers 失敗: {e}")
            raise
    
    def _load_cookies(self, cookies_file: str):
        """
        從文字檔案載入 cookies
        
        Args:
            cookies_file: Cookies 檔案路徑
        """
        try:
            cookies_path = Path(cookies_file)
            if cookies_path.exists():
                with open(cookies_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # 跳過空行和註解
                        if line and not line.startswith('#'):
                            self._set_cookies(line)
                            logger.info(f"✓ 已載入 cookies 從 {cookies_file}")
                            break
            else:
                logger.warning(f"⚠ Cookies 檔案不存在: {cookies_file}")
                logger.warning("⚠ 請在 config_cookies.txt 中設定你的 Cookie")
        except Exception as e:
            logger.error(f"✗ 載入 cookies 失敗: {e}")
            raise
    
    def _set_cookies(self, cookie_string: str):
        """
        從 cookie 字串設定 cookies
        
        Args:
            cookie_string: Cookie 字串（格式: "name1=value1; name2=value2")
        """
        for cookie in cookie_string.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                self.session.cookies.set(name.strip(), value.strip())
    
    def _decode_response_content(self, response: requests.Response) -> str:
        """
        解碼回應內容，處理可能的 zstd 壓縮
        
        Args:
            response: requests 回應物件
            
        Returns:
            解碼後的文字內容
        """
        # 檢查 Content-Encoding header
        encoding = response.headers.get('Content-Encoding', '').lower()
        
        if encoding == 'zstd':
            try:
                # 使用 zstandard 解壓縮
                dctx = zstd.ZstdDecompressor()
                decompressed = dctx.decompress(response.content)
                return decompressed.decode('utf-8')
            except Exception as e:
                logger.warning(f"⚠ zstd 解壓縮失敗，嘗試直接解碼: {e}")
                # 如果解壓縮失敗，嘗試直接解碼
                return response.text
        else:
            # 沒有壓縮或使用其他壓縮方式（requests 會自動處理 gzip, deflate）
            return response.text
    
    def _extract_audio_link(self, html_content: str) -> Optional[str]:
        """
        從 HTML 內容中提取第一個音訊下載連結
        
        Args:
            html_content: HTML 內容
            
        Returns:
            音訊下載連結，如果未找到則返回 None
        """
        parser = AudioLinkExtractor()
        parser.feed(html_content)
        return parser.audio_link
    
    def _download_audio(self, audio_url: str, video_id: str) -> Optional[str]:
        """
        下載音訊檔案（優化版：支援大檔案、顯示進度、更長超時時間）
        
        Args:
            audio_url: 音訊檔案 URL
            video_id: YouTube 影片 ID
            
        Returns:
            下載的檔案路徑，失敗則返回 None
        """
        try:
            # 建立輸出目錄
            output_dir = Path("audio_downloads")
            output_dir.mkdir(exist_ok=True)
            
            # 從 URL 判斷檔案格式
            if 'mime=audio%2Fwebm' in audio_url or 'mime=audio/webm' in audio_url:
                ext = 'weba'
            elif 'mime=audio%2Fmp4' in audio_url or 'mime=audio/mp4' in audio_url:
                ext = 'm4a'
            else:
                ext = 'audio'
            
            # 生成檔案名稱
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{video_id}_{timestamp}.{ext}"
            filepath = output_dir / filename
            
            logger.info(f"開始下載音訊: {filename}")
            
            # 下載檔案 - 增加超時時間到 10 分鐘，使用更大的 chunk size
            # connect timeout: 30秒, read timeout: 600秒 (10分鐘)
            response = requests.get(
                audio_url, 
                stream=True, 
                timeout=(30, 600)
            )
            response.raise_for_status()
            
            # 獲取檔案大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 寫入檔案並顯示進度
            downloaded_size = 0
            chunk_size = 1024 * 1024  # 1MB chunks for faster download
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 顯示進度（每 1MB 更新一次）
                        if total_size > 0 and downloaded_size % (1 * 1024 * 1024) < chunk_size:
                            progress = (downloaded_size / total_size) * 100
                            logger.info(f"下載進度: {progress:.1f}% ({downloaded_size / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB)")
            
            logger.info(f"✓ 音訊已下載: {filepath} (大小: {downloaded_size / (1024*1024):.1f}MB)")
            return str(filepath)
            
        except requests.exceptions.Timeout as e:
            logger.error(f"✗ 下載音訊超時: {e}")
            logger.error(f"   建議: 檔案可能太大，請檢查網路連線或稍後重試")
            return None
        except Exception as e:
            logger.error(f"✗ 下載音訊失敗: {e}")
            return None
    
    def process_single_url(self, youtube_url: str, save_html: bool = True, download_audio: bool = True) -> Dict:
        """
        處理單個 YouTube URL
        
        Args:
            youtube_url: YouTube 影片網址
            save_html: 是否將回應儲存為 HTML 檔案
            
        Returns:
            包含結果的字典
        """
        payload = {"url": youtube_url}
        
        try:
            logger.info(f"正在處理: {youtube_url}")
            response = self.session.post(
                self.api_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✓ 成功: {youtube_url}")
                
                # 解碼回應內容（處理可能的 zstd 壓縮）
                decoded_content = self._decode_response_content(response)
                
                # 儲存 HTML 回應
                html_file = None
                if save_html and decoded_content:
                    html_file = self._save_html_response(youtube_url, decoded_content)
                
                # 提取並下載音訊
                audio_file = None
                if download_audio and decoded_content:
                    audio_link = self._extract_audio_link(decoded_content)
                    if audio_link:
                        video_id = self._extract_video_id(youtube_url)
                        audio_file = self._download_audio(audio_link, video_id)
                    else:
                        logger.warning("⚠ 未找到音訊下載連結")
                
                return {
                    "url": youtube_url,
                    "status": "success",
                    "response": decoded_content,
                    "status_code": response.status_code,
                    "html_file": html_file,
                    "audio_file": audio_file
                }
            else:
                logger.warning(f"✗ 失敗 (狀態碼 {response.status_code}): {youtube_url}")
                return {
                    "url": youtube_url,
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "response": response.text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ 錯誤: {youtube_url} - {str(e)}")
            return {
                "url": youtube_url,
                "status": "error",
                "error": str(e)
            }
    
    def _save_html_response(self, youtube_url: str, html_content: str) -> str:
        """
        將 HTML 回應儲存為檔案
        
        Args:
            youtube_url: YouTube 影片網址
            html_content: HTML 內容
            
        Returns:
            儲存的檔案路徑
        """
        # 從 YouTube URL 提取影片 ID
        video_id = self._extract_video_id(youtube_url)
        
        # 建立輸出目錄
        output_dir = Path("html_responses")
        output_dir.mkdir(exist_ok=True)
        
        # 生成檔案名稱
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{video_id}_{timestamp}.html"
        filepath = output_dir / filename
        
        # 儲存 HTML 檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✓ HTML 已儲存: {filepath}")
        return str(filepath)
    
    def _extract_video_id(self, youtube_url: str) -> str:
        """
        從 YouTube URL 提取影片 ID
        
        Args:
            youtube_url: YouTube 影片網址
            
        Returns:
            影片 ID，如果無法提取則返回時間戳
        """
        try:
            # 支援多種 YouTube URL 格式
            if 'v=' in youtube_url:
                video_id = youtube_url.split('v=')[1].split('&')[0]
            elif 'youtu.be/' in youtube_url:
                video_id = youtube_url.split('youtu.be/')[1].split('?')[0]
            else:
                video_id = time.strftime("%Y%m%d_%H%M%S")
            return video_id
        except:
            return time.strftime("%Y%m%d_%H%M%S")
    
    def process_batch(self, youtube_urls: List[str], save_html: bool = True, download_audio: bool = True) -> List[Dict]:
        """
        批量處理多個 YouTube URL
        
        Args:
            youtube_urls: YouTube 影片網址列表
            save_html: 是否將回應儲存為 HTML 檔案
            download_audio: 是否自動下載音訊檔案
            
        Returns:
            包含所有結果的列表
        """
        results = []
        total = len(youtube_urls)
        
        logger.info(f"開始批量處理 {total} 個 URL")
        
        for idx, url in enumerate(youtube_urls, 1):
            logger.info(f"進度: {idx}/{total}")
            
            result = self.process_single_url(url, save_html=save_html, download_audio=download_audio)
            results.append(result)
            
            # 如果不是最後一個，則等待
            if idx < total:
                time.sleep(self.delay)
        
        logger.info("批量處理完成")
        return results
    
    def save_results(self, results: List[Dict], output_file: str = "results.json"):
        """
        儲存結果到 JSON 檔案
        
        Args:
            results: 結果列表
            output_file: 輸出檔案名稱
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"結果已儲存至: {output_file}")
    
    def print_summary(self, results: List[Dict]):
        """
        印出處理摘要
        
        Args:
            results: 結果列表
        """
        total = len(results)
        success = sum(1 for r in results if r['status'] == 'success')
        failed = total - success
        
        print("\n" + "="*50)
        print("處理摘要")
        print("="*50)
        print(f"總計: {total}")
        print(f"成功: {success}")
        print(f"失敗: {failed}")
        print("="*50 + "\n")


def main():
    """主程式"""
    
    # 範例：要處理的 YouTube URL 列表
    youtube_urls = [
        "https://www.youtube.com/watch?v=BFudEmWtgAc",
        # 在這裡添加更多 URL
        "https://www.youtube.com/watch?v=atRmcTIwJ4o",
    ]
    
    # 建立批量處理器（每次請求間隔 1 秒）
    # Headers 和 Cookies 會自動從 config_headers.json 和 config_cookies.txt 載入
    processor = TurboScribeBatch(delay=1.0)
    
    # 執行批量處理
    results = processor.process_batch(youtube_urls)
    
    # 儲存結果
    processor.save_results(results, "turboscribe_results.json")
    
    # 顯示摘要
    processor.print_summary(results)
    
    # 顯示詳細結果
    print("詳細結果:")
    for result in results:
        print(f"\nURL: {result['url']}")
        print(f"狀態: {result['status']}")
        if result['status'] == 'success':
            print(f"HTML 檔案: {result.get('html_file', 'N/A')}")
            print(f"音訊檔案: {result.get('audio_file', 'N/A')}")
            print(f"回應預覽: {result['response'][:100]}...")  # 只顯示前 100 字元
        else:
            print(f"錯誤: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    main()
