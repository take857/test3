import os
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
import streamlit as st

# AIのキャラクターを決めるシステムメッセージ
system_message_chat_conversation = """
あなたは経験豊富なデータアナリストです。
以下のテーブル定義を参考にして、ユーザーの質問に対するDataverse SQL を生成・実行して回答してください。
生成するDataverse SQLは、指定されたテーブルとカラムのみを使用し、正確で効率的でDataverseがサポートしている内容である必要があります。Dataverse SQLで期間を指定する際は絶対的な期間指定をお願いします。

【スキーマ情報】
--- テーブル定義 ---
- テーブル名: cr187_koutuu
  説明: Web広告の指標を格納するテーブル
  カラム:
  - cr187_koutuuId StringType- 一意識別子,
  - cr187_date DateType - 広告の配信日, 
  - cr187_impressions IntegerType - 広告の表示回数, 
  - cr187_clicks IntegerType- 広告のクリック数, 
  - cr187_cost DoubleType- 広告費,
  - cr187_medium StringType- 広告のメディア。Google, Yahooなど,
  - cr187_account StringType- 事業ドメイン
  - cr187_column08 - 新規登録された顧客数
  - cr187_column09 - 予約した顧客数
  - cr187_column10 - 受任意志を示した顧客数
  - cr187_column11 - 受任契約をした顧客数

【ルール】
1. DataverseのTDSエンドポイントで実行可能なSQL構文を使用してください。
2. SELECT文のみを生成してください。UPDATEやDELETEは禁止です。
3. 必要に応じてJOINを使用してください。
4. Dataverse SQL 内で日付を使う場合、絶対的な日付を使用してください。

"""


# ユーザーの質問に対し回答を生成する関数を定義する。
def search(history):
    # [{"role": "user", "content", "質問文"}, {"role": "assistant", "content": "回答"}]のようなjsonから
    # 末尾のcontentを取得する
    question = history[-1].get("content")

    try:
        azure_secrets = st.secrets["azure"]
    # Azure AI SearchのAPIに接続するためのクライアントを生成する
        search_client = SearchClient(
                endpoint = azure_secrets["SEARCH_SERVICE_ENDPOINT"],
                index_name = azure_secrets["SEARCH_SERVICE_INDEX_NAME"],
                credential = AzureKeyCredential(azure_secrets["SEARCH_SERVICE_API_KEY"])
        )

        # Azure OpenAIのAPIに接続するためのクライアントを生成する
        openai_client = AzureOpenAI(
            azure_endpoint = azure_secrets["AOAI_ENDPOINT"],
            api_key = azure_secrets["AOAI_API_KEY"],
            api_version = azure_secrets["AOAI_API_VERSION"]
        )

        # Azure OpenAIのAPIに接続するためのクライアントを生成する
        openai_client_gpt4o = AzureOpenAI(
            azure_endpoint = azure_secrets["AOAI_GPT4O_ENDPOINT"],
            api_key = azure_secrets["AOAI_GPT4O_API_KEY"],
            api_version = azure_secrets["AOAI_GPT4O_API_VERSION"]
        )
    except(KeyError, FileNotFoundError):
        st.error("接続情報ありません。")
        st.stop()

    # ユーザーからの質問をベクトルかする
    response = openai_client.embeddings.create(
        input = question,
        model = azure_secrets["AOAI_EMBEDDING_MODEL_NAME"]
    )
    # レスポンスがNoneでないか確認する
    if response is None:
        # 適切にエラーを処理する
        print("API呼び出しが失敗しました。")
        return "すみません、質問の処理中にエラーが発生しました。"

    # ベクトル化された質問を Azure AI Searchに対し検索するためのクエリを生成する
    vector_query = VectorizedQuery(
        vector = response.data[0].embedding,
        k_nearest_neighbor = 3,
        fields = "contentVector"
    )

    # ベクトル化された質問を用いて、Azure AI Searchに対してベクトル検索を行う。
    results = search_client.search(
        vector_queries = [vector_query],
        select = ["id", "content"]
    )

    # チャット履歴の中からユーザーの質問に対する回答を生成するためのメッセージを生成する
    messages = []

    # システムメッセージを追加する
    messages.insert(0, {
        "role": "system",
        "content": system_message_chat_conversation
    })

    # Azure AI Searchから取得した内容を追加する
    sources = ["[Source" + result["id"] + "]:" + result["content"] for result in results]
    source = "\n".join(sources)

    # ユーザーの質問と情報源を含むメッセージを生成する
    user_message = """
    {query}

    Sources:
    {source}
    """.format(query=question, source=source)

    # メッセージを追加する
    messages.append({"role": "user", "content": user_message})

    # Azure Open AI Serviceに回答生成依頼を生成する
    response = openai_client_gpt4o.chat.completions.create(
        model = "gpt-4o-mini",
        messages = messages
    )
    answer = response.choices[0].message.content

    return answer



# 画面を構築するためのコード
if "history" not in st.session_state:
    st.session_state["history"] = [{"role": "assistant",
                                    "content": "こんにちは、私は仮想アシスタントです。データベースについて回答します。"}]

# チャット履歴を表示する
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ユーザーが質問を入力した時の処理
if prompt := st.chat_input("質問を入力してください。"):

    # ユーザーが入力した質問を表示する
    with st.chat_message("user"):
        st.write(prompt)
    
    # ユーザーの質問をチャット履歴に追加する
    st.session_state.history.append({"role": "user", "content": prompt})

    # ユーザーの質問に対して回答を生成するためにsearch関数を呼び出す
    response = search(st.session_state.history)

    # 回答を表示する
    with st.chat_message("assistant"):
        st.write(response)
    
    # 回答をチャット履歴に追加する
    st.session_state.history.append({"role": "assistant", "content": response})

