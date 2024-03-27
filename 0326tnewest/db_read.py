import sqlite3

# 连接到 SQLite 数据库
conn = sqlite3.connect('user_infos.db')

# 创建一个游标对象
cursor = conn.cursor()

# 执行 SQL 查询，获取所有表的列表
# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

# # 获取查询结果
# tables = cursor.fetchall()

# # 打印所有表的列表
# for table in tables:
#     print(table[0])


cursor.execute("SELECT * FROM user_infos;")
rows = cursor.fetchall()
for row in rows:
    print(row)
# 关闭游标和连接
cursor.close()
conn.close()
