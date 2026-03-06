from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
import os
from werkzeug.utils import secure_filename
from app.models import Photo, Category, User, Content,Settings
from app import db
from sqlalchemy.orm import joinedload

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ==========================================
# AUTHENTIFICATION & DASHBOARD
# ==========================================
from PIL import Image

from PIL import Image, ImageOps

def handle_thumbnail_creation(relative_path):
    """Crée une miniature WebP et retourne son chemin relatif"""
    if not relative_path:
        return None
        
    abs_path = os.path.join(current_app.static_folder, relative_path)
    if not os.path.exists(abs_path):
        return None

    directory = os.path.dirname(abs_path)
    filename = os.path.basename(abs_path)
    
    # 1. On force l'extension en .webp (plus performant que le .jpg)
    base_name = os.path.splitext(filename)[0]
    thumb_filename = f"{base_name}.webp"
    
    thumb_dir = os.path.join(directory, 'thumbs')
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir, exist_ok=True)
        
    thumb_abs_path = os.path.join(thumb_dir, thumb_filename)
    
    # Chemin relatif pour la base de données
    rel_dir = os.path.dirname(relative_path)
    thumb_rel_path = os.path.join(rel_dir, 'thumbs', thumb_filename).replace('\\', '/')

    try:
        with Image.open(abs_path) as img:
            # 2. Correction automatique de l'orientation (Exif)
            img = ImageOps.exif_transpose(img)

            # 3. Redimensionnement (LANCZOS pour une netteté maximale)
            # On utilise une taille max de 600px
            img.thumbnail((600, 600), Image.Resampling.LANCZOS)
            
            # 4. Conversion intelligente pour WebP
            # WebP supporte la transparence (RGBA), donc on garde le mode original
            # ou on convertit en RGB si nécessaire.
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
                
            # 5. Sauvegarde en format WEBP (Beaucoup plus léger que le JPEG)
            img.save(thumb_abs_path, "WEBP", quality=80, method=6)
            
        return thumb_rel_path
    except Exception as e:
        print(f"Erreur miniature pour {filename} : {e}")
        return None










import json

@admin_bp.context_processor
def inject_admin_menu():
    # Construction du chemin dynamique vers ton fichier JSON
    json_path = os.path.join(current_app.static_folder, 'admin', 'assets', 'data', 'menu_admin.json')
    
    admin_menu = []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            admin_menu = json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement du menu JSON : {e}")
        # Menu de secours si le fichier est introuvable ou mal formé
        admin_menu = [{"title": "Erreur Menu", "type": "header"}]
    
    return dict(admin_menu=admin_menu)

