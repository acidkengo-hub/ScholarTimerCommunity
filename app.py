import streamlit as st
import requests
import xml.etree.ElementTree as ET

# --- 画面のUI（見た目）を作る ---
st.title("📚 論文執筆サポート：NDL詳細検索")
st.write("国立国会図書館のデータベースから、条件を絞って本を検索します。")

# 【新技術】アプリの「記憶領域」を準備する
if "search_params" not in st.session_state:
    st.session_state.search_params = {}

col1, col2 = st.columns(2)
with col1:
    title_input = st.text_input("書名（例：草枕）", "")
with col2:
    author_input = st.text_input("著者名（例：夏目漱石）", "")

col3, col4, col5 = st.columns(3)
with col3:
    publisher_input = st.text_input("出版社（例：岩波書店）", "")
with col4:
    from_year_input = st.text_input("出版年:開始（例：1950）", "")
with col5:
    until_year_input = st.text_input("出版年:終了（例：2000）", "")

# 検索ボタンが押されたら、検索条件を「記憶」に保存する
if st.button("🔍 詳細検索を実行"):
    if not any([title_input, author_input, publisher_input, from_year_input, until_year_input]):
        st.warning("⚠️ 検索条件を少なくとも一つ入力してください！")
    else:
        # 入力された条件をまとめる
        raw_params = {
            "title": title_input,
            "creator": author_input,
            "publisher": publisher_input,
            "from": from_year_input,
            "until": until_year_input
        }
        # 空欄の条件を消して、綺麗な辞書にして記憶（session_state）に保存！
        st.session_state.search_params = {k: v for k, v in raw_params.items() if v}


# ---------- ここから下が「検索結果の表示」エリア ----------

# もし記憶の中に検索条件があれば（＝検索ボタンが1回でも押されていれば）
if st.session_state.search_params:
    st.markdown("---")
    
    # 【ページネーション機能】1〜15ページまで選べるプルダウンを作る
    selected_page = st.selectbox("📄 ページを選択 (1ページ10件表示)", range(1, 21))
    
    st.info(f"{selected_page}ページ目を読み込み中...")

    # NDL APIへのリクエストを作る
    api_params = st.session_state.search_params.copy()
    api_params["cnt"] = 20 # 1ページにつき10件取得
    api_params["idx"] = (selected_page - 1) * 20 + 1 # 取得開始位置（1ページ目は1、2ページ目は11...）

    # いざ、国会図書館へ通信！
    api_url = "https://ndlsearch.ndl.go.jp/api/opensearch"
    response = requests.get(api_url, params=api_params)
    
    root = ET.fromstring(response.text)
    namespaces = {'dc': 'http://purl.org/dc/elements/1.1/'}

    # （※API側で既に10件に絞られているので、ここでは全部取り出します）
    items = root.findall('.//item')

    if not items:
        st.warning("このページには本が見つかりませんでした。")
    else:
        st.success(f"検索結果を表示しています。（現在: {selected_page}ページ目）")
        
        # 見つけた本をWeb画面にカード風に表示する
        for i, item in enumerate(items, 1):
            title_elem = item.find('title')
            book_title = title_elem.text if title_elem is not None else "タイトル不明"
            
            pub_elem = item.find('dc:publisher', namespaces)
            publisher = pub_elem.text if pub_elem is not None else "出版社不明"
            
            date_elem = item.find('dc:date', namespaces)
            date = date_elem.text if date_elem is not None else "不明"
            
            # 全体での通し番号を計算する（2ページ目の最初は「11」になる魔法）
            total_index = api_params["idx"] + i - 1
            
            with st.container(border=True):
                st.subheader(f"{total_index}. {book_title}")
                st.write(f"🏢 出版社: {publisher}  |  📅 出版年: {date}")