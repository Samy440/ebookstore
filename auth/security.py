# auth/security.py
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from decouple import config

# Configuration pour le hachage des mots de passe
# 'bcrypt' est un algorithme de hachage de mot de passe robuste et recommandé.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration pour les JWT
# Une clé secrète forte est cruciale pour la sécurité de tes tokens.
# EN PRODUCTION, CELA DOIT ÊTRE UNE VARIABLE D'ENVIRONNEMENT !
SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM", default="HS256")  # Algorithme de signature JWT

ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Durée de validité du token d'accès

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe clair correspond au mot de passe haché."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hache un mot de passe."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """Décode un JWT et retourne les données."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None # Token invalide ou expiré