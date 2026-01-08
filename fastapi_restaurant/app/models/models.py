from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Float, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
from sqlalchemy import UniqueConstraint

# Many-to-many if required between product and categories (optional)
product_category = Table(
    "product_category",
    Base.metadata,
    Column("product_id", ForeignKey("products.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)
class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # 👇 NEW LOCATION FIELDS
    country_code = Column(String(5), nullable=True)   # e.g. IN
    state_code = Column(String(10), nullable=True)    # e.g. BR, KA
    city_code = Column(String(50), nullable=True)     # e.g. PATNA

    location = Column(String(500))
    date_created = Column(DateTime, default=datetime.utcnow)
    type = Column(String(100))
    staff_rating = Column(Float, default=0.0)
    pure_veg = Column(Boolean, default=False)

    products = relationship("Product", back_populates="restaurant")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g. Starter, Drinks, Snacks, Dessert
    remark = Column(String(500), nullable=True)

    products = relationship("Product", secondary=product_category, back_populates="categories")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)

    veg = Column(Boolean, default=None)
    remark = Column(String(500))
    available = Column(Boolean, default=True)
    iced = Column(Boolean, default=False)
    description = Column(Text)

    restaurant = relationship("Restaurant", back_populates="products")
    categories = relationship("Category", secondary=product_category, back_populates="products")

    sizes = relationship(
        "ProductSize",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan"
    )

class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    image_url = Column(String(1024), nullable=False)

    product = relationship("Product", back_populates="images")


class ProductSize(Base):
    __tablename__ = "product_sizes"

    id = Column(Integer, primary_key=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    size_label = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)

    product = relationship("Product", back_populates="sizes")

    __table_args__ = (
     
        UniqueConstraint("product_id", "size_label", name="uq_product_size"),
    )


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)

    restaurant = relationship("Restaurant", backref="users")
