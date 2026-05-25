import os
import pymssql
from dotenv import load_dotenv

load_dotenv()

try:
    print("Connecting to 45.120.139.237 (no port)...")
    conn = pymssql.connect(
        server=os.environ.get("MSSQL_HOST"),
        user=os.environ.get("MSSQL_USER"),
        password=os.environ.get("MSSQL_PASSWORD"),
        timeout=10
    )
    print("Connected! Listing databases...")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.databases")
    for row in cursor:
        print(f" - {row[0]}")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
