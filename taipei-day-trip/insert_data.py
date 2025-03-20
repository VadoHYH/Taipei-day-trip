import json
import pymysql
import re
from database import get_db_connection

# 讀取 JSON
with open("data/taipei-attractions.json", encoding="utf-8") as f:
    raw_data = json.load(f)  # 讀取 JSON 內容

# 確保正確讀取景點資料陣列
data = raw_data["result"]["results"]  # 取出 `results` 陣列

# 連接 MySQL
conn = get_db_connection()
cursor = conn.cursor()

# **確保 `attractions` 表存在**
cursor.execute("""
    CREATE TABLE IF NOT EXISTS attractions(
        id          INT PRIMARY KEY AUTO_INCREMENT,
        name        VARCHAR(255) NOT NULL,
        category    VARCHAR(50) NOT NULL,
        description TEXT NOT NULL,
        address     VARCHAR(255) NOT NULL,
        transport   TEXT NOT NULL,
        mrt         VARCHAR(50),
        lat         DECIMAL(10, 6) NOT NULL,
        lng         DECIMAL(10, 6) NOT NULL
    )
""")

# **確保 `attraction_images` 表存在**
cursor.execute("""
    CREATE TABLE IF NOT EXISTS attraction_images(
        id             INT PRIMARY KEY AUTO_INCREMENT,
        attraction_id  INT NOT NULL,
        image_url      VARCHAR(500) NOT NULL,
        FOREIGN KEY (attraction_id) REFERENCES attractions(id) ON DELETE CASCADE
    )
""")

# **清除舊資料，確保重新插入**
cursor.execute("DELETE FROM attraction_images")
cursor.execute("DELETE FROM attractions")
conn.commit()

# **插入資料**
for index, item in enumerate(data):
    name = item["name"]
    category = item["CAT"]  # 使用 `CAT` 作為景點類別
    description = item["description"]
    address = item["address"]
    mrt = item.get("MRT", None)  # 使用 `.get()` 避免 KeyError
    lat = float(item["latitude"])  # 轉換為 float
    lng = float(item["longitude"])  # 轉換為 float
    transport = item.get("direction", "無資料")  # 使用 `.get()`，避免 KeyError

    # **插入 `attractions` 表**
    cursor.execute("""
        INSERT INTO attractions (name, category, description, address, transport, mrt, lat, lng)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (name, category, description, address, transport, mrt, lat, lng))

    # **獲取剛插入的景點 ID**
    attraction_id = cursor.lastrowid
    print(f" 已插入景點 {index + 1}: {name} (ID: {attraction_id})")

    # **解析 `file` 欄位並存入 `attraction_images` 表**
    if "file" in item and item["file"]:
        # **使用正則表達式抓取所有圖片網址**
        image_urls = re.findall(r"https?://.*?\.(?:jpg|png|jpeg|JPG|PNG|JPEG)", item["file"])
        
        # **確保 URLs 非空**
        if image_urls:
            for url in image_urls:
                cursor.execute("""
                    INSERT INTO attraction_images (attraction_id, image_url)
                    VALUES (%s, %s)
                """, (attraction_id, url))
                print(f"    插入圖片: {url}")
        else:
            print(f" {name} 沒有符合條件的圖片，跳過圖片插入")
    else:
        print(f" {name} 沒有 `file` 欄位，跳過圖片插入")

# **提交變更並關閉連線**
conn.commit()
conn.close()
print("資料存入成功！")
