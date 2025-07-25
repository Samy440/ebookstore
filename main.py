# main.py
from datetime import timedelta

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

# Importe nos configurations de base de données et nos modèles SQLAlchemy
from database.database import engine, get_db
from models import models
from schemas import schemas # Importe tous les schémas Pydantic

# Importe nos utilitaires de sécurité
from auth import security

# Crée toutes les tables dans la base de données.
# Ceci est exécuté au démarrage de l'application.
models.Base.metadata.create_all(bind=engine)
from starlette.middleware.cors import CORSMiddleware # <-- Importe le middleware CORS


app = FastAPI(
    title="API E-commerce de Livres",
    description="Une API complète pour gérer une boutique de livres PDF/e-books.",
    version="1.0.0",
)

# --- Configuration CORS ---
# Liste des origines (domaines) autorisées à faire des requêtes à ton API
# Remplace "http://localhost:3000" par l'URL de ton application front-end React/Angular/Vue.js
# Si tu as plusieurs origines, tu peux les lister : ["http://localhost:3000", "https://ton-site-front.com"]
# Pour autoriser toutes les origines (attention: à n'utiliser qu'en développement ou pour les APIs publiques sans données sensibles), utilise ["*"]
origins = [
    "http://localhost",
    "http://localhost:8080", # Exemple si ton front-end tourne sur ce port
    "http://localhost:3000", # Exemple pour React
    "http://localhost:4200"  # Exemple pour Angular
    # Ajoute ici les URLs de production de ton front-end quand tu déploieras
    # "https://ton-app-frontend.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Liste des origines autorisées
    allow_credentials=True, # Autorise les cookies et les en-têtes d'autorisation (comme notre JWT)
    allow_methods=["*"], # Autorise toutes les méthodes HTTP (GET, POST, PUT, DELETE, PATCH, OPTIONS)
    allow_headers=["*"], # Autorise tous les en-têtes HTTP de la requête (y compris l'Authorization pour le JWT)
)


# Configuration pour OAuth2 avec JWT (pour la documentation Swagger/Redoc)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # "login" est l'URL où on peut obtenir un token

# --- Dépendances Communes ---
# Cette dépendance sera utilisée par toutes les routes sécurisées pour obtenir l'utilisateur courant.
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # Récupérer l'utilisateur depuis la base de données
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Dépendance pour vérifier si l'utilisateur est un administrateur
async def get_current_admin_user(current_user: schemas.UserResponse = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs sont autorisés à accéder à cette ressource."
        )
    return current_user


# --- Routes Générales ---
@app.get("/")
async def read_root():
    return {"message": "Bienvenue dans votre librairie e-commerce FastAPI !"}

# --- Routes d'Authentification ---

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le nom d'utilisateur ou l'e-mail existe déjà.")

    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active,
        is_admin=user.is_admin # Permet de définir un admin à la création si nécessaire (à protéger plus tard)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Rafraîchit l'instance avec les données de la DB (ex: ID)
    return db_user

@app.post("/login", response_model=dict) # schemas.Token si on veut un schéma dédié pour le token
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte utilisateur inactif",
        )

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Routes Utilisateur Protégées ---

