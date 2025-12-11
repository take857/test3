import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. データベース接続の設定 ---

DB_NAME = "Chinook.db"

# @st.cache_resource は削除！
def get_connection(db_name):
    """
    データベースへの新しい接続を作成します。
    （接続は使用後に呼び出し元で閉じる必要があります。）
    """
    try:
        # 接続を作成
        conn = sqlite3.connect(db_name)
        return conn
    except Exception as e:
        st.error(f"データベース接続エラー: {e}")
        return None

# 初期テーブル作成（初回実行時のみ。動作確認用）
# setup_database関数内では、渡されたconnを commit/close する必要はありません。
def setup_database(conn):
    # ... (変更なし) ...
    try:
        cursor = conn.cursor()
        # テーブルが存在しない場合のみ作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER
            )
        """)
        # 初期データ挿入
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
            cursor.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
            conn.commit()
            st.toast("初期テーブル (users) とデータを作成しました。", icon='✅')
    except Exception as e:
        st.error(f"データベース初期設定エラー: {e}")


# --- 2. Streamlitページのメイン処理 ---

def sql_runner_page():
    st.title("🗄️ SQLクエリ実行ページ")
    st.markdown(f"**接続データベース:** `{DB_NAME}` (SQLite)")

    # setup_databaseのための一時的な接続
    temp_conn = get_connection(DB_NAME)

    if temp_conn is None:
        st.stop()

    # 初回実行時にデータベースのセットアップを行う
    setup_database(temp_conn)
    temp_conn.close() # ★ セットアップが終わったら接続を閉じる

    # ユーザーがクエリを入力するためのテキストエリア
    # ... (変更なし) ...
    default_query = "SELECT * FROM users"
    sql_query = st.text_area(
        "実行したいSQLクエリを入力してください:",
        value=default_query,
        height=150
    )

    # 実行ボタン
    if st.button("クエリを実行", type="primary"):
        if not sql_query.strip():
            st.warning("SQLクエリを入力してください。")
            return

        query_type = sql_query.strip().split()[0].upper()

        # ★ ここで新しい接続を作成する (最も重要な修正点)
        conn = get_connection(DB_NAME)
        if conn is None:
            return
            
        try:
            if query_type in ["SELECT", "PRAGMA"]:
                # 参照クエリの場合
                # pandasのread_sqlを使用して、結果をDataFrameとして取得
                df = pd.read_sql(sql_query, conn) # ここで新しい接続を使用
                
                st.success("クエリ実行成功！ (参照)")
                st.dataframe(df, use_container_width=True)
                st.info(f"取得行数: {len(df.index)}行")

            elif query_type in ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP"]:
                # 変更クエリの場合
                cursor = conn.cursor()
                cursor.execute(sql_query)
                conn.commit() # 変更を確定
                
                rowcount = cursor.rowcount if cursor.rowcount >= 0 else 0
                
                st.success(f"クエリ実行成功！ (変更) - 影響行数: {rowcount}行")
                
            else:
                # その他のクエリ（例: ALTERなど）の場合
                cursor = conn.cursor()
                cursor.execute(sql_query)
                conn.commit()
                st.success("クエリ実行成功！")

        except Exception as e:
            # エラー発生時の処理
            st.error("クエリ実行エラーが発生しました。")
            st.exception(e)

        finally:
            # ★ 処理が終わったら必ず接続を閉じる
            conn.close() 

# ページ処理を実行
sql_runner_page()

