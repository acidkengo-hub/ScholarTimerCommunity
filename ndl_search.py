import requests
import xml.etree.ElementTree as ET

# --- OPAC風 検索条件設定 ---
TITLE = "草枕"           # 書名
AUTHOR = "夏目漱石"        # 著者名
PUBLISHER = "岩波書店"     # 出版社（★追加！）
FROM_YEAR = "1950"       # 出版年（開始）（★追加！）
UNTIL_YEAR = "2000"      # 出版年（終了）（★追加！）

def fetch_ndl_books_advanced():
    print(f"📡 【詳細検索】書名:『{TITLE}』 著者:{AUTHOR} 出版社:{PUBLISHER} ({FROM_YEAR}年〜{UNTIL_YEAR}年)")
    print("国会図書館に問い合わせ中...\n")

    # 1. NDLサーチAPIのURL（条件を & でどんどん繋いでいく！）
    api_url = (
        f"https://ndlsearch.ndl.go.jp/api/opensearch"
        f"?title={TITLE}"
        f"&creator={AUTHOR}"
        f"&publisher={PUBLISHER}"
        f"&from={FROM_YEAR}"
        f"&until={UNTIL_YEAR}"
    )

    response = requests.get(api_url)
    root = ET.fromstring(response.text)
    namespaces = {'dc': 'http://purl.org/dc/elements/1.1/'}

    # 上から10件取り出す（少し多めにしました）
    items = root.findall('.//item')[:10]

    if not items:
        print("条件に一致する本は見つかりませんでした。")
        return

    # 見つけた本を1冊ずつ表示
    for i, item in enumerate(items, 1):
        # タイトル
        title_elem = item.find('title')
        book_title = title_elem.text if title_elem is not None else "タイトル不明"
        
        # 出版社（dc:publisher）
        pub_elem = item.find('dc:publisher', namespaces)
        publisher = pub_elem.text if pub_elem is not None else "出版社不明"
        
        # 出版年（dc:date）
        date_elem = item.find('dc:date', namespaces)
        date = date_elem.text if date_elem is not None else "不明"
        
        print(f"📚 {i}冊目: 『{book_title}』")
        print(f"    ▶ 出版社: {publisher} / 出版年: {date}\n")

if __name__ == "__main__":
    fetch_ndl_books_advanced()