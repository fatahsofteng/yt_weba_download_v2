"""從檔案讀取 URL 並批量處理"""

from turboscribe_batch import TurboScribeBatch
import sys


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


def main():
    # 從 urls.txt 讀取 URL
    urls = read_urls_from_file('urls.txt')
    
    if not urls:
        print("錯誤: urls.txt 中沒有找到任何 URL")
        sys.exit(1)
    
    print(f"從 urls.txt 讀取到 {len(urls)} 個 URL\n")
    print("提示: 下載已優化 - 支援大檔案、顯示進度、超時時間延長至10分鐘")
    print("如需更快速度，請使用 batch_from_file_parallel.py (支援並行下載)\n")
    
    # 建立處理器並執行
    # Headers 和 Cookies 會自動從 config_headers.json 和 config_cookies.txt 載入
    processor = TurboScribeBatch(delay=1.0)
    results = processor.process_batch(urls, save_html=True, download_audio=True)  # 自動儲存 HTML 和下載音訊
    
    # 儲存結果
    processor.save_results(results, "turboscribe_results.json")
    
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
