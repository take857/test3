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
sql = "SELECT * FROM "
st.write(sql)
