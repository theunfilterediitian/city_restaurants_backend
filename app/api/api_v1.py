import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.core.deps import require_admin, require_restaurant, get_current_user
import shutil, os
from pydantic import EmailStr  # Add this\
from app.crud.crud import (
    create_restaurant,
    delete_category,
    delete_restaurant,
    get_restaurants,
    get_restaurant,
    get_restaurant_by_email,
    create_category,
    list_categories,
    create_product,
    get_products_by_restaurant,
    get_product,
    soft_delete_product,
    soft_delete_restaurant,
    update_product,
    update_product_availability,
    get_restaurant_by_id,
    update_restaurant
)

from app.schemas.schemas import (
    ProductUpdate,
    PublicRestaurantView,
    RestaurantCreate,
    RestaurantRead,
    CategoryBase,
    CategoryRead,
    ProductCreate,
    ProductRead,
    ProductImageRead,
    ProductAvailabilityUpdate,
    RestaurantUpdate,
    MediaAssetRead,
    MediaAssetCreate,
)
from app.models.models import Product, ProductImage

from typing import List
from app.core.s3 import delete_file_from_s3, upload_file_to_s3
from app.crud.crud import add_product_images
from app.models import models
from passlib.context import CryptContext
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


router = APIRouter()


# =========================================================
# RESTAURANTS
# =========================================================

# @router.post(
#     "/restaurants/",
#     response_model=RestaurantRead,
#     dependencies=[Depends(require_admin)],
#     tags=["Restaurant"]
# )
# def create_restaurant_api(
#     rest_in: RestaurantCreate,
#     db: Session = Depends(get_db),
# ):
#     if get_restaurant_by_email(db, rest_in.email):
#         raise HTTPException(status_code=400, detail="Email already registered")

#     return create_restaurant(db, rest_in)

