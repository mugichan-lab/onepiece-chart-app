import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse

# ==========================================
# ページ設定 (ワイド表示)
# ==========================================
st.set_page_config(page_title="トレカ最新相場チャート", page_icon="📈", layout="wide")

# カスタムCSS (カード風の見た目をリッチにする)
st.markdown("""
    <style>
    .card-title { font-size: 14px; font-weight: bold; margin-bottom: 5px; height: 40px; overflow: hidden; }
    .price-market { font-size: 24px; font-weight: bold; color: #ff4b4b; margin: 0; }
    .price-list { font-size: 12px; color: #888; text-decoration: line-through; }
    .premium-tag { background-color: #ff4b4b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold;}
    .discount-tag { background-color: #09ab3b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.title("📈 トレカ最新相場チャート")
st.markdown("フリマアプリの実際の取引データに基づいた最新の相場情報です。")

# ==========================================
# データベース接続
# ==========================================
SUPABASE_URI = "postgresql://postgres.oywznddjjehwzfckljsy:Mugichan123454321@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"

# 代表的な画像 (見つからない場合は自動で名前入りのプレースホルダーを生成)
IMAGE_DICT = {
    "ワンピースカード 新たなる皇帝 (OP-09)": "https://placehold.jp/150x150.png?text=OP-09",
    "ワンピースカード 二つの伝説 (OP-08)": "https://placehold.jp/150x150.png?text=OP-08",
    "ポケモンカード 151": "https://placehold.jp/150x150.png?text=151",
}

@st.cache_data(ttl=60)
def load_data():
    engine = create_engine(SUPABASE_URI)
    # ★定価(list_price)も一緒に読み込むように修正
    df = pd.read_sql("SELECT timestamp, name, list_price, market_price FROM price_history", engine)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df_history = load_data()

if df_history.empty:
    st.warning("クラウドのデータベースは現在空っぽです。管理ソフトからAI相場取得を実行してください。")
else:
    # 各商品の「最新データ」と「1つ前のデータ」を抽出して一覧表を作る
    latest_data = []
    for name, group in df_history.groupby('name'):
        group = group.sort_values('timestamp', ascending=False)
        if len(group) > 0:
            current_price = group.iloc[0]['market_price']
            list_price = group.iloc[0]['list_price']
            previous_price = group.iloc[1]['market_price'] if len(group) > 1 else current_price
            diff = current_price - previous_price
            last_updated = group.iloc[0]['timestamp']
            
            # 定価に対するプレ値（％）を計算
            premium_rate = 0
            if list_price and list_price > 0:
                premium_rate = ((current_price - list_price) / list_price) * 100

            # 画像URLの取得 (辞書になければダミー画像を生成)
            img_url = IMAGE_DICT.get(name, f"https://placehold.jp/150x150.png?text={urllib.parse.quote(name[:6])}")
            
            latest_data.append({
                'name': name,
                'current_price': current_price,
                'list_price': list_price,
                'diff': diff,
                'premium_rate': premium_rate,
                'last_updated': last_updated,
                'img_url': img_url
            })
            
    df_latest = pd.DataFrame(latest_data)

    # ==========================================
    # コントロールパネル (ソートと検索)
    # ==========================================
    col_search, col_sort = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 商品名で絞り込み", "")
    with col_sort:
        sort_option = st.selectbox(
            "並び替え",
            ["最新更新順", "価格が高い順", "価格が低い順", "プレ値率が高い順"]
        )

    # フィルタリング適用
    if search_query:
        df_latest = df_latest[df_latest['name'].str.contains(search_query, case=False, na=False)]

    # ソート適用
    if sort_option == "最新更新順":
        df_latest = df_latest.sort_values('last_updated', ascending=False)
    elif sort_option == "価格が高い順":
        df_latest = df_latest.sort_values('current_price', ascending=False)
    elif sort_option == "価格が低い順":
        df_latest = df_latest.sort_values('current_price', ascending=True)
    elif sort_option == "プレ値率が高い順":
        df_latest = df_latest.sort_values('premium_rate', ascending=False)

    st.markdown("---")

    # ==========================================
    # グリッドレイアウトでのカード表示
    # ==========================================
    # 1行あたり4列で表示する
    cols_per_row = 4
    for i in range(0, len(df_latest), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(df_latest):
                item = df_latest.iloc[i + j]
                
                # Streamlit 1.30以降の枠付きコンテナを使用
                with cols[j].container(border=True):
                    # 画像を中心にして表示
                    st.image(item['img_url'], use_container_width=True)
                    
                    # 商品名
                    st.markdown(f"<div class='card-title'>{item['name']}</div>", unsafe_allow_html=True)
                    
                    # 定価と現在の相場
                    list_p = f"¥{int(item['list_price']):,}" if item['list_price'] > 0 else "不明"
                    st.markdown(f"<span class='price-list'>定価: {list_p}</span>", unsafe_allow_html=True)
                    
                    # プレ値タグ
                    if item['list_price'] > 0:
                        if item['premium_rate'] > 0:
                            st.markdown(f"<span class='premium-tag'>+{int(item['premium_rate'])}% プレ値</span>", unsafe_allow_html=True)
                        elif item['premium_rate'] < 0:
                            st.markdown(f"<span class='discount-tag'>{int(item['premium_rate'])}% 定価割れ</span>", unsafe_allow_html=True)
                    
                    # メトリクス（現在の価格と前日比）
                    st.metric(
                        label="現在相場", 
                        value=f"¥{int(item['current_price']):,}", 
                        delta=f"{int(item['diff']):,}円 (前回比)" if item['diff'] != 0 else "変動なし"
                    )
                    st.caption(f"🕒 {item['last_updated'].strftime('%m/%d %H:%M')}")
                    
                    # クリックして詳細チャートを見るためのボタン（展開アコーディオン）
                    with st.expander("詳細チャートを見る"):
                        df_selected = df_history[df_history['name'] == item['name']].sort_values('timestamp')
                        st.line_chart(data=df_selected.set_index('timestamp')['market_price'], height=150)