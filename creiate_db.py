# databaseを作成
# https://kioku-space.com/langchain-text-to-sql/
import requests
import sqlite3
import pandas as pd


url = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql"

r = requests.get(url)

with open("Chinook_Sqlite.sql", "wb") as f:
    f.write(r.content)

# SQLiteデータベースのファイル名
db_file = 'Chinook.db'
sql_file = 'Chinook_Sqlite.sql'

# データベース接続を開く
with sqlite3.connect(db_file) as conn:
    cursor = conn.cursor()

    # SQLファイルを読み込む
    with open(sql_file, 'r', encoding='utf-8') as file:
        sql_script = file.read()

    # SQLスクリプトを実行する
    cursor.executescript(sql_script)

    # コミットしてデータベースを保存
    conn.commit()
