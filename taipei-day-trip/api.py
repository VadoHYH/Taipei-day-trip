from fastapi import APIRouter, Query, HTTPException,Request,Response
from fastapi.responses import JSONResponse
from database import get_db_connection
from datetime import datetime, timedelta
from config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_DAYS,PARTNER_KEY,MERCHANT_KEY
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import text
import jwt
import bcrypt
import re
import requests


router = APIRouter()

@router.get("/api/attractions")
def get_attraction(
    page: int = Query(0, alias="page", ge=0),
    keyword: str = Query(None, alias="keyword")):

    try:
        per_page = 12
        offset = page * per_page

        # 從 connection pool 獲取連線
        with get_db_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=500,detail="無法連接資料庫")
             
            # 構建基本 SQL 查詢
            sql = """
                SELECT a.id, a.name, a.category, a.description, a.address, a.transport, 
                       a.mrt, a.lat, a.lng, GROUP_CONCAT(ai.image_url) AS images
                FROM attractions a
                LEFT JOIN attraction_images ai ON a.id = ai.attraction_id
            """
            
            params = {}
            
            if keyword:
                sql += " WHERE a.name LIKE :keyword_like OR a.mrt = :keyword"
                params["keyword_like"] = f"%{keyword}%"
                params["keyword"] = keyword
            
            sql += " GROUP BY a.id, a.name, a.category, a.description, a.address, a.transport, a.mrt, a.lat, a.lng"
            sql += " LIMIT :per_page OFFSET :offset"
            params["per_page"] = per_page
            params["offset"] = offset
            
            # 使用 SQLAlchemy 的 text() 執行 SQL
            result = conn.execute(text(sql), params)
            
            # 正確處理 SQLAlchemy 結果集
            attractions = []
            for row in result:
                # 使用 ._mapping 或直接使用下標訪問
                attraction_dict = {}
                for key in row._mapping.keys():
                    attraction_dict[key] = row._mapping[key]
                attractions.append(attraction_dict)
            
            # 轉換圖片格式
            for attraction in attractions:
                attraction["images"] = attraction["images"].split(",") if attraction["images"] else []
            
            # 查詢總數
            count_sql = "SELECT COUNT(*) AS total FROM attractions"
            if keyword:
                count_sql += " WHERE name LIKE :keyword_like OR mrt = :keyword"
                count_result = conn.execute(text(count_sql), {
                    "keyword_like": f"%{keyword}%", 
                    "keyword": keyword
                })
            else:
                count_result = conn.execute(text(count_sql))
            
            # 正確處理 COUNT 結果
            row = count_result.fetchone()
            total_count = row[0]  # 使用下標訪問第一個欄位
            next_page = page + 1 if (page + 1) * per_page < total_count else None

        return {"nextPage": next_page, "data": attractions}

    except Exception as e:
        return {"error": True, "message": f"伺服器錯誤: {str(e)}"}

@router.get("/api/attractions/{id}")
def get_attractions_id(id:int):
    try:
        with get_db_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=500,detail="無法連接資料庫")


            # 查詢指定 ID 的景點
            sql = """
                SELECT a.id, a.name, a.category, a.description, a.address, a.transport, 
                    a.mrt, a.lat, a.lng, GROUP_CONCAT(ai.image_url) AS images
                FROM attractions a
                LEFT JOIN attraction_images ai ON a.id = ai.attraction_id
                WHERE a.id = :id
                GROUP BY a.id, a.name, a.category, a.description, a.address, a.transport, a.mrt, a.lat, a.lng
            """

            # 執行查詢
            result = conn.execute(text(sql), {"id": id})

            # 獲取結果
            attraction_row = result.fetchone()

            # 如果景點不存在，回傳 400
            if not attraction_row:
                raise HTTPException(status_code=400, detail="景點編號不正確")

            # 轉換結果為字典
            attraction = {}
            for key in attraction_row._mapping.keys():
                attraction[key] = attraction_row._mapping[key]

            # 處理圖片格式
            attraction["images"] = attraction["images"].split(",") if attraction["images"] else []

        return {"data": attraction}

    except Exception as e:
        return {"error": True, "message": f"伺服器錯誤: {str(e)}"}
    
