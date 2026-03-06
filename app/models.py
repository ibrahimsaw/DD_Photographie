from . import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import re, os, shutil
from flask import current_app
from sqlalchemy import event

# --- UTILISATEUR ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default="Nom du Photographe")
    title = db.Column(db.String(200), default="Photographe Professionnel")
    bio = db.Column(db.Text)
    about_image = db.Column(db.String(255))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    instagram = db.Column(db.String(255))
    facebook = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    youtube = db.Column(db.String(255))
    behance = db.Column(db.String(255))
    meta_description = db.Column(db.String(255))
    google_analytics = db.Column(db.String(50))
    footer_text = db.Column(db.String(255), default="© 2026 Tous droits réservés")

    @staticmethod
    def get_settings():
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
        return settings

# --- CATÉGORIE ---
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    folder_path = db.Column(db.String(255)) 
    all_photos = db.relationship('Photo', back_populates='category', cascade="all, delete-orphan")

# --- PHOTO ---
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True) # Bien présent !
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category', back_populates='all_photos') 
    content_cover = db.relationship('Content', back_populates='cover_photo', uselist=False)

# --- CONTENU (Blog & Produit) ---
class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False) 
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    gallery = db.Column(db.String(255), nullable=False) 
    cover_image_id = db.Column(db.Integer, db.ForeignKey('photo.id', ondelete="SET NULL"))
    cover_photo = db.relationship('Photo', back_populates='content_cover', foreign_keys=[cover_image_id])

    def __init__(self, **kwargs):
        super(Content, self).__init__(**kwargs)
        if self.title and self.type:
            clean = re.sub(r'[^\w\s-]', '', self.title).strip().lower()
            clean = re.sub(r'[-\s]+', '_', clean)
            self.gallery = f"uploads/{self.type}/{clean}"
        self._ensure_system_category()

    def _ensure_system_category(self):
        # Category est accessible directement ici
        sys_cat = Category.query.filter_by(name="Contenu").first()
        if not sys_cat:
            sys_cat = Category(name="Contenu", folder_path="uploads/system")
            db.session.add(sys_cat)
            db.session.commit()
        if self.cover_photo:
            self.cover_photo.category_id = sys_cat.id

# ===================================================
# ÉVÉNEMENTS (Gestion automatique des dossiers/fichiers)
# ===================================================

@event.listens_for(Category, 'before_insert')
def receive_before_insert(mapper, connection, target):
    if target.name:
        clean_name = re.sub(r'[^\w\s-]', '', target.name).strip().lower()
        clean_name = re.sub(r'[-\s]+', '_', clean_name)
        target.folder_path = f"uploads/{clean_name}"
        full_path = os.path.join(current_app.root_path, 'static', target.folder_path)
        os.makedirs(full_path, exist_ok=True)
        # Créer aussi le dossier thumbs pour la catégorie
        os.makedirs(os.path.join(full_path, 'thumbs'), exist_ok=True)

@event.listens_for(Content, 'after_insert')
def create_content_folder(mapper, connection, target):
    if target.gallery:
        full_path = os.path.join(current_app.root_path, 'static', target.gallery)
        os.makedirs(full_path, exist_ok=True)
        # Créer aussi le dossier thumbs pour le contenu
        os.makedirs(os.path.join(full_path, 'thumbs'), exist_ok=True)

@event.listens_for(Photo, 'after_delete')
def auto_delete_photo_files(mapper, connection, target):
    """Fusion des fonctions de suppression : nettoie HD et Thumbnail"""
    for attr in ['image', 'thumbnail']:
        path = getattr(target, attr)
        if path:
            file_path = os.path.join(current_app.root_path, 'static', path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Erreur suppression fichier {path}: {e}")

@event.listens_for(Category, 'after_delete')
@event.listens_for(Content, 'after_delete')
def delete_folder(mapper, connection, target):
    path_attr = 'folder_path' if hasattr(target, 'folder_path') else 'gallery'
    path = getattr(target, path_attr)
    if path and path != "uploads/system": # Sécurité pour ne pas supprimer le dossier système
        full_path = os.path.join(current_app.root_path, 'static', path)
        if os.path.exists(full_path):
            shutil.rmtree(full_path, ignore_errors=True)