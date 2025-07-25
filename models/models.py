# models/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

from database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False) # Nouveau champ pour le rôle admin

    # Relations
    cart_items = relationship("CartItem", back_populates="owner")
    orders = relationship("Order", back_populates="customer")
    favorite_books = relationship("Favorite", back_populates="user")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    # Pour l'instant, stockons juste le chemin du fichier ou une URL simulée
    pdf_url = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)
    category = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    cart_items = relationship("CartItem", back_populates="book")
    order_items = relationship("OrderItem", back_populates="book")
    favorites = relationship("Favorite", back_populates="book")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    owner = relationship("User", back_populates="cart_items")
    book = relationship("Book", back_populates="cart_items")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending") # e.g., "pending", "completed", "cancelled"
    order_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    customer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False) # Prix du livre au moment de l'achat

    # Relations
    order = relationship("Order", back_populates="items")
    book = relationship("Book", back_populates="order_items")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    user = relationship("User", back_populates="favorite_books")
    book = relationship("Book", back_populates="favorites")