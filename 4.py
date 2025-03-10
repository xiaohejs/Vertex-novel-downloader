import requests
from lxml import etree
import os
import concurrent.futures
from tqdm import tqdm
import time
import random

# 随机选择请求头
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
]

REFERERS = [
    "https://www.ddyucshu.cc/",
    "https://www.baidu.com/",
    "https://www.google.com/",
    "https://www.bing.com/"
]

# 请求头随机选择
def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": random.choice(REFERERS),
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

BASE_URL = "https://m.ddyucshu.cc/"

# 输入小说ID获取章节列表**
def get_chapters(novel_id):
    url = f"{BASE_URL}{novel_id}"
    headers = get_random_headers()
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求章节目录失败: {e}")
        return []

    html = etree.HTML(response.text)

    dt_elements = html.xpath('//dt[contains(text(), "正文")]')
    if not dt_elements:
        raise ValueError("未找到包含'正文'的章节列表")

    # 获取所有章节链接
    chapter_list = []
    for dt in dt_elements:
        links = dt.xpath('./following-sibling::dd/a')
        for link in links:
            chapter_title = link.text.strip()
            chapter_url = link.get("href")
            if not chapter_url.startswith("http"):
                chapter_url = BASE_URL + chapter_url.lstrip("/")
            chapter_list.append((chapter_title, chapter_url))

    return chapter_list

#爬取单个章节
def download_chapter(chapter):
    chapter_title, chapter_url = chapter
    retries = 3  # 重试次数
    for _ in range(retries):
        try:
            headers = get_random_headers()
            response = requests.get(chapter_url, headers=headers, timeout=10)
            response.raise_for_status()
            html = etree.HTML(response.text)

            content_div = html.xpath('//div[@id="content"]')[0]
            
            # 处理<br/>标签替换成换行符
            content_html = etree.tostring(content_div, encoding='unicode')
            content_text = content_html.replace('<br />', '\n')

            # 移除其他标签
            content_text = ' '.join(etree.HTML(content_text).xpath('//text()')).replace(' \n', '\n')

            if not content_text:
                print(f"❌ 章节 `{chapter_title}` 正文提取失败！")
                return chapter_title, None

            return chapter_title, content_text
        
        except requests.exceptions.RequestException as e:
            print(f"❌ 下载章节 `{chapter_title}` 失败: {e}")
            time.sleep(random.randint(5, 10))  # 增加延迟（5-10秒）再重试

    return chapter_title, None

#运行主程序
def main():
    while True:
        print("\n* 输入下面的数字进入其他功能 *")
        print("1. 直接输入ID（例如网址https://m.ddyucshu.cc/wapbook/20221439.html中只需要输入“20221439”即可")
        print("2. 赞助我们")
        print("3. 退出")

        choice = input("请输入选项: ")
        if choice == "1":
            novel_id = input("请输入小说 ID: ").strip()
            try:
                chapters = get_chapters(novel_id)
                if not chapters:
                    print("❌ 获取章节列表失败，请重试！")
                    continue

                novel_name = novel_id + ".txt"
                print(f"\n📖 发现 {len(chapters)} 章，开始下载...")

                # **多线程加速爬取**
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    results = list(tqdm(executor.map(download_chapter, chapters), total=len(chapters), desc="下载进度", unit="章"))

                # **保存到文件**
                with open(novel_name, "w", encoding="utf-8") as f:
                    for title, content in results:
                        if content:
                            f.write(f"\n{title}\n{'=' * 40}\n{content}\n")

                print(f"\n✅ 小说《{novel_id}》下载完成，保存在 {novel_name}")
            
            except Exception as e:
                print(f"❌ 下载失败: {e}")

        elif choice == "2":
            print("\n感谢你的支持！不过赞助就实在不用了哈。。。。")

        elif choice == "3":
            print("\n👋 退出程序！")
            break

        else:
            print("\n❌ 请输入正确的选项！")

if __name__ == "__main__":
    main()