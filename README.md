# ebookstore
# FastAPI E-Bookstore API

## 📚 Description du Projet

Ce projet est une **API RESTful complète pour une boutique d'e-books**, développée avec le framework **FastAPI** en Python. Il vise à fournir une base solide pour une application e-commerce moderne, capable de gérer les utilisateurs, les produits (livres numériques), les paniers d'achat, les listes de favoris et le processus de commande.

L'API est conçue pour être performante et facile à utiliser, offrant des fonctionnalités clés pour un backend de boutique en ligne.

## ✨ Fonctionnalités Implémentées

* **Gestion des Utilisateurs**
    * Inscription et connexion des utilisateurs (authentification **JWT Bearer Token**).
    * Gestion des rôles utilisateur : **Administrateur** et utilisateur standard.
    * Récupération et mise à jour du profil utilisateur.
    * Suppression de compte.
    * Liste de tous les utilisateurs (accès réservé aux administrateurs).

* **Gestion des Livres (E-books)**
    * Ajout, modification (complète/partielle), suppression de livres (accès réservé aux administrateurs).
    * Récupération des détails d'un livre spécifique.
    * Affichage de tous les livres avec options de **pagination** et de **filtrage par catégorie**.

* **Panier d'Achat**
    * Ajout et mise à jour de la quantité de livres dans le panier.
    * Affichage du contenu du panier, incluant le **calcul automatique du prix total** et la **quantité totale d'articles**.
    * Suppression d'articles spécifiques du panier.
    * Vidage complet du panier.

* **Favoris**
    * Ajout et suppression de livres de la liste de favoris d'un utilisateur.
    * Affichage de la liste de favoris.

* **Commandes**
    * Création de commandes à partir du contenu du panier (le panier est vidé après la commande).
    * Enregistrement du **prix du livre au moment de l'achat** pour chaque article de commande.
    * Récupération de l'historique de toutes les commandes d'un utilisateur.
    * Affichage des détails d'une commande spécifique.

* **Sécurité**
    * Authentification JWT pour protéger les endpoints sensibles.
    * Autorisation basée sur les rôles (par exemple, seuls les admins peuvent gérer les livres ou lister les utilisateurs).
    * Gestion des **CORS** (Cross-Origin Resource Sharing) pour permettre l'accès depuis des applications front-end.

* **Qualité de Vie Développeur**
    * **Documentation interactive intégrée (Swagger UI / ReDoc)** générée automatiquement par FastAPI.
    * Typage statique avec Pydantic pour la validation des données.

## 🛠️ Technologies Utilisées

* **Python 3.9+**
* **FastAPI** : Framework web rapide et performant.
* **Uvicorn** : Serveur ASGI pour FastAPI.
* **SQLAlchemy** : ORM pour l'interaction avec la base de données.
* **Pydantic** : Validation des données et sérialisation.
* **SQLite** (par défaut) : Base de données légère pour le développement (facilement configurable pour PostgreSQL, MySQL, etc.).
* **python-jose** : Implémentation de JWT.
* **passlib** : Pour le hachage des mots de passe.
* **pytest** & **httpx** : Pour les tests unitaires et d'intégration.
* **CORS Middleware** : Gestion des requêtes cross-origin.

## 🚀 Démarrage Rapide

Suivez ces étapes pour configurer et exécuter le projet localement.

### Prérequis

* Python 3.9 ou version ultérieure
* `pip` (gestionnaire de paquets Python)

### 1. Cloner le Dépôt

```bash
git clone git@github.com:Samy440/ebookstore.git
cd fastapi-ebookstore-api

2. Créer et Activer l'Environnement Virtuel
Il est fortement recommandé d'utiliser un environnement virtuel pour gérer les dépendances.

Bash

python -m venv venv
# Pour Windows
.\venv\Scripts\activate
# Pour macOS/Linux
source venv/bin/activate
3. Installer les Dépendances
Bash

pip install -r requirements.txt
(Si tu n'as pas encore de fichier requirements.txt, tu peux le créer en exécutant pip freeze > requirements.txt dans ton environnement virtuel.)

4. Lancer l'Application
Bash

uvicorn main:app --reload --port 5000
L'API sera accessible à l'adresse http://127.0.0.1:5000.

5. Accéder à la Documentation Interactive
Une fois l'application lancée, vous pouvez accéder à la documentation Swagger UI à l'adresse :
http://127.0.0.1:5000/docs

Ou à la documentation ReDoc à l'adresse :
http://127.0.0.1:5000/redoc

🧪 Tests
Les tests sont écrits avec pytest et httpx. Ils utilisent une base de données SQLite en mémoire pour garantir l'isolation des tests.

Pour exécuter les tests :

Bash

pytest
🤝 Contribution
Les contributions sont les bienvenues ! Si vous souhaitez améliorer ce projet, n'hésitez pas à ouvrir une issue ou à soumettre une pull request.

📄 Licence
Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

📧 Contact
Pour toute question ou suggestion, n'hésitez pas à me contacter via GitHub ou par email samuelamou536@gmail.com.

Merci d'avoir lu ce README ! 😊