@app.get("/users/me/", response_model=schemas.UserResponse)
async def read_users_me(current_user: schemas.UserResponse = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur connecté."""
    return current_user

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
async def read_user(user_id: int, db: Session = Depends(get_db),
                    current_admin: schemas.UserResponse = Depends(get_current_admin_user)):
    """Récupère un utilisateur par ID (nécessite les droits admin)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

@app.put("/users/{user_id}", response_model=schemas.UserResponse)
async def update_user(user_id: int, user_update: schemas.UserBase, db: Session = Depends(get_db),
                      current_admin: schemas.UserResponse = Depends(get_current_admin_user)):
    """Met à jour un utilisateur (nécessite les droits admin)."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Mettre à jour les champs
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db),
                      current_admin: schemas.UserResponse = Depends(get_current_admin_user)):
    """Supprime un utilisateur (nécessite les droits admin)."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    db.delete(db_user)
    db.commit()
    return {"message": "Utilisateur supprimé avec succès."} # Bien que 204 NO_CONTENT ne retourne pas de corps.

@app.get("/users/", response_model=List[schemas.UserResponse])
async def read_users(
    skip: int = 0, # Paramètre de requête pour l'offset (début de la liste)
    limit: int = 100, # Paramètre de requête pour le nombre maximum d'éléments
    db: Session = Depends(get_db),
    current_admin: schemas.UserResponse = Depends(get_current_admin_user)
):
    """
    Récupère la liste de tous les utilisateurs (nécessite les droits admin).
    Supporte la pagination via 'skip' et 'limit'.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# --- Routes Livres ---

@app.post("/books/", response_model=schemas.BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_admin: schemas.UserResponse = Depends(get_current_admin_user)
):
    """
    Ajoute un nouveau livre à la boutique (nécessite les droits admin).
    """
    db_book = models.Book(**book.model_dump()) # Crée une instance de Book à partir du schéma
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/books/", response_model=List[schemas.BookResponse])
async def read_books(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None, # Nouveau paramètre de requête pour le filtrage
    db: Session = Depends(get_db)
):
    """
    Récupère la liste de tous les livres, avec pagination et filtrage par catégorie (accessible à tous).
    """
    query = db.query(models.Book)
    if category:
        query = query.filter(models.Book.category == category) # Applique le filtre de catégorie
    books = query.offset(skip).limit(limit).all()
    return books

@app.get("/books/{book_id}", response_model=schemas.BookResponse)
async def read_book(book_id: int, db: Session = Depends(get_db)):
    """
    Récupère les détails d'un livre spécifique par son ID (accessible à tous).
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    return book

@app.put("/books/{book_id}", response_model=schemas.BookResponse)
async def update_book_full(
    book_id: int,
    book_update: schemas.BookCreate, # Utilise BookCreate car PUT est une mise à jour complète
    db: Session = Depends(get_db),
    current_admin: schemas.UserResponse = Depends(get_current_admin_user)
):
    """
    Met à jour complètement un livre existant (nécessite les droits admin).
    Remplace toutes les informations du livre.
    """
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    # Mettre à jour tous les champs avec les données du schéma BookCreate
    for key, value in book_update.model_dump().items(): # Pas de exclude_unset car PUT est complet
        setattr(db_book, key, value)

    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.patch("/books/{book_id}", response_model=schemas.BookResponse)
async def update_book_partial(
    book_id: int,
    book_update: schemas.BookUpdate, # Utilise BookUpdate pour une mise à jour partielle
    db: Session = Depends(get_db),
    current_admin: schemas.UserResponse = Depends(get_current_admin_user)
):
    """
    Met à jour partiellement un livre existant (nécessite les droits admin).
    Modifie seulement les champs fournis dans la requête.
    """
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    # Mettre à jour seulement les champs qui sont fournis dans la requête
    # model_dump(exclude_unset=True) est crucial ici pour PATCH
    for key, value in book_update.model_dump(exclude_unset=True).items():
        setattr(db_book, key, value)

    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: schemas.UserResponse = Depends(get_current_admin_user)
):
    """
    Supprime un livre de la boutique (nécessite les droits admin).
    """
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    db.delete(db_book)
    db.commit()
    # Pour un statut 204 No Content, il ne faut pas retourner de corps.
    # FastAPI gérera cela automatiquement si tu ne retournes rien.
    # return {"message": "Livre supprimé avec succès."} # Ceci ne sera pas visible avec 204

