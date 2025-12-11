import os
import sqlite3
import streamlit as st
from openai import OpenAI

# ページ設定（オプション）
st.set_page_config(page_title="AI Data Analyst", layout="centered")

# ==========================================
# 1. セットアップと設定
# ==========================================

# APIキーの取得
try:
    api_key = st.secrets.get("OPENAI_API_KEY")
except (KeyError, FileNotFoundError):
    api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    st.error("OpenAI APIキーが設定されていません。st.secrets または環境変数を設定してください。")
    st.stop()

# OpenAIクライアントの初期化
client = OpenAI(api_key=api_key)

# ==========================================
# 2. プロンプト定義 (スキーマ情報)
# ==========================================

DB_SCHEMA_PROMPT = """
あなたは経験豊富なデータアナリストです。
以下のテーブル定義を参考にして、ユーザーの質問に対するSQLを生成してください。

CREATE TABLE "Album" (
    "AlbumId" INTEGER NOT NULL, 
    "Title" NVARCHAR(160) NOT NULL, 
    "ArtistId" INTEGER NOT NULL, 
    PRIMARY KEY ("AlbumId"), 
    FOREIGN KEY("ArtistId") REFERENCES "Artist" ("ArtistId")
);

CREATE TABLE "Artist" (
    "ArtistId" INTEGER NOT NULL, 
    "Name" NVARCHAR(120), 
    PRIMARY KEY ("ArtistId")
);

CREATE TABLE "Customer" (
    "CustomerId" INTEGER NOT NULL, 
    "FirstName" NVARCHAR(40) NOT NULL, 
    "LastName" NVARCHAR(20) NOT NULL, 
    "Company" NVARCHAR(80), 
    "Address" NVARCHAR(70), 
    "City" NVARCHAR(40), 
    "State" NVARCHAR(40), 
    "Country" NVARCHAR(40), 
    "PostalCode" NVARCHAR(10), 
    "Phone" NVARCHAR(24), 
    "Fax" NVARCHAR(24), 
    "Email" NVARCHAR(60) NOT NULL, 
    "SupportRepId" INTEGER, 
    PRIMARY KEY ("CustomerId"), 
    FOREIGN KEY("SupportRepId") REFERENCES "Employee" ("EmployeeId")
);

CREATE TABLE "Employee" (
    "EmployeeId" INTEGER NOT NULL, 
    "LastName" NVARCHAR(20) NOT NULL, 
    "FirstName" NVARCHAR(20) NOT NULL, 
    "Title" NVARCHAR(30), 
    "ReportsTo" INTEGER, 
    "BirthDate" DATETIME, 
    "HireDate" DATETIME, 
    "Address" NVARCHAR(70), 
    "City" NVARCHAR(40), 
    "State" NVARCHAR(40), 
    "Country" NVARCHAR(40), 
    "PostalCode" NVARCHAR(10), 
    "Phone" NVARCHAR(24), 
    "Fax" NVARCHAR(24), 
    "Email" NVARCHAR(60), 
    PRIMARY KEY ("EmployeeId"), 
    FOREIGN KEY("ReportsTo") REFERENCES "Employee" ("EmployeeId")
);

CREATE TABLE "Genre" (
    "GenreId" INTEGER NOT NULL, 
    "Name" NVARCHAR(120), 
    PRIMARY KEY ("GenreId")
);

CREATE TABLE "Invoice" (
    "InvoiceId" INTEGER NOT NULL, 
    "CustomerId" INTEGER NOT NULL, 
    "InvoiceDate" DATETIME NOT NULL, 
    "BillingAddress" NVARCHAR(70), 
    "BillingCity" NVARCHAR(40), 
    "BillingState" NVARCHAR(40), 
    "BillingCountry" NVARCHAR(40), 
    "BillingPostalCode" NVARCHAR(10), 
    "Total" NUMERIC(10, 2) NOT NULL, 
    PRIMARY KEY ("InvoiceId"), 
    FOREIGN KEY("CustomerId") REFERENCES "Customer" ("CustomerId")
);

CREATE TABLE "InvoiceLine" (
    "InvoiceLineId" INTEGER NOT NULL, 
    "InvoiceId" INTEGER NOT NULL, 
    "TrackId" INTEGER NOT NULL, 
    "UnitPrice" NUMERIC(10, 2) NOT NULL, 
    "Quantity" INTEGER NOT NULL, 
    PRIMARY KEY ("InvoiceLineId"), 
    FOREIGN KEY("TrackId") REFERENCES "Track" ("TrackId"), 
    FOREIGN KEY("InvoiceId") REFERENCES "Invoice" ("InvoiceId")
);

CREATE TABLE "MediaType" (
    "MediaTypeId" INTEGER NOT NULL, 
    "Name" NVARCHAR(120), 
    PRIMARY KEY ("MediaTypeId")
);

CREATE TABLE "Playlist" (
    "PlaylistId" INTEGER NOT NULL, 
    "Name" NVARCHAR(120), 
    PRIMARY KEY ("PlaylistId")
);

CREATE TABLE "PlaylistTrack" (
    "PlaylistId" INTEGER NOT NULL, 
    "TrackId" INTEGER NOT NULL, 
    PRIMARY KEY ("PlaylistId", "TrackId"), 
    FOREIGN KEY("TrackId") REFERENCES "Track" ("TrackId"), 
    FOREIGN KEY("PlaylistId") REFERENCES "Playlist" ("PlaylistId")
);

CREATE TABLE "Track" (
    "TrackId" INTEGER NOT NULL, 
    "Name" NVARCHAR(200) NOT NULL, 
    "AlbumId" INTEGER, 
    "MediaTypeId" INTEGER NOT NULL, 
    "GenreId" INTEGER, 
    "Composer" NVARCHAR(220), 
    "Milliseconds" INTEGER NOT NULL, 
    "Bytes" INTEGER, 
    "UnitPrice" NUMERIC(10, 2) NOT NULL, 
    PRIMARY KEY ("TrackId"), 
    FOREIGN KEY("MediaTypeId") REFERENCES "MediaType" ("MediaTypeId"), 
    FOREIGN KEY("GenreId") REFERENCES "Genre" ("GenreId"), 
    FOREIGN KEY("AlbumId") REFERENCES "Album" ("AlbumId")
);

**重要**: あなたは、ユーザーの質問に対し、このスキーマに基づくSQLiteのSQLクエリ（SELECT文）のみを生成してください。その他の説明は一切含めないでください。Markdownのコードブロック(```sql ... ```)も含めず、純粋なSQLのみを返してください。
""".strip()

