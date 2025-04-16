from fastapi import APIRouter, Query, HTTPException,Request,Response
from fastapi.responses import JSONResponse
from database import get_db_connection
from datetime import datetime, timedelta
from config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_DAYS,PARTNER_KEY
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
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

@router.get("/api/booking")
def get_booking(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return JSONResponse(status_code=403, content={"error": True, "message": "為提供授權 token"})
    
    try:
        payload = jwt.decode(token.split("Bearer ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except (ExpiredSignatureError,InvalidTokenError):
        return JSONResponse(status_code=403, content={"error": True, "message": "無效或過期的 token"})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b .attraction_id, b.date, b.time, b.price, a.name, a.address, GROUP_CONCAT(ai.image_url) AS images
        FROM booking b
        JOIN attractions a ON b.attraction_id = a.id
        LEFT JOIN attraction_images ai ON a.id = ai.attraction_id
        WHERE b.user_id = %s
        GROUP BY b.attraction_id, b.date, b.time, b.price, a.name, a.address
    """, (user_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return JSONResponse(status_code=200, content={"data": None})
    
    image_url = result["images"].split(",")[0] if result["images"] else None
    
    return JSONResponse(status_code=200, content={
        "data":{
            "attraction":{
                "id": result["attraction_id"],
                "name": result["name"],
                "address": result["address"],
                "image": image_url
            },
            "date": result["date"].strftime("%Y-%m-%d") if hasattr(result["date"], "strftime") else result["date"],
            "time": result["time"],
            "price": result["price"]
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
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM attractions WHERE id = %s", (attraction_id,))
        if not cursor.fetchone():
            return JSONResponse(status_code=400, content={"error": True, "message": "無效的景點的 ID"})
        
        cursor.execute("""
            INSERT INTO booking (user_id, attraction_id, date, time, price)
            VALUES (%s, %s, %s, %s, %s)
            on DUPLICATE KEY UPDATE attraction_id = VALUES(attraction_id),
                                    date = VALUES(date),
                                    time = VALUES(time),
                                    price = VALUES(price)
        """, (user_id, attraction_id, date, time, price))

        conn.commit()
        cursor.close()
        conn.close()

        return JSONResponse(status_code=200, content={"ok": True})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message":  f"伺服器錯誤: {str(e)}"})
    
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM booking WHERE user_id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return JSONResponse(status_code=200, content={"ok": True})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message":f"伺服器錯誤: {str(e)}"})

# #建立訂單並付款的 API
# @router.post("/api/orders")
# async def create_order(request: Request):
#     try:
#         # 取得登入使用者資訊
#         token = request.headers.get("Authorization")
#         if not token or not token.startswith("Bearer "):
#             return JSONResponse(status_code=403, content={"error": True, "message": "未登入系統，拒絕存取"})

#         try:
#             payload = jwt.decode(token.split("Bearer ")[1], SECRET_KEY, algorithms=[ALGORITHM])
#             user_id = payload["user_id"]
#         except Exception:
#             return JSONResponse(status_code=403, content={"error": True, "message": "登入憑證錯誤"})

#         # 解析 request body
#         body = await request.json()
#         prime = body.get("prime")
#         order = body.get("order", {})
#         price = order.get("price")
#         trip = order.get("trip", {})
#         contact = order.get("contact", {})

#         attraction = trip.get("attraction", {})
#         attraction_id = attraction.get("id")
#         date = trip.get("date")
#         time = trip.get("time")
#         name = contact.get("name")
#         email = contact.get("email")
#         phone = contact.get("phone")

#         # 基本驗證
#         if not all([prime, price, attraction_id, date, time, name, email, phone]):
#             return JSONResponse(status_code=400, content={"error": True, "message": "訂單資料不完整"})

#         # 建立訂單編號（可改為 UUID 或 timestamp）
#         order_number = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

#         # 建立訂單記錄（初始狀態 UNPAID）
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             INSERT INTO orders (user_id, attraction_id, date, time, price, contact_name, contact_email, contact_phone, status,order_number)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """, (user_id, attraction_id, date, time, price, name, email, phone, "UNPAID",order_number))
#         conn.commit()
#         order_id = cursor.lastrowid

#         # 呼叫 TapPay API
#         tappay_payload = {
#             "prime": prime,
#             "partner_key": PARTNER_KEY,
#             "merchant_id": "tppt_Vadohyh_GP_POS_1",
#             "amount": price,
#             "details": "Taipei Trip",
#             "cardholder": {
#                 "phone_number": phone,
#                 "name": name,
#                 "email": email
#             }
#         }

#         tappay_response = requests.post(
#             "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime",
#             headers={"Content-Type": "application/json", "x-api-key": PARTNER_KEY},
#             json=tappay_payload
#         )
#         tappay_result = tappay_response.json()

#         # 根據付款結果更新訂單狀態
#         if tappay_result.get("status") == 0:
#             cursor.execute("UPDATE orders SET status='PAID' WHERE id=%s", (order_id,))
#             conn.commit()
#             payment_status = 0
#             message = "付款成功"
#         else:
#             payment_status = tappay_result.get("status")
#             message = "付款失敗"

#         cursor.close()
#         conn.close()

#         return JSONResponse(status_code=200, content={
#             "data": {
#                 "number": str(order_number),
#                 "payment": {
#                     "status": payment_status,
#                     "message": message
#                 }
#             }
#         })

#     except Exception as e:
#         return JSONResponse(status_code=500, content={"error": True, "message": str(e)})
    
# # 取得訂單資訊的 API
# @router.get("/api/order/{order_number}")
# def get_order(order_number: str, request: Request):
#     try:
#         token = request.headers.get("Authorization")
#         if not token or not token.startswith("Bearer "):
#             return JSONResponse(status_code=403, content={"error": True, "message": "未登入系統"})

#         try:
#             payload = jwt.decode(token.split("Bearer ")[1], SECRET_KEY, algorithms=[ALGORITHM])
#             user_id = payload["user_id"]
#         except Exception:
#             return JSONResponse(status_code=403, content={"error": True, "message": "登入憑證錯誤"})

#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT o.id, o.price, o.date, o.time, o.contact_name, o.contact_email, o.contact_phone, o.status,
#                    a.id AS attraction_id, a.name, a.address,
#                    (SELECT image_url FROM attraction_images WHERE attraction_id = a.id LIMIT 1) AS image
#             FROM orders o
#             JOIN attractions a ON o.attraction_id = a.id
#             WHERE o.order_number = %s AND o.user_id = %s
#         """, (order_number, user_id))

#         result = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         if not result:
#             return JSONResponse(status_code=200, content={"data": None})

#         return JSONResponse(status_code=200, content={
#             "data": {
#                 "number": str(order_number),
#                 "price": result["price"],
#                 "trip": {
#                     "attraction": {
#                         "id": result["attraction_id"],
#                         "name": result["name"],
#                         "address": result["address"],
#                         "image": result["image"]
#                     },
#                     "date": result["date"].strftime("%Y-%m-%d") if hasattr(result["date"], "strftime") else result["date"],
#                     "time": result["time"]
#                 },
#                 "contact": {
#                     "name": result["contact_name"],
#                     "email": result["contact_email"],
#                     "phone": result["contact_phone"]
#                 },
#                 "status": 1 if result["status"] == "PAID" else 0
#             }
#         })

#     except Exception as e:
#         return JSONResponse(status_code=500, content={"error": True, "message": str(e)})
#建立訂單並付款的 API
@router.post("/api/orders")
async def create_order(request: Request):
    try:
        # 取得登入使用者資訊
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return JSONResponse(status_code=403, content={"error": True, "message": "未登入系統，拒絕存取"})

        try:
            payload = jwt.decode(token.split("Bearer ")[1], SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload["user_id"]
        except Exception:
            return JSONResponse(status_code=403, content={"error": True, "message": "登入憑證錯誤"})

        # 解析 request body
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

        # 基本驗證
        if not all([prime, price, attraction_id, date, time, name, email, phone]):
            return JSONResponse(status_code=400, content={"error": True, "message": "訂單資料不完整"})

        # 建立訂單編號（使用 timestamp）
        order_number = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

        # 建立訂單記錄（初始狀態 UNPAID）
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (user_id, attraction_id, date, time, price, contact_name, contact_email, contact_phone, status, order_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, attraction_id, date, time, price, name, email, phone, "UNPAID", order_number))
        conn.commit()
        order_id = cursor.lastrowid

        # 呼叫 TapPay API
        tappay_payload = {
            "prime": prime,
            "partner_key": PARTNER_KEY,
            "merchant_id": "Vadohyh_CTBC",
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

        # 🔍 印出 TapPay 回傳內容（你要看的重點！）
        print("TapPay 回傳結果：", tappay_result)

        # 根據付款結果更新訂單狀態
        if tappay_result.get("status") == 0:
            cursor.execute("UPDATE orders SET status='PAID' WHERE id=%s", (order_id,))
            conn.commit()
            payment_status = 0
            message = "付款成功"
        else:
            payment_status = tappay_result.get("status")
            message = "付款失敗"

        cursor.close()
        conn.close()

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

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.id, o.price, o.date, o.time, o.contact_name, o.contact_email, o.contact_phone, o.status,
                   a.id AS attraction_id, a.name, a.address,
                   (SELECT image_url FROM attraction_images WHERE attraction_id = a.id LIMIT 1) AS image
            FROM orders o
            JOIN attractions a ON o.attraction_id = a.id
            WHERE o.order_number = %s AND o.user_id = %s
        """, (order_number, user_id))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return JSONResponse(status_code=200, content={"data": None})

        return JSONResponse(status_code=200, content={
            "data": {
                "number": str(order_number),
                "price": result["price"],
                "trip": {
                    "attraction": {
                        "id": result["attraction_id"],
                        "name": result["name"],
                        "address": result["address"],
                        "image": result["image"]
                    },
                    "date": result["date"].strftime("%Y-%m-%d") if hasattr(result["date"], "strftime") else result["date"],
                    "time": result["time"]
                },
                "contact": {
                    "name": result["contact_name"],
                    "email": result["contact_email"],
                    "phone": result["contact_phone"]
                },
                "status": 1 if result["status"] == "PAID" else 0
            }
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": str(e)})
