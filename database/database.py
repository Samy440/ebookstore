# database/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de la base de données SQLite. Le fichier sera créé à la racine du projet.
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgre_server/db_name" # Exemple pour PostgreSQL

# create_engine est le "point d'entrée" vers ta base de données.
# connect_args={"check_same_thread": False} est nécessaire pour SQLite
# car il n'est pas thread-safe par défaut. Pour d'autres DB, ce n'est pas nécessaire.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# sessionmaker est une fabrique de sessions. Chaque instance de Session
# sera une transaction de base de données.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# declarative_base retourne une classe de base dont nos modèles de base de données hériteront.
Base = declarative_base()

# Dépendance pour obtenir une session de base de données.
# Nous utiliserons cette fonction dans nos opérations de route pour obtenir une session DB.
def get_db():
    db = SessionLocal()
    try:
        yield db # Le 'yield' rend cette fonction un générateur de dépendance.
    finally:
        db.close() # S'assure que la session est fermée après la requête.