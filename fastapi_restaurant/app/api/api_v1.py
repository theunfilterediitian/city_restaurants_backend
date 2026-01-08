from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.core.deps import require_admin, require_restaurant
import shutil, os

from app.crud.crud import (
    create_restaurant,
    delete_restaurant,
    get_restaurants,
    get_restaurant,
    get_restaurant_by_email,
    create_category,
    list_categories,
    create_product,
    get_products_by_restaurant,
    get_product,
    update_product,
    update_product_availability,
    get_restaurant_by_id,
    update_restaurant
)

from app.schemas.schemas import (
    ProductUpdate,
    RestaurantCreate,
    RestaurantRead,
    CategoryBase,
    CategoryRead,
    ProductCreate,
    ProductRead,
    ProductImageRead,
    ProductAvailabilityUpdate,
    RestaurantUpdate,
)
from app.models.models import ProductImage

from typing import List
from app.core.s3 import upload_file_to_s3
from app.crud.crud import add_product_images


router = APIRouter()

# =========================================================
# RESTAURANTS
# =========================================================

@router.post(
    "/restaurants/",
    response_model=RestaurantRead,
    dependencies=[Depends(require_admin)],
    tags=["Restaurant"]
)
def create_restaurant_api(
    rest_in: RestaurantCreate,
    db: Session = Depends(get_db),
):
    if get_restaurant_by_email(db, rest_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    return create_restaurant(db, rest_in)


@router.delete("/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)], tags=["Restaurant"]
)
def delete_restaurant_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    
):
    restaurant = delete_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return


@router.patch("/restaurants/{restaurant_id}", response_model=RestaurantRead, tags=["Restaurant"])
def update_restaurant_api(
    restaurant_id: int,
    data: RestaurantUpdate,
    db: Session = Depends(get_db),
):
    restaurant = update_restaurant(db, restaurant_id, data)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.get("/restaurants/", response_model=list[RestaurantRead],  tags=["Restaurant"])
def list_restaurants_api(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_restaurants(db, skip, limit)


@router.get("/restaurants/{restaurant_id}", response_model=RestaurantRead,  tags=["Category"])
def get_restaurant_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant_by_id(db, restaurant_id)
    
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return restaurant
# =========================================================
# CATEGORIES (ADMIN CREATE, PUBLIC READ)
# =========================================================

@router.post(
    "/categories/",
    response_model=CategoryRead,
    dependencies=[Depends(require_admin)],
     tags=["Category"]
)
def create_category_api(
    category: CategoryBase,
    db: Session = Depends(get_db),
):
    return create_category(db, category)


@router.get("/categories/", response_model=list[CategoryRead],   tags=["Category"])
def list_categories_api(db: Session = Depends(get_db)):
    return list_categories(db)


# =========================================================
# PRODUCTS
# =========================================================

@router.post(
    "/restaurants/{rest_id}/products/",
    response_model=ProductRead,
      tags=["Product"]
)
def create_product_api(
    rest_id: int,
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    user=Depends(require_restaurant),
):
    # 🔐 restaurant can only create for itself
    if user["restaurant_id"] != rest_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if not get_restaurant(db, rest_id):
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return create_product(db, rest_id, product_in)


@router.get(
    "/restaurants/{rest_id}/products/",
    response_model=list[ProductRead],
      tags=["Product"]
)
def list_products_api(
    rest_id: int,
    db: Session = Depends(get_db),
):
    return get_products_by_restaurant(db, rest_id)


@router.get(
    "/products/{product_id}",
    response_model=ProductRead,
      tags=["Product"]
)
def read_product_api(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch(
    "/products/{product_id}",
    response_model=ProductRead,
      tags=["Product"]
)
def update_product_api(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_restaurant),
):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 🔐 restaurant can update only its own product
    if product.restaurant_id != user["restaurant_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    return update_product(db, product, product_in)

# =========================================================
# PRODUCT AVAILABILITY (RESTAURANT ONLY)
# =========================================================

@router.patch(
    "/products/{product_id}/availability",
    response_model=ProductRead,
      tags=["Product"]
)
def update_availability_api(
    product_id: int,
    payload: ProductAvailabilityUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_restaurant),
):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.restaurant_id != user["restaurant_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    return update_product_availability(db, product_id, payload.available)


# =========================================================
# PRODUCT IMAGES (RESTAURANT ONLY)
# =========================================================

@router.post(
    "/products/{product_id}/images/",
    response_model=List[ProductImageRead]
  
)
def upload_product_images_api(
    product_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_restaurant),
    
):
    

    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.restaurant_id != user["restaurant_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    image_urls = []
    for file in files:
        url = upload_file_to_s3(file, f"products/{product_id}")
        image_urls.append(url)

    return add_product_images(db, product_id, image_urls)



@router.post(
    "/temp/products/{product_id}/images/",
    response_model=List[ProductImageRead],
    tags=["TEMP"]
)
def upload_product_images_temp(
    product_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):  
 
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    image_urls = []
    for file in files:
        url = upload_file_to_s3(file, f"products/{product_id}")
        image_urls.append(url)

    return add_product_images(db, product_id, image_urls)