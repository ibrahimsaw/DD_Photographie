from app import create_app, db
from flask_migrate import upgrade  # <--- Import de la fonction d'auto-upgrade
from app.models import Category, Photo, Content

app = create_app()

def setup_database():
    with app.app_context():
        # 1. AUTO-MIGRATE (L'équivalent de 'flask db upgrade')
        # Cela applique les fichiers .py présents dans ton dossier /migrations
        try:
            upgrade()
            print("✅ Base de données mise à jour via Flask-Migrate.")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'upgrade : {e}")
            # Si le dossier /migrations n'existe pas, upgrade() échouera.
            # Il faut avoir fait 'flask db init' au moins une fois manuellement.

        # 2. LOGIQUE MÉTIER (Catégorie Système)
        sys_cat = Category.query.filter_by(name="Contenu").first()
        if not sys_cat:
            sys_cat = Category(name="Contenu", folder_path="uploads/system")
            db.session.add(sys_cat)
            db.session.commit()
            print("✅ Catégorie 'Contenu' initialisée.")

        # 3. FIX PHOTOS
        photos_to_fix = Photo.query.join(Content, Content.cover_image_id == Photo.id)\
                                   .filter(Photo.category_id != sys_cat.id).all()
        if photos_to_fix:
            for photo in photos_to_fix:
                photo.category_id = sys_cat.id
            db.session.commit()
            print(f"✅ {len(photos_to_fix)} photos rattachées au système.")

# On prépare tout avant le run
setup_database()

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)