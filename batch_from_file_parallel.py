"""從檔案讀取 URL 並批量處理（並行下載音檔版本）"""

from turboscribe_batch import TurboScribeBatch
import sys
import concurrent.futures
import logging

logger = logging.getLogger(__name__)


def read_urls_from_file(filename: str) -> list:
    """
    從檔案讀取 URL（每行一個）
    
    Args:
        filename: 檔案名稱
        
    Returns:
        URL 列表
    """
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳過空行和註解
                if line and not line.startswith('#'):
                    urls.append(line)
        return urls
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 '{filename}'")
        sys.exit(1)


class ParallelAudioDownloader:
    """並行下載音檔的處理器"""
    
    def __init__(self, processor: TurboScribeBatch, max_workers: int = 3):
        """
        初始化
        
        Args:
            processor: TurboScribeBatch 實例
            max_workers: 最大並行下載數量（建議 2-4 個）
        """
        self.processor = processor
        self.max_workers = max_workers
    
    def download_audio_task(self, result: dict) -> dict:
        """
        單個音檔下載任務
        
        Args:
            result: 包含 URL 和音訊連結的結果字典
            
        Returns:
            更新後的結果字典
        """
        if result['status'] == 'success' and result.get('audio_link'):
            video_id = self.processor._extract_video_id(result['url'])
            audio_file = self.processor._download_audio(result['audio_link'], video_id)
            result['audio_file'] = audio_file
        return result
    
    def process_with_parallel_download(self, urls: list) -> list:
        """
        處理 URLs 並並行下載音檔
        
        Args:
            urls: URL 列表
            
        Returns:
            結果列表
        """
        # 第一步：獲取所有音訊連結（需要順序執行以遵守 API 限制）
        print(f"步驟 1/2: 獲取 {len(urls)} 個音訊連結...")
        results = []
        for idx, url in enumerate(urls, 1):
            print(f"  進度: {idx}/{len(urls)}")
            result = self.processor.process_single_url(
                url, 
                save_html=True, 
                download_audio=False  # 先不下載，只獲取連結
            )
            
            # 提取音訊連結
            if result['status'] == 'success' and result.get('response'):
                audio_link = self.processor._extract_audio_link(result['response'])
                result['audio_link'] = audio_link
            
            results.append(result)
            
            # 延遲（除了最後一個）
            if idx < len(urls):
                import time
                time.sleep(self.processor.delay)
        
        # 第二步：並行下載所有音檔
        print(f"\n步驟 2/2: 並行下載音檔（最多 {self.max_workers} 個同時下載）...")
        download_tasks = [r for r in results if r['status'] == 'success' and r.get('audio_link')]
        
        if download_tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有下載任務
                future_to_result = {
                    executor.submit(self.download_audio_task, result): result 
                    for result in download_tasks
                }
                
                # 收集結果
                completed = 0
                for future in concurrent.futures.as_completed(future_to_result):
                    completed += 1
                    result = future.result()
                    print(f"  完成: {completed}/{len(download_tasks)} - {result.get('audio_file', '失敗')}")
        
        print("\n✓ 所有任務完成！")
        return results


def main():
    # 從 urls.txt 讀取 URL
    urls = read_urls_from_file('urls.txt')
    
    if not urls:
        print("錯誤: urls.txt 中沒有找到任何 URL")
        sys.exit(1)
    
    print(f"從 urls.txt 讀取到 {len(urls)} 個 URL\n")
    
    # 建立處理器
    processor = TurboScribeBatch(delay=1.0)
    
    # 建立並行下載器（同時下載 3 個音檔）
    parallel_downloader = ParallelAudioDownloader(processor, max_workers=3)
    
    # 執行處理（獲取連結 + 並行下載）
    results = parallel_downloader.process_with_parallel_download(urls)
    
    # 儲存結果
    processor.save_results(results, "turboscribe_results_parallel.json")
    
    # 顯示摘要
    processor.print_summary(results)
    
    # 顯示 HTML 檔案列表
    print("\n儲存的 HTML 檔案:")
    for result in results:
        if result['status'] == 'success' and 'html_file' in result:
            print(f"  - {result['html_file']}")
    
    # 顯示音訊檔案列表
    print("\n下載的音訊檔案:")
    audio_count = 0
    for result in results:
        if result['status'] == 'success' and result.get('audio_file'):
            print(f"  - {result['audio_file']}")
            audio_count += 1
    
    print(f"\n總計成功下載 {audio_count} 個音訊檔案")


if __name__ == "__main__":
    main()
