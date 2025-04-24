from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

# 建立 SQLAlchemy 引擎（內建 connection pool）
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
    pool_size=10,            # 最多連線數
    max_overflow=5,          # 超出 pool_size 時額外的連線數
    pool_pre_ping=True,      # 每次連線前測試是否還活著（避免 timeout）
    pool_recycle=3600,       # 每小時重啟一次連線（避免 MySQL timeout）
    echo=False,              # 可改 True 來看 SQL log
    future=True              # 使用 SQLAlchemy 2.0 API
)

# 提供一個連線（需手動關閉）
def get_db_connection() -> Connection:
    return engine.connect()