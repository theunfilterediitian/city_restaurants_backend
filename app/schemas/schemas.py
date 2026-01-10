from pydantic import BaseModel, EmailStr
from typing import List, Optional


# ============================
# Product Size (Pricing)
# ============================

class ProductSizeCreate(BaseModel):
    size_label: str
    price: float


class ProductSizeRead(ProductSizeCreate):
    id: int

    class Config:
        orm_mode = True


# ============================
# Categories
# ============================

class CategoryBase(BaseModel):
    name: str
    remark: Optional[str] = None


class CategoryRead(CategoryBase):
    id: int

    class Config:
        orm_mode = True


# ============================
# Product Images  ✅ MUST COME BEFORE ProductRead
# ============================

class ProductImageRead(BaseModel):
    id: int
    image_url: str

    class Config:
        orm_mode = True



# ============================
# Products
# ============================

class ProductCreate(BaseModel):
    name: str
    veg: Optional[bool] = None
    remark: Optional[str] = None
    available: bool = True
    iced: bool = False
    description: Optional[str] = None
    category_ids: List[int] = []
    sizes: List[ProductSizeCreate] = []


class ProductRead(BaseModel):
    id: int
    restaurant_id: int
    name: str
    veg: Optional[bool]
    remark: Optional[str]
    available: bool
    iced: bool
    description: Optional[str]

    sizes: List[ProductSizeRead] = []
    images: List[ProductImageRead] = []
    categories: List[CategoryRead] = []

    class Config:
        orm_mode = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    veg: Optional[bool] = None
    remark: Optional[str] = None
    available: Optional[bool] = None
    iced: Optional[bool] = None
    description: Optional[str] = None
    category_ids: Optional[List[int]] = None
    sizes: Optional[List[ProductSizeCreate]] = None
        
    


# ============================
# Product Availability
# ============================

class ProductAvailabilityUpdate(BaseModel):
    available: bool


# ============================
# Restaurants
# ============================

class RestaurantCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

    country_code: Optional[str] = None
    state_code: Optional[str] = None
    city_code: Optional[str] = None

    location: Optional[str] = None
    type: Optional[str] = None
    pure_veg: Optional[bool] = False
    logo_url: Optional[str] = None



class RestaurantRead(BaseModel):
    id: int
    name: str
    email: EmailStr

    country_code: Optional[str]
    state_code: Optional[str]
    city_code: Optional[str]

    location: Optional[str]
    type: Optional[str]
    pure_veg: bool
    logo_url: Optional[str]

    class Config:
        orm_mode = True


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    country_code: Optional[str] = None
    state_code: Optional[str] = None
    city_code: Optional[str] = None

    location: Optional[str] = None
    type: Optional[str] = None
    pure_veg: Optional[bool] = None
    logo_url: Optional[str] = None
    
    
class PublicRestaurantRead(BaseModel):
    id: int
    name: str
    email: str
    country_code: str
    state_code: str
    city_code: str
    location: Optional[str]
    logo_url: Optional[str]
    pure_veg: bool
    staff_rating: int
    type: str

    class Config:
        orm_mode = True
        

class PublicProductRead(BaseModel):
    id: int
    restaurant_id: int

    name: str
    description: Optional[str]
    remark: Optional[str]

    veg: Optional[bool]
    iced: bool
    available: bool

    sizes: List[ProductSizeRead] = []
    images: List[ProductImageRead] = []
    categories: List[CategoryRead] = []

    class Config:
        orm_mode = True
        
from typing import List

class PublicRestaurantView(BaseModel):
    restaurant: PublicRestaurantRead
    products: List[PublicProductRead]

    class Config:
        orm_mode = True