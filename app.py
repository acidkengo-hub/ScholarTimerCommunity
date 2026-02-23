import streamlit as st
import requests
import xml.etree.ElementTree as ET
from supabase import create_client, Client
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 🔑 Supabaseの接続設定 ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- ⏱️ 24時間稼働のグローバル・タイマー（1秒ごとに画面を更新） ---
st_autorefresh(interval=1000, key="global_timer")

def get_global_pomodoro_state():
    now = datetime.now()
    m = now.minute
    s = now.second
    
    # 0〜24分、30〜54分は「集中タイム」
    if m < 25:
        return "🔥 集中タイム", 24 - m, 59 - s, "#fff5f5", "#d9534f"
    elif m < 30:
        return "☕️ 休憩タイム", 29 - m, 59 - s, "#f0f8ff", "#5bc0de"
    elif m < 55:
        return "🔥 集中タイム", 54 - m, 59 - s, "#fff5f5", "#d9534f"
    else:
        return "☕️ 休憩タイム", 59 - m, 59 - s, "#f0f8ff", "#5bc0de"

mode, r_min, r_sec, bg_color, text_color = get_global_pomodoro_state()

# タイマーのUI（見た目）
st.markdown(f"""
<div style="background-color: {bg_color}; padding: 30px; border-radius: 15px; text-align: center; border: 2px solid {text_color}; margin-bottom: 20px;">
    <h3 style="color: {text_color}; margin: 0;">現在のポモドーロ列車</h3>
    <h1 style="color: {text_color}; font-size: 70px; margin: 10px 0; font-family: monospace;">{r_min:02d}:{r_sec:02d}</h1>
    <h2 style="color: {text_color}; margin: 0;">{mode}</h2>
</div>
""", unsafe_allow_html=True)

# --- 画面のUI（見た目）を作る ---
st.title("📚 仮想図書室：NDL検索 ＆ 乗車")
st.write("検索した本をタスクとしてセットし、ポモドーロ列車に乗車（記録）します。")

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

if st.button("🔍 詳細検索を実行"):
    if not any([title_input, author_input, publisher_input, from_year_input, until_year_input]):
        st.warning("⚠️ 検索条件を少なくとも一つ入力してください！")
    else:
        raw_params = {
            "title": title_input,
            "creator": author_input,
            "publisher": publisher_input,
            "from": from_year_input,
            "until": until_year_input
        }
        st.session_state.search_params = {k: v for k, v in raw_params.items() if v}

# ---------- 検索結果の表示と、Supabaseへの記録 ----------
if st.session_state.search_params:
    st.markdown("---")
    selected_page = st.selectbox("📄 ページを選択 (1ページ20件表示)", range(1, 21))
    st.info(f"{selected_page}ページ目を読み込み中...")

    api_params = st.session_state.search_params.copy()
    api_params["cnt"] = 20 
    api_params["idx"] = (selected_page - 1) * 20 + 1 

    api_url = "https://ndlsearch.ndl.go.jp/api/opensearch"
    response = requests.get(api_url, params=api_params)
    
    root = ET.fromstring(response.text)
    namespaces = {'dc': 'http://purl.org/dc/elements/1.1/'}
    items = root.findall('.//item')

    if not items:
        st.warning("このページには本が見つかりませんでした。")
    else:
        st.success(f"検索結果を表示しています。（現在: {selected_page}ページ目）")
        
        for i, item in enumerate(items, 1):
            title_elem = item.find('title')
            book_title = title_elem.text if title_elem is not None else "タイトル不明"
            
            pub_elem = item.find('dc:publisher', namespaces)
            publisher = pub_elem.text if pub_elem is not None else "出版社不明"
            
            date_elem = item.find('dc:date', namespaces)
            date = date_elem.text if date_elem is not None else "不明"
            
            total_index = api_params["idx"] + i - 1
            
            with st.container(border=True):
                st.subheader(f"{total_index}. {book_title}")
                st.write(f"🏢 出版社: {publisher}  |  📅 出版年: {date}")
                
                # 【新機能】Supabaseの金庫にデータを投げ込むボタン
                if st.button(f"🍅 「{book_title}」の執筆を記録 (25分)", key=f"btn_{total_index}"):
                    try:
                        # Supabaseの 'pomodoro_logs' テーブルにデータを挿入
                        supabase.table('pomodoro_logs').insert({
                            "task_name": book_title,
                            "duration_seconds": 1500  # 25分 * 60秒
                        }).execute()
                        
                        st.success(f"🎉 記録完了！金庫に「{book_title}」の1ポモドーロを保存しました！")
                        st.balloons() # 成功したら風船を飛ばす！
                    except Exception as e:
                        st.error(f"⚠️ 保存に失敗しました: {e}")