#panier
@app.post("/cart/items", response_model=schemas.CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    cart_item_data: schemas.CartItemCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Ajoute un livre au panier de l'utilisateur ou met à jour sa quantité s'il existe déjà.
    """
    book = db.query(models.Book).filter(models.Book.id == cart_item_data.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé.")

    # Vérifier si l'article existe déjà dans le panier de l'utilisateur
    db_cart_item = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id,
        models.CartItem.book_id == cart_item_data.book_id
    ).first()

    if db_cart_item:
        # Si l'article existe, met à jour la quantité
        db_cart_item.quantity += cart_item_data.quantity
    else:
        # Sinon, crée un nouvel article dans le panier
        db_cart_item = models.CartItem(
            user_id=current_user.id,
            book_id=cart_item_data.book_id,
            quantity=cart_item_data.quantity
        )
        db.add(db_cart_item)

    db.commit()
    db.refresh(db_cart_item)
    # Pour inclure les détails du livre dans la réponse, nous devons le charger
    db_cart_item.book = book # Attache le livre pour la sérialisation Pydantic
    return db_cart_item

@app.get("/cart/", response_model=dict) # Nous allons retourner un dictionnaire personnalisé
async def get_cart_content(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Récupère le contenu du panier de l'utilisateur connecté, y compris le total des prix et la quantité totale d'articles.
    """
    cart_items = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).options(
        joinedload(models.CartItem.book) # Charge les détails du livre en une seule requête
    ).all()

    total_amount = 0.0
    total_quantity = 0 # <-- Nouvelle variable pour la quantité totale
    response_items = []
    for item in cart_items:
        if item.book:
            total_amount += item.quantity * item.book.price
            total_quantity += item.quantity # <-- Ajout à la quantité totale

            # Construire manuellement le dictionnaire qui correspond à CartItemResponse
            cart_item_dict = {
                "id": item.id,
                "user_id": item.user_id,
                "book_id": item.book_id,
                "quantity": item.quantity,
                "added_at": item.added_at.isoformat(), # Convertir datetime en string ISO
                "book": { # Construire manuellement le dictionnaire pour le livre imbriqué
                    "id": item.book.id,
                    "title": item.book.title,
                    "author": item.book.author,
                    "description": item.book.description,
                    "price": item.book.price,
                    "pdf_url": item.book.pdf_url,
                    "cover_image_url": item.book.cover_image_url,
                    "category": item.book.category,
                    "created_at": item.book.created_at.isoformat(),
                    "updated_at": item.book.updated_at.isoformat() if item.book.updated_at else None
                }
            }
            response_items.append(cart_item_dict)

    return {
        "user_id": current_user.id,
        "items": response_items,
        "total_amount_fcfa": round(total_amount, 2), # Arrondir à 2 décimales
        "total_items_in_cart": total_quantity # <-- Nouvelle clé dans la réponse
    }

@app.patch("/cart/items/{book_id}", response_model=schemas.CartItemResponse)
async def update_cart_item_quantity(
    book_id: int,
    cart_item_update: schemas.CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Met à jour la quantité d'un livre spécifique dans le panier de l'utilisateur.
    Si la quantité devient 0, l'article est supprimé du panier.
    """
    db_cart_item = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id,
        models.CartItem.book_id == book_id
    ).first()

    if not db_cart_item:
        raise HTTPException(status_code=404, detail="Livre non trouvé dans le panier.")

    if cart_item_update.quantity <= 0:
        # Si la quantité est 0 ou moins, supprimer l'article du panier
        db.delete(db_cart_item)
        db.commit()
        raise HTTPException(status_code=200, detail="Livre supprimé du panier car quantité nulle ou négative.")
        # Note: Un 204 No Content serait plus approprié si on ne voulait pas de message,
        # mais 200 avec un message est plus informatif ici.

    db_cart_item.quantity = cart_item_update.quantity
    db.commit()
    db.refresh(db_cart_item)
    db_cart_item.book = db.query(models.Book).filter(models.Book.id == book_id).first() # Recharge le livre
    return db_cart_item

@app.delete("/cart/items/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Supprime un livre spécifique du panier de l'utilisateur.
    """
    db_cart_item = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id,
        models.CartItem.book_id == book_id
    ).first()

    if not db_cart_item:
        raise HTTPException(status_code=404, detail="Livre non trouvé dans le panier.")

    db.delete(db_cart_item)
    db.commit()
    # Le statut 204 No Content signifie pas de corps de réponse.

