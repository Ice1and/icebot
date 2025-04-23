# -*- coding: utf-8 -*-
from typing import List, Dict, Union
from sqlite3 import Connection


def query_table(conn: Connection, table_name: str) -> bool:
    cursor = conn.cursor()

    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    if cursor.execute(query, (table_name,)).fetchone() is None:
        cursor.close()
        return False
    else:
        cursor.close()
        return True


def create_table_if_not_exists(conn: Connection, table_name: str) -> None:
    cursor = conn.cursor()

    cursor.execute(
        f"""CREATE TABLE '{table_name}'(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role CHAR(10),
            content LONGTEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP /* 默认数据插入时的时间 */
        )"""
    )

    conn.commit()
    cursor.close()


# 查询最近的历史信息
def query_recent_history_message(conn: Connection, table_name: str) -> List[Union[any, Dict[str, str]]]:
    cursor = conn.cursor()
    recent_history_message = []

    if not query_table(conn, table_name):
        create_table_if_not_exists(conn, table_name)
    else:
        results = cursor.execute(
            f"SELECT role, content, timestamp FROM '{table_name}' ORDER BY timestamp DESC LIMIT 15"
        ).fetchall()
        # 倒置列表，[5, 4, 3, 2, 1] -> [1, 2, 3, 4, 5]
        for res in results[::-1]:
            recent_history_message.append(
                {
                    "role": res[0],
                    "content": res[1]
                }
            )

    cursor.close()
    return recent_history_message


def insert_messages_to_table(conn: Connection, table_name: str, messages: List[Dict[str, str]]) -> None:
    cursor = conn.cursor()

    cursor.executemany(
        f"INSERT INTO '{table_name}' (role, content, timestamp) VALUES (?, ?, ?)",
        [(message["role"], message["content"], message["timestamp"]) for message in messages]
    )

    conn.commit()
    cursor.close()