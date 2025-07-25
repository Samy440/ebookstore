# schemas/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import datetime

# --- Schémas pour l'Authentification et l'Utilisateur ---

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDB(UserBase):
    id: int
    hashed_password: str

    class Config:
        orm_mode = True # Permet à Pydantic de lire les données d'un ORM (comme SQLAlchemy)

class UserResponse(UserBase):
    id: int
    # Pas de hashed_password ici pour la réponse API
    class Config:
        orm_mode = True

# --- Schémas pour les Livres ---

class BookBase(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., gt=0) # gt = greater than (strictement supérieur à 0)
    pdf_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    category: Optional[str] = None

class BookCreate(BookBase):
    pass # Pour l'instant, pas de champs supplémentaires lors de la création

class BookUpdate(BookBase):
    title: Optional[str] = None
    author: Optional[str] = None
    price: Optional[float] = None
    # Tous les champs sont optionnels pour une mise à jour partielle

class BookResponse(BookBase):
    id: int
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True

# --- Schémas pour le Panier ---

class CartItemBase(BaseModel):
    book_id: int
    quantity: int = Field(..., gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(CartItemBase):
    quantity: int = Field(..., gt=0) # La quantité est le seul champ à mettre à jour

class CartItemResponse(CartItemBase):
    id: int
    user_id: int
    added_at: datetime.datetime
    book: BookResponse # Inclut les détails du livre

    class Config:
        orm_mode = True

# --- Schémas pour les Commandes ---

class OrderItemBase(BaseModel):
    book_id: int
    quantity: int = Field(..., gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    price_at_purchase: float
    book: BookResponse # Inclut les détails du livre

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    # Pas de champs ici, car la commande est créée à partir du panier
    pass

class OrderCreate(OrderBase):
    # Peut inclure des informations de livraison si nécessaire
    pass

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    order_date: datetime.datetime
    items: List[OrderItemResponse] = [] # Liste des articles de la commande

    class Config:
        orm_mode = True

# --- Schémas pour les Favoris ---

class FavoriteBase(BaseModel):
    book_id: int

class FavoriteCreate(FavoriteBase):
    pass

class FavoriteResponse(FavoriteBase):
    id: int
    user_id: int
    added_at: datetime.datetime
    book: BookResponse # Inclut les détails du livre

    class Config:
        orm_mode = True