@router.get("/api/mrts")
def get_mrts():
    try:
        # 使用 with 語句從 connection pool 獲取連線
        with get_db_connection() as conn:

            # 查詢 MRT 站點其對應景點數
            sql = """
                SELECT mrt, COUNT(*) as attraction_count
                FROM attractions
                WHERE mrt IS NOT NULL
                GROUP BY mrt
                ORDER BY attraction_count DESC
            """

         # 執行查詢
            result = conn.execute(text(sql))
            
            # 從結果中提取 mrt 欄位值
            mrts = []
            for row in result:
                mrts.append(row.mrt)

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

        # 使用 with 語句從 connection pool 獲取連線
        with get_db_connection() as conn:
            # 檢查 email 是否已被註冊
            check_sql = "SELECT id FROM users WHERE email = :email"
            result = conn.execute(text(check_sql), {"email": email})
            existing_user = result.fetchone()

            if existing_user:
                return JSONResponse(status_code=400, content={
                    "error": True,
                    "message": "該 Email 已被註冊"
                })

            # 密碼加密
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            
            # 插入新用戶
            insert_sql = "INSERT INTO users (name, email, password) VALUES (:name, :email, :password)"
            conn.execute(text(insert_sql), {
                "name": name,
                "email": email,
                "password": hashed_password
            })
            
            # 提交事務
            conn.commit()

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

    # 使用 with 語句從 connection pool 獲取連線
    with get_db_connection() as conn:
        # 使用 SQLAlchemy text 執行查詢
        sql = "SELECT id, name, email FROM users WHERE id = :user_id"
        result = conn.execute(text(sql), {"user_id": user_id})
        user = result.fetchone()

    if not user:
        return JSONResponse(content={"data": None}, status_code=401)
    
    return JSONResponse(
        content={"data": {
            "id": user.id,  # 使用點記法存取欄位
            "name": user.name,
            "email": user.email
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

        # 使用 with 語句從 connection pool 獲取連線
        with get_db_connection() as conn:
            # 查詢用戶
            sql = "SELECT id, name, email, password FROM users WHERE email = :email"
            result = conn.execute(text(sql), {"email": email})
            user = result.fetchone()

        # 檢查用戶是否存在及密碼是否正確
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            return JSONResponse(status_code=400, content={
                "error": True,
                "message": "Email 或密碼錯誤"
            })

        # 生成 JWT token
        expiration = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
        payload = {
            "user_id": user.id,  # 使用點記法訪問屬性
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

@router.get("/api/booking")
def get_booking(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return JSONResponse(status_code=403, content={"error": True, "message": "為提供授權 token"})
    
    try:
        payload = jwt.decode(token.split("Bearer ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except (ExpiredSignatureError, InvalidTokenError):
        return JSONResponse(status_code=403, content={"error": True, "message": "無效或過期的 token"})
    
    # 使用 with 語句從 connection pool 獲取連線
    with get_db_connection() as conn:
        # 查詢預訂資訊
        sql = """
            SELECT b.attraction_id, b.date, b.time, b.price, a.name, a.address, GROUP_CONCAT(ai.image_url) AS images
            FROM booking b
            JOIN attractions a ON b.attraction_id = a.id
            LEFT JOIN attraction_images ai ON a.id = ai.attraction_id
            WHERE b.user_id = :user_id
            GROUP BY b.attraction_id, b.date, b.time, b.price, a.name, a.address
        """
        result = conn.execute(text(sql), {"user_id": user_id})
        booking = result.fetchone()

    if not booking:
        return JSONResponse(status_code=200, content={"data": None})
    
    # 處理圖片 URL
    image_url = booking.images.split(",")[0] if booking.images else None
    
    return JSONResponse(status_code=200, content={
        "data": {
            "attraction": {
                "id": booking.attraction_id,
                "name": booking.name,
                "address": booking.address,
                "image": image_url
            },
            "date": booking.date.strftime("%Y-%m-%d") if hasattr(booking.date, "strftime") else booking.date,
            "time": booking.time,
            "price": booking.price
        }
    })

@router.post("/api/booking")
async def post_booking(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return JSONResponse(status_code=403, content={"error": True, "message": "為提供授權 token"})
    
    try:
        payload = jwt.decode(token.split("Bearer ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except (ExpiredSignatureError, InvalidTokenError):
        return JSONResponse(status_code=403, content={"error": True, "message": "無效或過期的 token"})
    
    try:
        data = await request.json()
        attraction_id = data.get("attractionId")
        date = data.get("date")
        time = data.get("time")
        price = data.get("price")

        if not all([attraction_id, date, time, price]):
            return JSONResponse(status_code=400, content={"error": True, "message": "預定資料不完整"})
        
        # 使用 with 語句從 connection pool 獲取連線
        with get_db_connection() as conn:
            # 檢查景點是否存在
            check_sql = "SELECT id FROM attractions WHERE id = :attraction_id"
            result = conn.execute(text(check_sql), {"attraction_id": attraction_id})
            if not result.fetchone():
                return JSONResponse(status_code=400, content={"error": True, "message": "無效的景點的 ID"})
            
            # 插入或更新預訂
            insert_sql = """
                INSERT INTO booking (user_id, attraction_id, date, time, price)
                VALUES (:user_id, :attraction_id, :date, :time, :price)
                ON DUPLICATE KEY UPDATE attraction_id = VALUES(attraction_id),
                                        date = VALUES(date),
                                        time = VALUES(time),
                                        price = VALUES(price)
            """
            conn.execute(text(insert_sql), {
                "user_id": user_id,
                "attraction_id": attraction_id,
                "date": date,
                "time": time,
                "price": price
            })

            # 提交事務
            conn.commit()

        return JSONResponse(status_code=200, content={"ok": True})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": f"伺服器錯誤: {str(e)}"})
    
@router.delete("/api/booking")
def delete_booking(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return JSONResponse(status_code=403, content={"error": True, "message": "未提供授權 token"})

    try:
        payload = jwt.decode(token.split("Bearer ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except (ExpiredSignatureError, InvalidTokenError):
        return JSONResponse(status_code=403, content={"error": True, "message": "無效或過期的 token"})
    
    try:
        # 使用 with 語句從 connection pool 獲取連線
        with get_db_connection() as conn:
            # 刪除預訂
            delete_sql = "DELETE FROM booking WHERE user_id = :user_id"
            conn.execute(text(delete_sql), {"user_id": user_id})
            
            # 提交事務
            conn.commit()

        return JSONResponse(status_code=200, content={"ok": True})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": f"伺服器錯誤: {str(e)}"})

#建立訂單並付款的 API
@router.post("/api/orders")
async def create_order(request: Request):
    try:
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return JSONResponse(status_code=403, content={"error": True, "message": "未登入系統，拒絕存取"})

        try:
            payload = jwt.decode(token.split("Bearer ")[1], SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload["user_id"]
        except Exception:
            return JSONResponse(status_code=403, content={"error": True, "message": "登入憑證錯誤"})

        body = await request.json()
        prime = body.get("prime")
        order = body.get("order", {})
        price = order.get("price")
        trip = order.get("trip", {})
        contact = order.get("contact", {})

        attraction = trip.get("attraction", {})
        attraction_id = attraction.get("id")
        date = trip.get("date")
        time = trip.get("time")
        name = contact.get("name")
        email = contact.get("email")
        phone = contact.get("phone")

        if not all([prime, price, attraction_id, date, time, name, email, phone]):
            return JSONResponse(status_code=400, content={"error": True, "message": "訂單資料不完整"})

        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            today = datetime.today().date()
            if selected_date < today:
                return JSONResponse(status_code=400, content={"error": True, "message": "請選擇今天或未來的日期"})
        except Exception:
            return JSONResponse(status_code=400, content={"error": True, "message": "無效的日期格式"})

        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        phone_pattern = r"^09\d{8}$"

        if not re.match(email_pattern, email):
            return JSONResponse(status_code=400, content={"error": True, "message": "聯絡人 Email 格式錯誤"})

        if not re.match(phone_pattern, phone):
            return JSONResponse(status_code=400, content={"error": True, "message": "聯絡人手機格式錯誤"})

        order_number = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

        with get_db_connection() as conn:
            trans = conn.begin()
            try:
                result = conn.execute(
                    text("""
                        INSERT INTO orders (user_id, attraction_id, date, time, price, contact_name, contact_email, contact_phone, status, order_number)
                        VALUES (:user_id, :attraction_id, :date, :time, :price, :name, :email, :phone, :status, :order_number)
                    """),
                    {
                        "user_id": user_id,
                        "attraction_id": attraction_id,
                        "date": date,
                        "time": time,
                        "price": price,
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "status": "UNPAID",
                        "order_number": order_number
                    }
                )
                order_id = result.lastrowid

                tappay_payload = {
                    "prime": prime,
                    "partner_key": PARTNER_KEY,
                    "merchant_id": MERCHANT_KEY,
                    "amount": price,
                    "details": "Taipei Trip",
                    "cardholder": {
                        "phone_number": phone,
                        "name": name,
                        "email": email
                    }
                }

                tappay_response = requests.post(
                    "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime",
                    headers={"Content-Type": "application/json", "x-api-key": PARTNER_KEY},
                    json=tappay_payload
                )
                tappay_result = tappay_response.json()
                print("TapPay 回傳結果：", tappay_result)

                if tappay_result.get("status") == 0:
                    conn.execute(text("UPDATE orders SET status='PAID' WHERE id=:order_id"), {"order_id": order_id})
                    conn.execute(text("DELETE FROM booking WHERE user_id = :user_id"), {"user_id": user_id})
                    payment_status = 0
                    message = "付款成功"
                else:
                    payment_status = tappay_result.get("status")
                    message = "付款失敗"

                trans.commit()

            except Exception as e:
                trans.rollback()
                raise e

        return JSONResponse(status_code=200, content={
            "data": {
                "number": str(order_number),
                "payment": {
                    "status": payment_status,
                    "message": message
                }
            }
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": str(e)})


# 取得訂單資訊的 API
@router.get("/api/order/{order_number}")
def get_order(order_number: str, request: Request):
    try:
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return JSONResponse(status_code=403, content={"error": True, "message": "未登入系統"})

        try:
            payload = jwt.decode(token.split("Bearer ")[1], SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload["user_id"]
        except Exception:
            return JSONResponse(status_code=403, content={"error": True, "message": "登入憑證錯誤"})

        with get_db_connection() as conn:
            query = text("""
                SELECT o.id, o.price, o.date, o.time, o.contact_name, o.contact_email, o.contact_phone, o.status,
                       a.id AS attraction_id, a.name, a.address,
                       (SELECT image_url FROM attraction_images WHERE attraction_id = a.id LIMIT 1) AS image
                FROM orders o
                JOIN attractions a ON o.attraction_id = a.id
                WHERE o.order_number = :order_number AND o.user_id = :user_id
            """)
            result = conn.execute(query, {
                "order_number": order_number,
                "user_id": user_id
            }).fetchone()

            if not result:
                return JSONResponse(status_code=200, content={"data": None})

            return JSONResponse(status_code=200, content={
                "data": {
                    "number": str(order_number),
                    "price": result.price,
                    "trip": {
                        "attraction": {
                            "id": result.attraction_id,
                            "name": result.name,
                            "address": result.address,
                            "image": result.image
                        },
                        "date": result.date.strftime("%Y-%m-%d") if hasattr(result.date, "strftime") else result.date,
                        "time": result.time
                    },
                    "contact": {
                        "name": result.contact_name,
                        "email": result.contact_email,
                        "phone": result.contact_phone
                    },
                    "status": 1 if result.status == "PAID" else 0
                }
            })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": str(e)})
