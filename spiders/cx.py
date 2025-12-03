from openpyxl import Workbook
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://sh.spb.gov.cn/shsyzglj/c100057/c100058/common_list.shtml"
ROOT = "https://sh.spb.gov.cn"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://zwfw.spb.gov.cn/",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1"
}

wb = Workbook()
ws = wb.active
ws.append(["标题", "发布日期", "链接"])

def get_soup(url):
    r = requests.get(url, headers=headers, timeout=10)
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, "html.parser")

soup = get_soup(URL)

# li 中的结构非常统一：<p>标题</p> 和 <span>日期</span>
for li in soup.select("li"):
    a = li.find("a")
    if not a:
        continue

    title_tag = a.find("p")
    date_tag = a.find("span")

    if not title_tag or not date_tag:
        continue

    title = title_tag.get_text(strip=True)
    date = date_tag.get_text(strip=True)
    link = urljoin(ROOT, a["href"])

    # 只匹配含“撤销”
    if "撤销" in title:
        ws.append([title, date, link])
        print("命中:", title)

wb.save("cx.xlsx")
print("抓取完成，已生成 result.xlsx")
