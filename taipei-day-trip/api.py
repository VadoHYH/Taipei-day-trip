from fastapi import APIRouter, Query, HTTPException
from database import get_db_connection

router = APIRouter()

@router.get("/api/attractions")
def get_attraction(
    page: int = Query(0, alias="page", ge=0),
    keyword: str = Query(None, alias="keyword")
):
    try:
        per_page = 12  # 每頁 12 筆
        offset = page * per_page

        conn = get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="無法連接到資料庫")

        cursor = conn.cursor(dictionary=True)  # 使用 dictionary 方式返回結果

        # **修正 SQL 查詢**
        sql = """
            SELECT a.id, a.name, a.category, a.description, a.address, a.transport, 
                   a.mrt, a.lat, a.lng, GROUP_CONCAT(ai.image_url) AS images
            FROM attractions a
            LEFT JOIN attraction_images ai ON a.id = ai.attraction_id
        """
        count_sql = "SELECT COUNT(DISTINCT a.id) AS total FROM attractions a"
        params = []

        # **如果有關鍵字，加入搜尋條件**
        if keyword:
            sql += " WHERE a.name LIKE %s OR a.mrt = %s"
            count_sql += " WHERE a.name LIKE %s OR a.mrt = %s"
            params.extend([f"%{keyword}%", keyword])

        # **修正 ORDER BY，確保翻頁時資料順序正確**
        sql += " GROUP BY a.id ORDER BY a.id LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(sql, tuple(params))
        attractions = cursor.fetchall()

        # **轉換圖片格式**
        for attraction in attractions:
            attraction["images"] = attraction["images"].split(",") if attraction["images"] else []

        # **計算總數**
        cursor.execute(count_sql, tuple(params[:2]))  # count_sql 只用 `keyword` 的參數
        total_count = cursor.fetchone()["total"]

        # **計算 nextPage**
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
