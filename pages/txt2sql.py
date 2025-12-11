import os
from openai import OpenAI
import streamlit as st

# StreamlitのシークレットからAPIキーを取得
# secrets = st.secrets["OPENAI_API_KEY"] # 元の行。環境変数からの取得と併用しない場合はコメントアウトまたは削除。

# 1. OpenAIクライアントの初期化
# Streamlitのシークレット (st.secrets) からAPIキーを取得して使用します。
# もし環境変数 'OPENAI_API_KEY' も設定されている場合は、そちらも使用可能です。
# Streamlit Cloudでデプロイする場合は、st.secretsの使用が推奨されます。

try:
    # st.secrets から API キーを取得
    api_key = st.secrets["OPENAI_API_KEY"]
except KeyError:
    # st.secrets にない場合は、環境変数から取得を試みる (ローカル実行用など)
    api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    st.error("OpenAI APIキーが設定されていません。Streamlitのシークレットまたは環境変数に 'OPENAI_API_KEY' を設定してください。")
    st.stop() # キーがない場合は処理を停止

client = OpenAI(
    api_key=api_key,
)

# 2. データベースのスキーマ定義
# AIに特定のデータベースに関する質問をさせる場合、ここにスキーマ情報やInstructionsを追記します。
# 例: system_prompt = "あなたはデータベースの専門家です。提供されたスキーマ情報に基づいて、ユーザーの質問に回答してください。スキーマ: [ここにスキーマ情報]"
# 今回は一般的な会話AIとして動作させるため、この部分はそのままにします。
system_prompt = "あなたは親切で役立つAIアシスタントです。ユーザーの質問に丁寧に回答してください。"

# 3. 画面を構築するためのコード
# ユーザーが質問を入力した時の処理
if prompt := st.chat_input("質問を入力してください。"):

    # ユーザーが入力した質問を表示する
    with st.chat_message("user"):
        st.write(prompt)

    # 4. アシスタントの応答を生成
    with st.chat_message("assistant"):
        # スピナーを表示して、処理中であることをユーザーに伝える
        with st.spinner("AIが回答を生成中です..."):
            try:
                # OpenAI API を呼び出す
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # 使用するモデルを指定 (例: gpt-4, gpt-4o, gpt-3.5-turbo)
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7 # 応答のランダム性 (0.0〜2.0)
                )
                
                # AIの回答を取得
                ai_response = response.choices[0].message.content
                
                # AIの回答を表示
                st.write(ai_response)
                
            except Exception as e:
                st.error(f"OpenAI APIの呼び出し中にエラーが発生しました: {e}")
                st.write("申し訳ありませんが、回答を生成できませんでした。")
