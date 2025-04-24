import os
from dotenv import load_dotenv

load_dotenv()  # 載入環境變數

SECRET_KEY = os.getenv("SECRET_KEY", "default-fallback-key")  # 若環境變數未設置，則使用備用值
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7

MERCHANT_KEY=os.getenv("MERCHANT_KEY", "Vadohyh_CTBC")

PARTNER_KEY = "partner_IUVM060Pn8TyybxpvyDItaPiv4vv5622ruZHPIOJThxmS3AtnS35igfC"

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "vadomysql")#vadomysql#ec2wehelpmysql
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "taipei_trip")

ATTRACTION_API_URL= os.getenv("apiUrl", "http://127.0.0.1:8000/api/attractions/${attractionId}")