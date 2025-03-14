from fastapi import APIRouter, Query, HTTPException
from database import get_db_connection

router = APIRouter()

@router.get("/api/attractions")
def get_attraction(
    page: int = Query(0, alias="page", ge=0),
    keyword: str = Query(None, alias="keyword")
):
    try:
        per_page = 12
        offset = page * per_page

        conn = get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="無法連接到資料庫")

        cursor = conn.cursor()

        # SQL 條件
        sql = """
            SELECT a.id, a.name, a.category, a.description, a.address, a.transport, 
                   a.mrt, a.lat, a.lng
            FROM attractions a
        """
        params = []

        if keyword:
            sql += " WHERE a.name LIKE %s OR a.mrt = %s"
            params.extend([f"%{keyword}%", keyword])

        sql += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(sql, tuple(params))
        attractions = cursor.fetchall()

        # 取得每個景點的圖片
        for attraction in attractions:
            cursor.execute("""
                SELECT image_url FROM attraction_images WHERE attraction_id = %s
            """, (attraction["id"],))
            images = [row["image_url"] for row in cursor.fetchall()]
            attraction["images"] = images

        # 查詢總數
        count_sql = "SELECT COUNT(*) AS total FROM attractions"
        if keyword:
            count_sql += " WHERE name LIKE %s OR mrt = %s"
            cursor.execute(count_sql, (f"%{keyword}%", keyword))
        else:
            cursor.execute(count_sql)

        total_count = cursor.fetchone()["total"]
        next_page = page + 1 if page * per_page < total_count else None

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

        #查詢指定 ID的景點
        sql = """
            SELECT id, name, category, description, address, transport, mrt, lat, lng
            FROM attractions
            WHERE id = %s
        """
        cursor.execute(sql, (id,))
        attraction = cursor.fetchone()

        #如果景點不在回傳400
        if not attraction:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="景點編號不正確")
        
        #查詢該景點圖片
        cursor.execute("""
            SELECT image_url FROM attraction_images WHERE attraction_id = %s
        """, (id,))
        images = [row["image_url"] for row in cursor.fetchall()]

        #將圖片加進結果
        attraction["images"] = images

        cursor.close()
        conn.close()

        return{"data": attraction}
    
    except Exception as e:
        return {"error": True, "message": f"伺服器錯誤: {str(e)}"}

@router.get("/api/mrts")
def get_mrts():
    try:
        conn = get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="無法連接到資料庫")
        
        cursor = conn.cursor()

        # 查詢 MRT站點其對應景點數
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