import streamlit as st
import sys

# 画面のタイトルを設定
st.title('私のStreamlitアプリ')

# ここに表示したい要素（ウィジェット）を追加します。
# 例1: テキストの表示
st.write('これはシンプルなテキストです。')

# 例2: ボタンの追加とその反応
if st.button('押してみて'):
    st.write('ボタンが押されました！')

# 例3: スライダーの追加
age = st.slider('あなたの年齢', 0, 100, 25)
st.write('あなたの年齢は', age, '歳です。')

# 例4: サイドバーの追加
st.sidebar.header('設定')
st.sidebar.text_input('ユーザー名', 'ゲスト')

# などの要素を追加できます...
