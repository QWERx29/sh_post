import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from openpyxl import Workbook
from urllib.parse import urljoin

BASE_URL = "https://zwfw.spb.gov.cn/sj/310000/pfyycsml?currentPage={}"
ROOT = "https://zwfw.spb.gov.cn"

# 配置 headers（模拟浏览器）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://zwfw.spb.gov.cn/",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1"
}
# 建立带重试机制的 Session
session = requests.Session()
session.headers.update(headers)
retries = Retry(
    total=5,
    backoff_factor=2,                    # 失败后退避间隔：1s,2s,4s...
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"]
)
adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
session.mount("https://", adapter)
session.mount("http://", adapter)

# 如果你在 CI 或公司网络遇到证书问题，可以临时设为 False（不推荐长期使用）
VERIFY_SSL = True

wb = Workbook()
ws = wb.active
ws.append(["所属省", "所属市", "所属县", "场所名称", "开办业务", "详情链接"])

def safe_get(url, max_attempts=3, timeout=(10, 30)):
    """带额外异常处理的 GET，返回 text 或 None"""
    for attempt in range(1, max_attempts + 1):
        try:
            resp = session.get(url, headers=headers, timeout=timeout, verify=VERIFY_SSL)
            # 如果状态码不在 200-399，抛出异常触发重试逻辑
            resp.raise_for_status()
            # 确保正确编码
            resp.encoding = resp.apparent_encoding
            return resp.text
        except requests.exceptions.RequestException as e:
            print(f"[请求失败] {url} （尝试 {attempt}/{max_attempts}）: {e}")
            # 退避后重试
            sleep_seconds = 1.5 ** attempt
            time.sleep(sleep_seconds)
        except Exception as e:
            print(f"[未知错误] {url} ：{e}")
            time.sleep(1)
    print(f"[放弃] 多次重试后仍失败：{url}")
    return None

def parse_page(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    # 选择 table 中的 tr（视页面实际结构调整）
    rows = soup.select("table tr")
    if not rows:
        # 有时表格的类名不同或 JS 渲染，打印提示
        print(f"[警告] 未找到 table tr：{page_url}")
        return

    for tr in rows[1:]:  # 跳过表头（若无表头则要小心）
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        a_tags = [td.find("a") for td in tds[:5]]
        if any(a is None for a in a_tags):
            continue

        province = a_tags[0].get_text(strip=True)
        city = a_tags[1].get_text(strip=True)
        district = a_tags[2].get_text(strip=True)
        place_name = a_tags[3].get_text(strip=True)
        services = a_tags[4].get_text(strip=True)
        detail_link = urljoin(ROOT, a_tags[0]["href"])

        ws.append([province, city, district, place_name, services, detail_link])

def main():
    for page in range(1, 27 + 1):
        url = BASE_URL.format(page)
        print("抓取页面：", url)
        html = safe_get(url)
        if html is None:
            # 跳过此页而不是终止整个抓取
            continue
        parse_page(html, url)
        # 礼貌等待，避免触发防爬
        time.sleep(0.8)

    out = "current.xlsx"
    wb.save(out)
    print("完成，已写入：", out)

if __name__ == "__main__":
    main()