@admin_bp.route("/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.check_password(request.form["password"]):
            login_user(user)
            flash("Connexion réussie", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Identifiants incorrects", "danger")
    return render_template("admin/login.html")

@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Déconnexion réussie", "success")
    return redirect(url_for("admin.login"))

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    site_settings = Settings.get_settings()
    return render_template(
        "admin/pages/dashboard.html",
        site_settings=site_settings, # <--- C'est cette ligne qui corrige ton erreur
        photos_count=Photo.query.count(),
        categories_count=Category.query.count(),
        blogs_count=Content.query.filter_by(type='blog').count(),
        products_count=Content.query.filter_by(type='product').count(),
        name=site_settings.name or 'Administrateur' # On utilise le vrai nom si possible
    )

@admin_bp.route("/create-admin")
def create_admin():
    if User.query.filter_by(username="admin").first():
        return "Admin existe déjà"
    admin = User(username="admin")
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return "Admin créé (Identifiants: admin / admin123)"



@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    setting = Settings.get_settings()
    if request.method == "POST":
        # --- 1. GESTION DE LA PHOTO ---
        file = request.files.get('about_image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            # Dossier spécifique : static/uploads/profile
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'profile')
            
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # Sauvegarde physique
            file.save(os.path.join(upload_folder, filename))
            # Mise à jour du chemin en DB
            setting.about_image = f"uploads/profile/{filename}"

        # --- 2. INFOS GÉNÉRALES ---
        setting.name = request.form.get("name")
        setting.title = request.form.get("title")
        setting.bio = request.form.get("bio")
        
        # --- 3. CONTACTS ---
        setting.email = request.form.get("email")
        setting.phone = request.form.get("phone")
        setting.address = request.form.get("address")
        setting.city = request.form.get("city") # <--- Ajouté

        # --- 4. RÉSEAUX SOCIAUX ---
        setting.instagram = request.form.get("instagram")
        setting.facebook = request.form.get("facebook")
        setting.twitter = request.form.get("twitter")   # <--- Ajouté
        setting.linkedin = request.form.get("linkedin")
        setting.youtube = request.form.get("youtube")   # <--- Ajouté
        setting.behance = request.form.get("behance")

        # --- 5. SEO & SITE ---
        setting.meta_description = request.form.get("meta_description")
        setting.google_analytics = request.form.get("google_analytics") # <--- Ajouté
        setting.footer_text = request.form.get("footer_text")

        db.session.commit()
        flash("Tous les réglages ont été mis à jour !", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", setting=setting)


# ==========================================
# GESTION DES CATÉGORIES (Stock Global)
# ==========================================

@admin_bp.route("/categories")
@login_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    return render_template("admin/pages/categories.html", categories=cats, category=None, name="categories")

@admin_bp.route("/category/detail/<int:id>")
@login_required
def category_detail(id):
    # On récupère la catégorie ou on renvoie une erreur 404
    category = Category.query.get_or_404(id)
    
    # Grace à back_populates='category', on accède directement aux photos
    photos = category.all_photos 
    
    return render_template("admin/pages/category_detail.html", category=category, photos=photos)
    
@admin_bp.route("/categories/add", methods=["POST"])
@admin_bp.route("/categories/edit/<int:id>", methods=["POST"])
@login_required
def category_form(id=None):
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Le nom est requis", "danger")
        return redirect(url_for("admin.categories"))

    category = Category.query.get(id) if id else None
    
    if category:  # ÉDITION
        category.name = name
        # Le dossier ne change pas pour ne pas casser les liens images existants
        db.session.commit()
        flash("Catégorie modifiée", "success")
    else:  # CRÉATION
        if Category.query.filter_by(name=name).first():
            flash("Cette catégorie existe déjà", "danger")
        else:
            new_cat = Category(name=name)
            db.session.add(new_cat)
            db.session.commit()
            flash("Catégorie ajoutée (Dossier créé)", "success")
            
    return redirect(url_for("admin.categories"))

@admin_bp.route("/categories/delete/<int:id>", methods=["POST"])
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    
    # --- PROTECTION SYSTÈME ---
    # On interdit la suppression de la catégorie réservée au contenu du site
    if cat.name == "Contenu":
        flash("Action impossible : La catégorie 'Contenu' est protégée car elle contient les photos de vos articles et produits.", "danger")
        return redirect(url_for("admin.categories"))
    
    # Si ce n'est pas la catégorie système, on procède à la suppression
    try:
        # L'event 'after_delete' dans models.py supprimera le dossier physique
        db.session.delete(cat)
        db.session.commit()
        flash(f"La catégorie '{cat.name}' et toutes ses photos ont été supprimées.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "danger")
        
    return redirect(url_for("admin.categories"))

# ==========================================
# GESTION DES PHOTOS (Stock Global)
# ==========================================



@admin_bp.route("/photos")
@login_required
def photos():
    # On utilise joinedload pour récupérer la catégorie en UNE SEULE requête
    # Cela évite le problème du "N+1 queries"
    all_photos = Photo.query.options(joinedload(Photo.category))\
                            .order_by(Photo.id.desc()).all()
                            
    categories = Category.query.order_by(Category.name).all()
    
    return render_template("admin/pages/photos.html", photos=all_photos, categories=categories, name="photos")

@admin_bp.route("/photos/add", methods=["POST"])
@login_required
def photo_form():
    category_id = request.form.get("category_id")
    category = Category.query.get_or_404(category_id)
    files = request.files.getlist('images')

    # Chemin absolu du dossier de la catégorie
    upload_path = os.path.join(current_app.static_folder, category.folder_path)
    
    count = 0
    for f in files:
        if f and f.filename:
            filename = secure_filename(f.filename)
            # Gestion des doublons de nom de fichier
            base, ext = os.path.splitext(filename)
            candidate = filename
            i = 1
            while os.path.exists(os.path.join(upload_path, candidate)):
                candidate = f"{base}_{i}{ext}"
                i += 1
            
            # 1. Sauvegarde de l'image HD sur le disque
            rel_image_path = f"{category.folder_path}/{candidate}"
            f.save(os.path.join(upload_path, candidate))
            
            # 2. GÉNÉRATION DE LA MINIATURE (Création du fichier physique)
            thumb_path = handle_thumbnail_creation(rel_image_path)
            
            # 3. ENREGISTREMENT EN BASE DE DONNÉES (HD + Miniature)
            new_photo = Photo(
                image=rel_image_path, 
                thumbnail=thumb_path, # Enregistre le chemin du dossier /thumbs/
                category_id=category.id
            )
            db.session.add(new_photo)
            count += 1
    
    db.session.commit()
    flash(f"{count} photo(s) ajoutée(s) avec succès dans {category.name}", "success")
    return redirect(url_for('admin.photos'))


@admin_bp.route("/photos/delete/<int:id>", methods=["POST"])
@login_required
def delete_photo(id):
    photo = Photo.query.get_or_404(id)
    # L'event 'after_delete' dans models.py supprimera le fichier sur le disque
    db.session.delete(photo)
    db.session.commit()
    flash("Photo supprimée", "success")
    return redirect(url_for("admin.photos"))

# ==========================================
# GESTION DU CONTENU (BLOG & PRODUITS)
# ==========================================

@admin_bp.route("/content/<string:type>")
@login_required
def content_list(type):
    items = Content.query.filter_by(type=type).order_by(Content.created_at.desc()).all()
    name = "blogs" if type == "blog" else "products"
    return render_template("admin/pages/contents.html", contents=items, content_type=type, name=name)

# Dans ta classe Content dans models.py
@property
def photo_count(self):
    from app.models import Photo
    return Photo.query.filter(Photo.image.like(f"{self.gallery}/%")).count()

@admin_bp.route("/content/add/<string:type>", methods=["GET", "POST"])
@admin_bp.route("/content/edit/<int:id>", methods=["GET", "POST"])
@login_required
def content_form(type=None, id=None):
    content = Content.query.get(id) if id else None
    current_type = type if type else (content.type if content else 'blog')

    existing_photos = []
    if content:
        existing_photos = Photo.query.filter(Photo.image.like(f"{content.gallery}/%")).all()

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        
        # --- RÉCUPÉRATION DU STATUT DE PUBLICATION ---
        # Si la checkbox 'is_published' est cochée, elle sera dans request.form
        is_published = 'is_published' in request.form 

        # 1. Gestion de la Création / Mise à jour du contenu
        if not content:
            content = Content(
                type=current_type, 
                title=title, 
                description=description, 
                price=float(price) if price and price != "" else None,
                is_published=is_published  # Ajout ici
            )
            db.session.add(content)
            db.session.flush() # Génère l'ID et crée le dossier via l'event
        else:
            content.title = title
            content.description = description
            content.price = float(price) if price and price != "" else None
            content.is_published = is_published  # Ajout ici

        # 2. SUPPRESSION DES PHOTOS COCHÉES
        photos_to_delete_ids = request.form.getlist('delete_photos')
        for photo_id in photos_to_delete_ids:
            p_to_del = Photo.query.get(int(photo_id))
            if p_to_del:
                if content.cover_image_id == p_to_del.id:
                    content.cover_image_id = None
                db.session.delete(p_to_del)

        # 3. UPLOAD DES NOUVELLES PHOTOS AVEC MINIATURES
        upload_path = os.path.join(current_app.static_folder, content.gallery)
        files = request.files.getlist('images')
        for f in files:
            if f and f.filename:
                fname = secure_filename(f.filename)
                rel_img_path = f"{content.gallery}/{fname}"
                
                # Sauvegarde HD
                f.save(os.path.join(upload_path, fname))
                
                # GÉNÉRATION DE LA MINIATURE
                t_path = handle_thumbnail_creation(rel_img_path)
                
                # Création en BDD (catégorie 1 = Contenu système)
                new_p = Photo(
                    image=rel_img_path, 
                    thumbnail=t_path, 
                    category_id=1
                )
                db.session.add(new_p)
                db.session.flush()
                
                if not content.cover_image_id:
                    content.cover_image_id = new_p.id
                    db.session.flush()

        # 4. MISE À JOUR DE LA COUVERTURE
        cover_id = request.form.get("cover_image_id")
        if cover_id and cover_id not in photos_to_delete_ids:
            content.cover_image_id = int(cover_id)

        db.session.commit()
        flash(f"Contenu {'publié' if content.is_published else 'enregistré en brouillon'}", "success")
        return redirect(url_for("admin.content_list", type=current_type))

    return render_template("admin/pages/content_form.html", content=content, content_type=current_type, photos=existing_photos)

@admin_bp.route("/<string:type>/<int:id>")
def content_detail(type, id):
    item = Content.query.get_or_404(id)
    album_photos = Photo.query.filter(Photo.image.like(f"{item.gallery}/%")).all()

    return render_template("admin/pages/content_detail.html", item=item, photos=album_photos)

@admin_bp.route("/content/delete/<int:id>", methods=["POST"])
@login_required
def delete_content(id):
    item = Content.query.get_or_404(id)
    c_type = item.type
    # L'event 'after_delete' dans models.py supprimera le dossier gallery entier
    db.session.delete(item)
    db.session.commit()
    flash("Contenu et dossier d'images supprimés", "success")
    return redirect(url_for("admin.content_list", type=c_type))