@app.delete("/cart/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Vide entièrement le panier de l'utilisateur connecté.
    """
    # Supprime tous les articles du panier pour l'utilisateur courant
    db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).delete()
    db.commit()
    # Le statut 204 No Content signifie pas de corps de réponse.


# --- Routes Commandes ---

@app.post("/orders", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Crée une nouvelle commande à partir du contenu actuel du panier de l'utilisateur.
    Le panier est vidé après la création de la commande.
    """
    cart_items = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).options(
        joinedload(models.CartItem.book)
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le panier est vide. Impossible de créer une commande."
        )

    total_amount = 0.0
    order_items_to_create = []

    for item in cart_items:
        if not item.book:
            # Ceci ne devrait pas arriver si les relations sont bien gérées, mais c'est une sécurité
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Livre avec ID {item.book_id} non trouvé pour un article du panier.")

        # Calcul du total et préparation des articles de la commande
        item_price = item.book.price # Prix du livre au moment de l'achat
        total_amount += item.quantity * item_price

        order_item = models.OrderItem(
            book_id=item.book_id,
            quantity=item.quantity,
            price_at_purchase=item_price # Enregistre le prix au moment de l'achat
        )
        order_items_to_create.append(order_item)

    # Création de la commande principale
    new_order = models.Order(
        user_id=current_user.id,
        total_amount=round(total_amount, 2),
        status="pending", # Ou "completed", "shipped", etc. selon ton workflow
        items=order_items_to_create # Associe les OrderItems à la Order
    )
    db.add(new_order)
    db.commit()

    # Vider le panier après la création de la commande
    db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).delete()
    db.commit() # Commit pour la suppression du panier

    db.refresh(new_order) # Rafraîchir pour obtenir l'ID de la commande et les OrderItems associés
    # Charger les détails des livres pour les OrderItems si nécessaire pour la réponse
    db.refresh(new_order) # Un second refresh peut être nécessaire pour les relations après commit du panier vide

    # Construire la réponse OrderResponse manuellement pour gérer les objets imbriqués
    response_order_items = []
    for order_item in new_order.items:
        # Charger le livre associé à l'OrderItem pour la sérialisation
        book_details = db.query(models.Book).filter(models.Book.id == order_item.book_id).first()
        if book_details:
            order_item_dict = {
                "id": order_item.id,
                "order_id": order_item.order_id,
                "book_id": order_item.book_id,
                "quantity": order_item.quantity,
                "price_at_purchase": order_item.price_at_purchase,
                "book": {
                    "id": book_details.id,
                    "title": book_details.title,
                    "author": book_details.author,
                    "description": book_details.description,
                    "price": book_details.price,
                    "pdf_url": book_details.pdf_url,
                    "cover_image_url": book_details.cover_image_url,
                    "category": book_details.category,
                    "created_at": book_details.created_at.isoformat(),
                    "updated_at": book_details.updated_at.isoformat() if book_details.updated_at else None
                }
            }
            response_order_items.append(order_item_dict)

    return {
        "id": new_order.id,
        "user_id": new_order.user_id,
        "total_amount": new_order.total_amount,
        "status": new_order.status,
        "order_date": new_order.order_date.isoformat(),
        "items": response_order_items
    }

