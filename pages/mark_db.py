import os
import sqlite3
import streamlit as st
from openai import OpenAI
from datetime import datetime  # 追加: 日付操作用

# ページ設定
st.set_page_config(page_title="Marketing AI Analyst", layout="centered")

# ==========================================
# 0. アプリ概要の表示
# ==========================================
st.title("Marketing AI Analyst 📈")
st.markdown("""
このチャットボットは、**広告運用および顧客獲得データ**に接続されています。
以下のようなデータについて質問できます。

* 📊 **広告実績 (AdPerformance)**: Google/Yahoo等の媒体別実績、表示回数、コスト、CPAなど
* 👥 **顧客獲得 (CustomerAcquisition)**: 流入元(UTM)別の新規獲得数、予約数、受任数

**質問例:**
* 「先月のGoogle広告のCPAはいくら？」
* 「媒体ごとの獲得件数を比較して」
* 「キャンペーンAからの予約数は？」""")
st.divider()

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
# 2. プロンプト定義 (スキーマ情報 + 日付指示)
# ==========================================

# 今日の日付を取得 (YYYY-MM-DD形式)
current_date = datetime.now().strftime("%Y-%m-%d")

DB_SCHEMA_PROMPT = """
あなたは経験豊富なマーケティングデータアナリストです。
以下のテーブル定義を参考にして、ユーザーの質問に対するSQLを生成してください。

CREATE TABLE "AdPerformance" (
    "date" TEXT,          -- 日付 (YYYY-MM-DD)
    "media_type" TEXT,    -- 媒体 (Google, Yahooなど)
    "account_type" TEXT,  -- アカウント/ブランド名
    "impressions" INTEGER,-- 表示回数
    "clicks" INTEGER,     -- クリック数
    "conversions" INTEGER,-- コンバージョン(獲得)数
    "cost" REAL,          -- 費用(コスト)
    "month" INTEGER,      -- 月
    "year" INTEGER        -- 年
);

CREATE TABLE "CustomerAcquisition" (
    "date" TEXT,          -- 日付 (YYYY-MM-DD)
    "utm_medium" TEXT,    -- 媒体 (cpc, organic, snsなど)
    "utm_source" TEXT,    -- ソース (google, yahoo, instagramなど)
    "utm_campaign" TEXT,  -- キャンペーン名
    "y_new" INTEGER,      -- 新規リード数
    "y_yoyaku" INTEGER,   -- 予約数
    "y_junin" INTEGER     -- 受任(成約)数
);

**重要ルール**:
1. 日付カラム `date` は 'YYYY-MM-DD' 文字列形式です。
2. **日付計算**: 「今日」「先月」「直近30日」などの指示があった場合は、後述する【現在の日付】を基準にSQLの `WHERE` 句を作成してください。
   - 例（先月）: `WHERE date BETWEEN date('now', 'start of month', '-1 month') AND date('now', 'start of month', '-1 day')` ※SQLite関数を使用、または文字列比較で範囲指定を行ってください。
   - SQLiteでは `strftime` や文字列比較が有効です。例: `date LIKE '2023-11%'`
3. CPA（獲得単価）の計算: `SUM(cost) / NULLIF(SUM(conversions), 0)`
4. 出力: 説明なしで、実行可能なSQLクエリ（SELECT文）のみを返してください。
""".strip()

RESPONSE_GENERATION_PROMPT_TEMPLATE = """
以下の【データ】に基づき、ユーザーの問い合わせに対する適切な回答を作成してください。

回答作成のガイドライン:
1. **目的の確認:** ユーザーの質問意図を理解する。
2. **結果の分析:** SQL実行結果から数値を読み取り、増減や傾向を分析する。
3. **回答の構成:** 「現在の日付（{current_date}）時点でのデータによると...」のように、いつの時点の情報かを意識して回答する。

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
if user_input := st.chat_input("質問を入力してください（例：先月の媒体別CPAを教えて）"):

    # ユーザーの質問を表示
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        # --- Phase 1: SQL生成 ---
        with st.spinner("データを分析中..."):
            try:
                # APIに「今日の日付」を伝えるメッセージを追加
                messages_for_sql = [
                    {"role": "system", "content": DB_SCHEMA_PROMPT},
                    {"role": "system", "content": f"【システム情報】現在の日付は {current_date} です。ユーザーが「今月」や「先月」と言った場合、この日付を基準にしてください。"},
                    {"role": "user", "content": user_input}
                ]

                sql_response = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=messages_for_sql,
                )
                generated_sql = sql_response.choices[0].message.content
                
                # SQLから余計な装飾（Markdownなど）があれば除去
                generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

                # --- Phase 2: SQL実行 ---
                db_path = "marketing.db"
                
                if not os.path.exists(db_path):
                    st.error(f"データベース '{db_path}' が見つかりません。DB作成スクリプトを実行してください。")
                    st.stop()

                with sqlite3.connect(db_path) as conn:
                    cursor = conn.execute(generated_sql)
                    columns = [description[0] for description in cursor.description]
                    query_results = cursor.fetchall()
                    
                    formatted_results = [dict(zip(columns, row)) for row in query_results]

                # --- Phase 3: 自然言語での回答生成 ---
                final_prompt = RESPONSE_GENERATION_PROMPT_TEMPLATE.format(
                    question=user_input,
                    sql=generated_sql,
                    context=str(formatted_results),
                    current_date=current_date # テンプレートにも日付を渡す
                )

                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "あなたはマーケティングデータのアシスタントです。"},
                        {"role": "user", "content": final_prompt}
                    ],
                )
                natural_language_answer = final_response.choices[0].message.content

                # 結果の表示
                st.write(natural_language_answer)
                
                # デバッグ用情報
                with st.expander(f"詳細データ（基準日: {current_date}）"):
                    st.code(generated_sql, language="sql")
                    st.write("検索結果:", formatted_results)

            except sqlite3.Error as e:
                st.error(f"SQL実行エラー: {e}")
                st.warning(f"生成されたSQL: {generated_sql}")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
