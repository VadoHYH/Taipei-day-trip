from fastapi import APIRouter, Query, HTTPException,Request,Response
from fastapi.responses import JSONResponse
from database import get_db_connection
from datetime import datetime, timedelta
from jose import jwt, JWTError
from config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_DAYS
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import bcrypt
import re


router = APIRouter()

@router.get("/api/attractions")
def get_attraction(
    page: int = Query(0, alias="page", ge=0),
    keyword: str = Query(None, alias="keyword")):

    try:
        per_page = 12
        offset = page * per_page

        conn = get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="無法連接到資料庫")

        cursor = conn.cursor()

        # SQL 查詢，使用 JOIN 一次取得所有資訊
        sql = """
            SELECT a.id, a.name, a.category, a.description, a.address, a.transport, 
                   a.mrt, a.lat, a.lng, GROUP_CONCAT(ai.image_url) AS images
            FROM attractions a
            LEFT JOIN attraction_images ai ON a.id = ai.attraction_id
        """
        params = []

        if keyword:
            sql += " WHERE a.name LIKE %s OR a.mrt = %s"
            params.extend([f"%{keyword}%", keyword])

        sql += " GROUP BY a.id, a.name, a.category, a.description, a.address, a.transport, a.mrt, a.lat, a.lng"
        sql += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(sql, tuple(params))
        attractions = cursor.fetchall()

        # 轉換圖片格式
        for attraction in attractions:
            attraction["images"] = attraction["images"].split(",") if attraction["images"] else []

        # 查詢總數
        count_sql = "SELECT COUNT(*) AS total FROM attractions"
        if keyword:
            count_sql += " WHERE name LIKE %s OR mrt = %s"
            cursor.execute(count_sql, (f"%{keyword}%", keyword))
        else:
            cursor.execute(count_sql)

        total_count = cursor.fetchone()["total"]
        next_page = page + 1 if (page + 1) * per_page < total_count else None

        cursor.close()
        conn.close()

        return {"nextPage": next_page, "data": attractions}

    except Exception as e:
        return {"error": True, "message": f"伺服器錯誤: {str(e)}"}

@router.get("/api/attractions/{id}")
def get_attractions_id( id : int):
    try:
        conn = get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500,detail="無法連接資料庫")
        
        cursor = conn.cursor()

        # 查詢指定 ID 的景點
        sql = """
            SELECT a.id, a.name, a.category, a.description, a.address, a.transport, 
                   a.mrt, a.lat, a.lng, GROUP_CONCAT(ai.image_url) AS images
            FROM attractions a
            LEFT JOIN attraction_images ai ON a.id = ai.attraction_id
            WHERE a.id = %s
            GROUP BY a.id, a.name, a.category, a.description, a.address, a.transport, a.mrt, a.lat, a.lng
        """
        cursor.execute(sql, (id,))
        attraction = cursor.fetchone()

        # 如果景點不存在，回傳 400
        if not attraction:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="景點編號不正確")

        # 處理圖片格式
        attraction["images"] = attraction["images"].split(",") if attraction["images"] else []

        cursor.close()
        conn.close()

        return {"data": attraction}
    
    except Exception as e:
        return {"error": True, "message": f"伺服器錯誤: {str(e)}"}

@router.get("/api/mrts")
def get_mrts():
    try:
        conn = get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="無法連接到資料庫")
        
        cursor = conn.cursor()

        # 查詢 MRT 站點其對應景點數
        sql = """
            SELECT mrt, COUNT(*) as attraction_count
            FROM attractions
            WHERE mrt IS NOT NULL
            GROUP BY mrt
            ORDER BY attraction_count DESC
        """

        cursor.execute(sql)
        mrts = [row["mrt"] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {"data":mrts}

    except Exception as e:
        return {"error": True,"message":f"伺服器錯誤: {str(e)}"}

@router.post("/api/user")
async def post_user(request: Request):
    try:
        data = await request.json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not name or not email or not password:
            return JSONResponse(status_code=400, content={
                "error": True,
                "message": "請提供完整的註冊資訊"
            })

        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_pattern, email):
            return JSONResponse(status_code=400, content={
                "error": True,
                "message": "請輸入有效的 Email 格式"
            })

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            return JSONResponse(status_code=400, content={
                "error": True,
                "message": "該 Email 已被註冊"
            })

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        conn.commit()

        cursor.close()
        conn.close()

        return {"ok": True}

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "error": True,
            "message": f"伺服器錯誤: {str(e)}"
        })

@router.get("/api/user/auth")
def get_user_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(content={"data": None}, status_code=401)
    
    token = auth_header.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            return JSONResponse(content={"data": None}, status_code=401)
    except (ExpiredSignatureError, InvalidTokenError):
        return JSONResponse(content={"data": None}, status_code=401)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return JSONResponse(content={"data": None}, status_code=401)
    
    return JSONResponse(
        content={"data": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }},
        status_code=200
    )

@router.put("/api/user/auth")
async def put_user_auth(request: Request):
    try:
        data = await request.json()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not email or not password:
            return JSONResponse(status_code=400, content={
                "error": True,
                "message": "請提供 Email 和密碼"
            })

        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_pattern, email):
            return JSONResponse(status_code=400, content={
                "error": True,
                "message": "請輸入有效的 Email 格式"
            })

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            return JSONResponse(status_code=400, content={
                "error": True,
                "message": "Email 或密碼錯誤"
            })

        expiration = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
        payload = {
            "user_id": user["id"],
            "exp": expiration
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return JSONResponse(status_code=200, content={
            "data": {"token": token}
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "error": True,
            "message": f"伺服器錯誤: {str(e)}"
        })
