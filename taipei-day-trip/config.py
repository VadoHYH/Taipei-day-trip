import os
from dotenv import load_dotenv
from pathlib import Path

# 明確指定 .env 的位置（與啟動檔同目錄）
env_path = Path(__file__).resolve().parent / ".env"

load_dotenv()  # 載入環境變數

SECRET_KEY = os.getenv("SECRET_KEY", "default-fallback-key")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7

MERCHANT_KEY=os.getenv("MERCHANT_KEY", "")
PARTNER_KEY = os.getenv("PARTNER_KEY", "") 

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "taipei_trip")

print("DB_USER =", DB_USER)
print("DB_PASSWORD =", DB_PASSWORD)