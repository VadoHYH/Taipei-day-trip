# models/order.py

from pydantic import BaseModel
from typing import Literal

class AttractionInfo(BaseModel):
    id: int
    name: str
    address: str
    image: str

class TripInfo(BaseModel):
    attraction: AttractionInfo
    date: str           # 可進一步轉換為 datetime 但這裡保持字串（YYYY-MM-DD）
    time: Literal["morning", "afternoon"]

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: str

class OrderDetail(BaseModel):
    price: int
    trip: TripInfo
    contact: ContactInfo

class OrderRequest(BaseModel):
    prime: str
    order: OrderDetail
