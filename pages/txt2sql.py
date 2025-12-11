import os
from openai import OpenAI

# 1. 環境変数からAPIキーを取得
# 環境変数名：OPENAI_API_KEY
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# 2. データベースのスキーマ定義
# ここをあなたのデータベースに合わせて変更してください
DATABASE_SCHEMA = """
CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY,
    product_name TEXT,
    revenue REAL,
    sale_date TEXT
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT,
    category TEXT
);
"""

def text_to_sql(natural_language_query: str) -> str:
    """
    OpenAI APIを使用して自然言語の質問からSQLクエリを生成します。
    """
    prompt = f"""
    あなたはSQLエキスパートです。以下のデータベーススキーマに基づいて、
    ユーザーの質問に正確に合致するSQLiteのSQLクエリ（SELECT文）のみを生成してください。
    その他の説明や文章は一切含めないでください。

    --- データベーススキーマ ---
    {DATABASE_SCHEMA}
    ---

    --- ユーザーの質問 ---
    {natural_language_query}
    ---

    生成されるSQL:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # または gpt-4o, gpt-3.5-turboなど
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": natural_language_query}
            ],
            temperature=0.0 # 創造性よりも正確性を優先
        )
        # 生成されたSQLクエリを取得
        sql_query = response.choices[0].message.content.strip()
        return sql_query

    except Exception as e:
        return f"エラーが発生しました: {e}"

# 3. 実行例
user_question = "昨日（2025-12-10）の売上が最も高かった製品の名前を教えて"
generated_sql = text_to_sql(user_question)

print(f"質問: {user_question}")
print(f"生成されたSQL:\n{generated_sql}")