RESPONSE_GENERATION_PROMPT_TEMPLATE = """
以下の【データ】に基づき、ユーザーの問い合わせに対する適切な回答を作成してください。

回答を作成する際は、以下のステップとガイドラインに従ってください。

### 回答作成のためのガイドライン
1. **目的の確認:** 【データ】内の「ユーザーの問い合わせ」の意図を正確に理解する。
2. **結果の分析:** 【データ】内の「実行されたSQL」と「SQLの返り値」を分析し、問いに答えるために必要な情報を抽出する。
3. **回答の構成:** SQLの返り値をそのまま表示するのではなく、ユーザーが**理解しやすい自然な言葉**（日本語）で結論や必要な情報を提示する。
4. **情報の明確化:** 必要に応じて、どのデータが何を示しているかを明確に伝える。

---
### 【データ】
#### ユーザーの問い合わせ
{question}

#### 実行されたSQL
{sql}

#### SQLの実行結果
{context}
""".strip()

# ==========================================
# 3. アプリケーションロジック
# ==========================================

# ユーザーからの入力を受け取る
if user_input := st.chat_input("質問を入力してください。"):

    # ユーザーの質問を表示
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        
        try:
            # --- Phase 1: SQL生成 ---
            with st.spinner("データベースを確認中..."):
                sql_response = client.chat.completions.create(
                    model="gpt-4o",  # gpt-5-nano は未公開のため gpt-4o に変更 (必要に応じて変更可)
                    messages=[
                        {"role": "system", "content": DB_SCHEMA_PROMPT},
                        {"role": "user", "content": user_input}
                    ],
                )
                generated_sql = sql_response.choices[0].message.content
                
                # SQLから余計な装飾（Markdownなど）があれば除去する簡易処理
                generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

            # --- Phase 2: SQL実行 ---
            # DB接続には with 構文を使用して確実に閉じる
            db_path = "Chinook.db"
            if not os.path.exists(db_path):
                 st.error(f"データベースファイル '{db_path}' が見つかりません。")
                 st.stop()

            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(generated_sql)
                query_results = cursor.fetchall()

            # --- Phase 3: 自然言語での回答生成 ---
            with st.spinner("回答を作成中..."):
                final_prompt = RESPONSE_GENERATION_PROMPT_TEMPLATE.format(
                    question=user_input,
                    sql=generated_sql,
                    context=query_results
                )

                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "あなたはデータに基づき、ユーザーにわかりやすく日本語で答えるアシスタントです。"},
                        {"role": "user", "content": final_prompt}
                    ],
                )
                natural_language_answer = final_response.choices[0].message.content

            # 結果の表示
            st.write(natural_language_answer)
            
            # デバッグ用情報（エキスパンダーに隠す）
            with st.expander("詳細データを見る（SQLと生の検索結果）"):
                st.code(generated_sql, language="sql")
                st.write("検索結果:", query_results)

        except sqlite3.Error as e:
            st.error(f"SQL実行エラー: {e}")
            st.warning(f"生成されたSQL: {generated_sql}")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
