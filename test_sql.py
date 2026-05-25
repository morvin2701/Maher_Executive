import os
import pymssql
from dotenv import load_dotenv

load_dotenv()

try:
    print("Connecting to 45.120.139.237...")
    conn = pymssql.connect(
        server=os.environ.get("MSSQL_HOST"),
        port=os.environ.get("MSSQL_PORT"),
        user=os.environ.get("MSSQL_USER"),
        password=os.environ.get("MSSQL_PASSWORD"),
        timeout=5
    )
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.databases")
    print("Connected! Available databases:")
    for row in cursor:
        print(f" - {row[0]}")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
