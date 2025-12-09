import os
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
import streamlit as st

# AIのキャラクターを決めるシステムメッセージ
system_message_chat_conversation = """
あなたはユーザーの質問に回答するチャットボットです。
「Sources:」以下に記載されている内容に基づいて簡潔に回答してください。
「Source:」に記載されている情報以外の回答はしないでください。
情報が複数ある場合は「Sources:」の後に[Source1], [Source2], [Source3]のように記載されますので、それに基づいて回答してください。
また、ユーザーの質問に対して、Source以下に記載されている内容に基づいて適切な回答ができない場合は、「すみません。わかりません。」と回答してください。
回答の中に情報源の提示は含めないでください。例えば、回答の中に「[Source1]」や「[Source:]」という形で情報源を示すことはしないでください。
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
    st.session_state["history"] = ["DBについて回答します。"]

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

