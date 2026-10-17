import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="ワンピチャート(仮)", page_icon="🏴‍☠️", layout="wide")

st.title("🏴‍☠️ ワンピチャート(仮) - ワンピースカード最新相場")
st.markdown("フリマアプリの実際の取引データに基づいた最新の相場情報と価格推移です。")

# ==========================================
# ★追加: 商品名と画像URLを結びつける辞書
# （実際はここにAmazonや公式のパッケージ画像URLを貼り付けます）
# ==========================================
IMAGE_DICT = {
    "ワンピースカード 新たなる皇帝 (OP-09)": "https://shop.r10s.jp/14promo/cabinet/imgrc0101844548.jpg",
    "ワンピースカード 二つの伝説 (OP-08)": "https://placehold.jp/100x100.png?text=OP-08",
    "ワンピースカード 500年後の未来 (OP-07)": "https://placehold.jp/100x100.png?text=OP-07",
    "ワンピースカード 双璧の覇者 (OP-06)": "https://placehold.jp/100x100.png?text=OP-06",
    "ワンピースカード 新時代の主役 (OP-05)": "https://placehold.jp/100x100.png?text=OP-05",
}
# リストにない商品用の「NO IMAGE」画像
DEFAULT_IMAGE = "https://placehold.co/100x100/eeeeee/999999?text=NO+IMAGE"


@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect("tcg_data.db")
    df_history = pd.read_sql("SELECT timestamp, name, market_price FROM price_history", conn)
    conn.close()
    df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
    return df_history

df_history = load_data()
df_op_history = df_history[df_history['name'].str.contains("ワンピース", na=False)]

if df_op_history.empty:
    st.warning("まだワンピースカードの相場履歴が保存されていません。元の管理ソフトで相場を取得してください。")
else:
    latest_data = []
    for name, group in df_op_history.groupby('name'):
        group = group.sort_values('timestamp', ascending=False)
        if len(group) > 0:
            current_price = group.iloc[0]['market_price']
            previous_price = group.iloc[1]['market_price'] if len(group) > 1 else current_price
            diff = current_price - previous_price
            
            # ★追加: 画像URLを辞書から取得（なければNO IMAGEをセット）
            img_url = IMAGE_DICT.get(name, DEFAULT_IMAGE)
            
            latest_data.append({
                '画像': img_url,      # ★追加
                '商品名': name,
                '現在の相場': current_price,
                '前日比': diff,
                '最終更新': group.iloc[0]['timestamp'].strftime("%Y-%m-%d %H:%M")
            })
            
    df_latest = pd.DataFrame(latest_data).sort_values('現在の相場', ascending=False).reset_index(drop=True)

    st.markdown("### 📊 BOXごとの詳細推移")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### アイテム選択")
        selected_item = st.selectbox("確認したいBOXを選んでください", df_latest['商品名'].tolist(), label_visibility="collapsed")
        
        item_info = df_latest[df_latest['商品名'] == selected_item].iloc[0]
        
        # ★追加: 選択されたアイテムの画像を左サイドにも表示
        st.image(item_info['画像'], width=150)
        
        st.metric(
            label="最新の取引相場", 
            value=f"¥{item_info['現在の相場']:,}", 
            delta=f"{int(item_info['前日比']):,}円"
        )
        st.caption(f"最終取得日時: {item_info['最終更新']}")

    with col2:
        df_selected = df_op_history[df_op_history['name'] == selected_item].sort_values('timestamp')
        st.line_chart(data=df_selected.set_index('timestamp')['market_price'], height=250)

    st.markdown("---")

    st.markdown("### 📋 最新相場一覧（ランキング）")
    
    def color_diff(val):
        if val > 0:
            return 'color: #ff4b4b'
        elif val < 0:
            return 'color: #09ab3b'
        return 'color: gray'

    styled_df = df_latest.style.format({
        '現在の相場': '¥{:,}',
        '前日比': '{:+,}円'
    }).map(color_diff, subset=['前日比'])
    
    # ★追加: column_configを使って「画像」列を本物の画像として表示するように指示
    st.dataframe(
        styled_df, 
        column_config={
            "画像": st.column_config.ImageColumn("パッケージ", width="small")
        },
        use_container_width=True, 
        hide_index=True
    )