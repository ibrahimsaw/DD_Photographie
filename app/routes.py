from flask import Blueprint, render_template, request, send_file, abort, current_app,jsonify
import os, uuid, zipfile,io
from PIL import Image

print("app.routes import OK")   # debug temporaire
WATERMARK = "static/watermark.png"
main = Blueprint('main', __name__)

def _paths():
    root = current_app.root_path
    upload_dir = os.path.join(root, 'static', 'uploads')
    temp_dir = os.path.join(root, 'temp')
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    return upload_dir, temp_dir

def add_watermark(src_path, out_path):
    # simple watermark example (replace by votre logique)
    base = Image.open(src_path).convert("RGBA")
    try:
        wm = Image.open(os.path.join(current_app.root_path, WATERMARK)).convert("RGBA")
        wm = wm.resize((int(base.width*0.25), int(base.height*0.25)))
        base.paste(wm, (base.width - wm.width - 10, base.height - wm.height - 10), wm)
    except Exception:
        pass
    base.convert("RGB").save(out_path, "JPEG", quality=85)

from app.models import *

@main.context_processor
def inject_settings():
    # On utilise la méthode statique qu'on a créée dans le modèle
    return dict(site_settings=Settings.get_settings())

@main.route("/")
def index():
    from app import db # On s'assure d'avoir db
    from app.models import Category, Photo
    
    # On récupère toutes les catégories
    categories = Category.query.all()
    
    slider_data = []
    
    for cat in categories:
        # On ignore la catégorie système 'contenu' si elle existe
        if cat.name.lower() == 'contenu':
            continue

        # On cherche la dernière photo de CETTE catégorie
        latest_photo = Photo.query.filter_by(category_id=cat.id).order_by(Photo.id.desc()).first()
        
        if latest_photo:
            slider_data.append({
                'category_name': cat.name,
                'image_url': latest_photo.image,
                'image_url_thumb': latest_photo.thumbnail
            })
    
    # DEBUG : Regarde ton terminal après avoir rafraîchi la page
    print(f"DEBUG: Nombre de slides trouvés : {len(slider_data)}")
    for item in slider_data:
        print(f" - Catégorie: {item['category_name']} | Image: {item['image_url']}")

    return render_template("pages/index.html", slider_data=slider_data)

@main.route("/contact")
def contact():
    categories = Category.query.all()
    photos = Photo.query.order_by(Photo.id.desc()).all()
    return render_template("pages/contact.html", categories=categories, photos=photos)

@main.route("/categories")
def categories():
    categories = Category.query.all()
    # On récupère toutes les photos, ou seulement celles marquées pour le categories
    photos = Photo.query.order_by(Photo.id.desc()).all() 
    return render_template("pages/categories.html", categories=categories, photos=photos)

@main.route("/about")
def about():
    return render_template("pages/about-me.html")

@main.route("/content-list/<string:content_type>")
def display_content(content_type):
    if content_type not in ['product', 'blog']:
        abort(404)

    items = Content.query.filter_by(type=content_type, is_published=True)\
                         .order_by(Content.created_at.desc()).all()

    # Configuration dynamique
    config = {
        'product': {
            'title': "Nos Réalisations & Produits",
            'desc': "Découvrez nos prestations et produits exclusifs."
        },
        'blog': {
            'title': "Nos Articles & Actualités",
            'desc': "Découvrez les coulisses et les conseils de notre studio."
        }
    }
    
    current_config = config[content_type]
    
    return render_template("pages/content_view.html", items=items, content_type=content_type, title=current_config['title'],subtitle=current_config['desc'])

@main.route("/content_detail")
def content_detail():
    article_id = request.args.get('id', type=int) 
    article = Content.query.get_or_404(article_id)
    photos_du_projet = []
    folder_path = os.path.join(current_app.static_folder, article.gallery, 'thumbs')

    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.webp'):
                photos_du_projet.append({
                    'thumb_url': f"{article.gallery}/thumbs/{filename}",
                    'full_url': f"{article.gallery}/{filename.replace('.webp', '.jpg')}",
                    'id': filename.replace('.', '_')
                })

    return render_template("pages/content_detail.html", article=article, photos_du_projet=photos_du_projet)


@main.route("/download", methods=["POST"])
def download_images():
    data = request.get_json()
    if not data or 'images' not in data:
        return jsonify({"error": "Aucune image sélectionnée"}), 400

    # Création d'un fichier ZIP en mémoire (pour ne pas encombrer le serveur)
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rel_path in data['images']:
            # rel_path ressemble à "uploads/blog/mariage/thumbs/photo.webp"
            # On veut l'original : "uploads/blog/mariage/photo.jpg"
            
            # 1. On retrouve le chemin de l'original (en sortant du dossier /thumbs/)
            original_rel_path = rel_path.replace('/thumbs/', '/')
            # 2. On remet l'extension JPG (si tes originaux sont en jpg)
            original_rel_path = original_rel_path.replace('.webp', '.jpg')
            
            # Chemin complet sur le serveur
            abs_path = os.path.join(current_app.static_folder, original_rel_path)

            if os.path.exists(abs_path):
                # On ajoute le fichier au ZIP avec son nom d'origine uniquement
                zf.write(abs_path, os.path.basename(abs_path))
            else:
                # Si le JPG n'existe pas, on tente de prendre le fichier tel quel
                fallback_path = os.path.join(current_app.static_folder, rel_path)
                if os.path.exists(fallback_path):
                    zf.write(fallback_path, os.path.basename(fallback_path))

    memory_file.seek(0)
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name="mon_album_photos.zip"
    )