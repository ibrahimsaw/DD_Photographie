#!/bin/bash

echo "📁 Création des dossiers..."

# Dossiers principaux
mkdir -p app/admin
mkdir -p app/templates/admin
mkdir -p app/templates/pages
mkdir -p app/static/uploads
mkdir -p app/static/data
mkdir -p app/static/js
mkdir -p app/static/css
mkdir -p app/static/img

echo "📄 Création des fichiers..."

# Fichiers Python
touch app/__init__.py
touch app/models.py
touch app/routes.py
touch app/admin/__init__.py
touch app/admin/routes.py
touch app/admin/forms.py

# Templates admin
touch app/templates/admin/dashboard.html
touch app/templates/admin/add_photo.html
touch app/templates/admin/categories.html
touch app/templates/admin/blog.html

# Templates front
touch app/templates/pages/home.html
touch app/templates/pages/portfolio.html
touch app/templates/pages/contact.html
touch app/templates/pages/blog.html

# Static JS
touch app/static/js/portfolio.js
touch app/static/js/admin.js

# Static DATA (JSON)
touch app/static/data/portfolio.json
touch app/static/data/categories.json

# CSS
touch app/static/css/custom.css

echo "✅ Structure créée avec succès !"