@app.get("/orders", response_model=List[schemas.OrderResponse])
async def get_user_orders(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Récupère toutes les commandes passées par l'utilisateur connecté.
    """
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.book) # Charge les articles de commande et leurs livres
    ).all()

    response_orders = []
    for order in orders:
        response_order_items = []
        for order_item in order.items:
            # S'assurer que le livre est chargé, même si joinedload devrait le faire
            book_details = order_item.book # Accède directement à l'objet livre chargé
            if book_details:
                order_item_dict = {
                    "id": order_item.id,
                    "order_id": order_item.order_id,
                    "book_id": order_item.book_id,
                    "quantity": order_item.quantity,
                    "price_at_purchase": order_item.price_at_purchase,
                    "book": {
                        "id": book_details.id,
                        "title": book_details.title,
                        "author": book_details.author,
                        "description": book_details.description,
                        "price": book_details.price,
                        "pdf_url": book_details.pdf_url,
                        "cover_image_url": book_details.cover_image_url,
                        "category": book_details.category,
                        "created_at": book_details.created_at.isoformat(),
                        "updated_at": book_details.updated_at.isoformat() if book_details.updated_at else None
                    }
                }
                response_order_items.append(order_item_dict)

        response_orders.append({
            "id": order.id,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "status": order.status,
            "order_date": order.order_date.isoformat(),
            "items": response_order_items
        })
    return response_orders


@app.get("/orders/{order_id}", response_model=schemas.OrderResponse)
async def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Récupère les détails d'une commande spécifique appartenant à l'utilisateur connecté.
    """
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.user_id == current_user.id # S'assurer que l'utilisateur est le propriétaire de la commande
    ).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.book)
    ).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande non trouvée ou n'appartient pas à cet utilisateur.")

    # Construire la réponse OrderResponse manuellement
    response_order_items = []
    for order_item in order.items:
        book_details = order_item.book
        if book_details:
            order_item_dict = {
                "id": order_item.id,
                "order_id": order_item.order_id,
                "book_id": order_item.book_id,
                "quantity": order_item.quantity,
                "price_at_purchase": order_item.price_at_purchase,
                "book": {
                    "id": book_details.id,
                    "title": book_details.title,
                    "author": book_details.author,
                    "description": book_details.description,
                    "price": book_details.price,
                    "pdf_url": book_details.pdf_url,
                    "cover_image_url": book_details.cover_image_url,
                    "category": book_details.category,
                    "created_at": book_details.created_at.isoformat(),
                    "updated_at": book_details.updated_at.isoformat() if book_details.updated_at else None
                }
            }
            response_order_items.append(order_item_dict)

    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "order_date": order.order_date.isoformat(),
        "items": response_order_items
    }

@app.post("/favorites", response_model=schemas.FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_book_to_favorites(
    favorite_data: schemas.FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Ajoute un livre aux favoris de l'utilisateur.
    """
    book = db.query(models.Book).filter(models.Book.id == favorite_data.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé.")

    # Vérifier si le livre est déjà en favori pour cet utilisateur
    existing_favorite = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id,
        models.Favorite.book_id == favorite_data.book_id
    ).first()

    if existing_favorite:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce livre est déjà dans vos favoris.")

    db_favorite = models.Favorite(
        user_id=current_user.id,
        book_id=favorite_data.book_id
    )
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    db_favorite.book = book # Attache le livre pour la sérialisation Pydantic

    return db_favorite

@app.get("/favorites", response_model=List[schemas.FavoriteResponse])
async def get_user_favorites(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Récupère tous les livres favoris de l'utilisateur connecté.
    """
    favorites = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id
    ).options(
        joinedload(models.Favorite.book)
    ).all()

    response_favorites = []
    for fav_item in favorites:
        if fav_item.book:
            fav_item_dict = {
                "id": fav_item.id,
                "user_id": fav_item.user_id,
                "book_id": fav_item.book_id,
                "added_at": fav_item.added_at.isoformat(),
                "book": {
                    "id": fav_item.book.id,
                    "title": fav_item.book.title,
                    "author": fav_item.book.author,
                    "description": fav_item.book.description,
                    "price": fav_item.book.price,
                    "pdf_url": fav_item.book.pdf_url,
                    "cover_image_url": fav_item.book.cover_image_url,
                    "category": fav_item.book.category,
                    "created_at": fav_item.book.created_at.isoformat(),
                    "updated_at": fav_item.book.updated_at.isoformat() if fav_item.book.updated_at else None
                }
            }
            response_favorites.append(fav_item_dict)
    return response_favorites

@app.delete("/favorites/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_book_from_favorites(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Supprime un livre spécifique des favoris de l'utilisateur.
    """
    db_favorite = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id,
        models.Favorite.book_id == book_id
    ).first()

    if not db_favorite:
        raise HTTPException(status_code=404, detail="Livre non trouvé dans vos favoris.")

    db.delete(db_favorite)
    db.commit()
    # 204 No Content pour une suppression réussie