@router.post(
    "/restaurants/",
    response_model=RestaurantRead,
    dependencies=[Depends(require_admin)],
    tags=["Restaurant"]
)
def create_restaurant_api(
    name: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),

    country_code: str | None = Form(None),
    state_code: str | None = Form(None),
    city_code: str | None = Form(None),

    location: str | None = Form(None),
    type: str | None = Form(None),
    pure_veg: bool = Form(False),
    landmark: str | None = Form(None),
    # ✅ OPTIONAL LOGO
    logo: UploadFile | None = File(None),

    db: Session = Depends(get_db),
):
    if get_restaurant_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")

    logo_url = None
    if logo:
        logo_url = upload_file_to_s3(logo, folder="restaurants/logos")

    restaurant = models.Restaurant(
        name=name,
        email=email,
        password_hash=pwd_ctx.hash(password),

        country_code=country_code,
        state_code=state_code,
        city_code=city_code,

        location=location,
        type=type,
        pure_veg=pure_veg,
        landmark=landmark,

        # ✅ SET LOGO URL
        logo_url=logo_url,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant






# @router.patch("/restaurants/{restaurant_id}", response_model=RestaurantRead, tags=["Restaurant"])
# def update_restaurant_api(
#     restaurant_id: int,
#     data: RestaurantUpdate,
#     db: Session = Depends(get_db),
# ):
#     restaurant = update_restaurant(db, restaurant_id, data)
#     if not restaurant:
#         raise HTTPException(status_code=404, detail="Restaurant not found")
#     return restaurant


@router.patch(
    "/restaurants/{restaurant_id}",
    response_model=RestaurantRead,
    tags=["Restaurant"],
)
def update_restaurant_api(
    restaurant_id: int,

    # ===== TEXT FIELDS =====
    name: str | None = Form(None),
    email: EmailStr | None = Form(None),
    password: str | None = Form(None),

    country_code: str | None = Form(None),
    state_code: str | None = Form(None),
    city_code: str | None = Form(None),

    location: str | None = Form(None),
    type: str | None = Form(None),
    pure_veg: bool | None = Form(None),
    landmark: str | None = Form(None),
    phone_number: str | None = Form(None),

    # ===== FILE =====
    logo: UploadFile | None = File(None),

    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # 🔐 Security Check: Admin or Self-Update only
    if user["role"] != "admin" and user.get("restaurant_id") != restaurant_id:
        raise HTTPException(status_code=403, detail="Not allowed to update this restaurant")

    restaurant = get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # ----- Update normal fields -----
    if name is not None:
        restaurant.name = name
    if email is not None:
        restaurant.email = email
    if password is not None:
        restaurant.password_hash = pwd_ctx.hash(password)

    restaurant.country_code = country_code or restaurant.country_code
    restaurant.state_code = state_code or restaurant.state_code
    restaurant.city_code = city_code or restaurant.city_code
    restaurant.location = location or restaurant.location
    restaurant.type = type or restaurant.type

    if pure_veg is not None:
        restaurant.pure_veg = pure_veg
    if landmark is not None:
        restaurant.landmark = landmark
    if phone_number is not None:
        restaurant.phone_number = phone_number

    # ----- Update logo -----
    if logo:
        logo_url = upload_file_to_s3(logo, folder="restaurants/logos")
        restaurant.logo_url = logo_url

    db.commit()
    db.refresh(restaurant)
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
# CATEGORIES (RESTAURANT SPECIFIC)
# =========================================================

@router.post(
    "/categories/",
    response_model=CategoryRead,
    tags=["Category"]
)
def create_category_api(
    name: str = Form(...),
    remark: str | None = Form(None),
    image: UploadFile | None = File(None),
    image_url: str | None = Form(None), # Added to support gallery images
    db: Session = Depends(get_db),
    user=Depends(require_restaurant) # Now restaurant can create its own
):
    final_image_url = image_url
    if image:
        final_image_url = upload_file_to_s3(image, folder="categories")
    
    category_in = CategoryBase(name=name, remark=remark, image_url=final_image_url, restaurant_id=user["restaurant_id"])
    return create_category(db, category_in)


@router.get("/categories/", response_model=list[CategoryRead], tags=["Category"])
def list_categories_api(
    rest_id: int | None = None,
    db: Session = Depends(get_db)
):
    if rest_id:
        return db.query(models.Category).filter(models.Category.restaurant_id == rest_id).all()
    return list_categories(db)



# =========================================================
# PRODUCTS
# =========================================================

# @router.post(
#     "/restaurants/{rest_id}/products/",
#     response_model=ProductRead,
#       tags=["Product"]
# )
# def create_product_api(
#     rest_id: int,
#     product_in: ProductCreate,
#     db: Session = Depends(get_db),
#     user=Depends(require_restaurant),
# ):
#     # 🔐 restaurant can only create for itself
#     if user["restaurant_id"] != rest_id:
#         raise HTTPException(status_code=403, detail="Not allowed")

#     if not get_restaurant(db, rest_id):
#         raise HTTPException(status_code=404, detail="Restaurant not found")

#     return create_product(db, rest_id, product_in)

@router.post(
    "/restaurants/{rest_id}/products/",
    response_model=ProductRead,
    tags=["Product"]
)
def create_product_api(
    rest_id: int,
    product: str = Form(...),                # JSON string
    db: Session = Depends(get_db),
    user=Depends(require_restaurant),
):
    # 🔐 Permission check
    if user["restaurant_id"] != rest_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if not get_restaurant(db, rest_id):
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # 🔹 Parse JSON
    product_in = ProductCreate(**json.loads(product))

    # 🔹 Create product
    product_obj = create_product(db, rest_id, product_in)

    return product_obj

    return product_obj



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


# @router.patch(
#     "/products/{product_id}",
#     response_model=ProductRead,
#       tags=["Product"]
# )
# def update_product_api(
#     product_id: int,
#     product_in: ProductUpdate,
#     db: Session = Depends(get_db),
#     user=Depends(require_restaurant),
# ):
#     product = get_product(db, product_id)
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")

#     # 🔐 restaurant can update only its own product
#     if product.restaurant_id != user["restaurant_id"]:
#         raise HTTPException(status_code=403, detail="Not allowed")

#     return update_product(db, product, product_in)


@router.patch(
    "/products/{product_id}",
    response_model=ProductRead,
    tags=["Product"]
)
def update_product_api(
    product_id: int,
    product: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_restaurant),
):
    product_obj = get_product(db, product_id)
    if not product_obj:
        raise HTTPException(status_code=404, detail="Product not found")

    if product_obj.restaurant_id != user["restaurant_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    # 🔹 Parse JSON
    product_in = ProductUpdate(**json.loads(product))

    # 🔹 Update product fields
    updated_product = update_product(db, product_obj, product_in)

    return updated_product

    return updated_product


@router.delete(
    "/products/images/{image_id}",
    status_code=204,
    tags=["Product"]
)
def delete_product_image_api(
    image_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_restaurant),
):
    image = db.query(ProductImage).filter(
        ProductImage.id == image_id
    ).first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # 🔐 ownership check
    product = db.query(Product).filter(
        Product.id == image.product_id
    ).first()

    if product.restaurant_id != user["restaurant_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    # 🔥 delete from DB (just disconnects the image from this product)
    db.delete(image)
    db.commit()

    return



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
    
    print("here")
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









# =========================================================
# PUBLIC ENDPOINTS (NO AUTH REQUIRED)
# =========================================================
@router.get(
    "/public/{country}/{state}/{city}/{identifier}",
    response_model=PublicRestaurantView,
    tags=["Public"]
)
def get_public_restaurant_view(
    country: str,
    state: str,
    city: str,
    identifier: str,
    db: Session = Depends(get_db)
):
    restaurant = db.query(models.Restaurant).filter(
        models.Restaurant.email.ilike(f"{identifier}@%.com")
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    from sqlalchemy.orm import selectinload
    products = db.query(models.Product).filter(
        models.Product.restaurant_id == restaurant.id,
        models.Product.available.is_(True),
        models.Product.is_deleted.is_(False)
    ).options(
        selectinload(models.Product.sizes),
        selectinload(models.Product.images),
        selectinload(models.Product.categories)
    ).all()

    return {
        "restaurant": restaurant,
        "products": products
    }
    
    
    # app/api/api_v1.py

@router.delete("/restaurants/{restaurant_id}", tags=["Restaurant"])
def delete_restaurant_api(restaurant_id: int, db: Session = Depends(get_db), user=Depends(require_admin)):
    # Calls the CRUD soft delete
    success = soft_delete_restaurant(db, restaurant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return {"detail": "Restaurant soft-deleted successfully"}

@router.delete("/products/{product_id}", tags=["Product"])
def delete_product_api(
    product_id: int, 
    db: Session = Depends(get_db),
    user=Depends(require_restaurant)
):
    product = get_product(db, product_id) # Ensure you filter by is_deleted inside get_product too
    if not product or product.restaurant_id != user["restaurant_id"]:
        raise HTTPException(status_code=403, detail="Not allowed or not found")
    
    soft_delete_product(db, product_id)
    return {"detail": "Product soft-deleted successfully"}



@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Category"])
def delete_category_api(
    category_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_restaurant) # Now restaurant can delete its own
):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    if category.restaurant_id != user["restaurant_id"]:
         raise HTTPException(status_code=403, detail="Not allowed")

    success = delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return


# =========================================================
# MEDIA GALLERY (ADMIN UPLOAD, REUSABLE BY ALL)
# =========================================================

@router.post(
    "/media/upload/",
    response_model=List[MediaAssetRead],
    dependencies=[Depends(require_admin)],
    tags=["Media"]
)
def upload_media_assets_api(
    labels: str = Form(...),            # JSON string: ["Label 1", "Label 2"]
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    try:
        labels_list = json.loads(labels)
    except Exception:
        raise HTTPException(status_code=400, detail="labels must be a JSON array of strings")

    if len(labels_list) != len(files):
        raise HTTPException(status_code=400, detail="Number of labels must match number of files")

    assets = []
    for label, file in zip(labels_list, files):
        url = upload_file_to_s3(file, folder="gallery")
        asset = models.MediaAsset(
            label=label,
            image_url=url
        )
        db.add(asset)
        assets.append(asset)

    db.commit()
    for asset in assets:
        db.refresh(asset)
    
    return assets

@router.get(
    "/media/",
    response_model=List[MediaAssetRead],
    tags=["Media"]
)
def list_media_assets_api(
    db: Session = Depends(get_db),
):
    return db.query(models.MediaAsset).all()

@router.delete(
    "/media/{asset_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
    tags=["Media"]
)
def delete_media_asset_api(
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = db.query(models.MediaAsset).filter(models.MediaAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found")
    
    # 🔥 delete from S3
    try:
        delete_file_from_s3(asset.image_url)
    except Exception as e:
        print(f"❌ S3 Deletion Failed: {e}")
        # If it's a permission error, we should probably stop and let the user know.
        # But to avoid "stuck" records, you might sometimes want to pass. 
        # For now, we raise a proper 500 so you see the message.
        raise HTTPException(status_code=500, detail=f"S3 Deletion Failed (Check IAM Permissions): {str(e)}")

    # 🔹 ALSO DELETE from product_images where image_url matches
    db.query(models.ProductImage).filter(models.ProductImage.image_url == asset.image_url).delete()

    db.delete(asset)
    db.commit()

    return
