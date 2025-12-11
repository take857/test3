import os
from openai import OpenAI
import streamlit as st

secrets = st.secrets["OPENAI_API_KEY"]

# 1. 環境変数からAPIキーを取得
# 環境変数名：OPENAI_API_KEY
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# 2. データベースのスキーマ定義
# ここをあなたのデータベースに合わせて変更してください
# 画面を構築するためのコード
# ユーザーが質問を入力した時の処理
if prompt := st.chat_input("質問を入力してください。"):

    # ユーザーが入力した質問を表示する
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        st.write(prompt + "ですね")
