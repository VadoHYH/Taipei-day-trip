import os
from dotenv import load_dotenv

load_dotenv()  # 載入環境變數

SECRET_KEY = os.getenv("SECRET_KEY", "default-fallback-key")  # 若環境變數未設置，則使用備用值
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7

PARTNER_KEY = "partner_IUVM060Pn8TyybxpvyDItaPiv4vv5622ruZHPIOJThxmS3AtnS35igfC"