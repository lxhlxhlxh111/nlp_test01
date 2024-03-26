import sqlite3

# Connect to or create a database file
connection = sqlite3.connect('example.db')

# Create a cursor object to execute SQL statements
cursor = connection.cursor()

# Define a SQL statement to create a table
create_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    email TEXT
);
"""

# Execute the query
cursor.execute(create_table_query)

# Commit the changes to the database
connection.commit()
