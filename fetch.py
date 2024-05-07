import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

# 目标网页的URL
url = 'https://www.centbrowser.cn/history.html'

# 设置请求头部，模拟浏览器User-Agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}
while True:
    # 发送HTTP GET请求
    response = requests.get(url, headers=headers)
    
    # 确保请求成功
    if response.status_code == 200:
        # 使用BeautifulSoup解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到所有的exe和apk下载链接
        download_links = []
    
        # 寻找exe下载链接，假设它们在class为"download-link"的a标签中
        # 由于您只想要便携版的链接，这里我们可以根据文本内容来过滤
        for link in soup.find_all('a'):
            if "便携版" in link.text:
                href = link.get('href')
                text = link.text.strip()
                # 确保链接是exe文件
                if href.endswith('.exe'):
                    download_links.append({'href': urljoin(url, href), 'text': text})
        
        # 将下载链接保存到一个JSON文件中
        with open('data.json', 'w') as f:
            json.dump(download_links, f, indent=4)
        
        print("Portable download links have been updated.")
        break
    else:
        print("Failed to retrieve the webpage. Status code:", response.status_code)
        continue
