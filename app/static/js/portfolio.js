document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("portfolio-container");
    const menuContainer = document.getElementById("portfolio-menu"); // ⚠ Défini ici

    // Charger les catégories pour le menu
    fetch("/static/data/categories.json")
        .then(res => res.json())
        .then(categories => {
            // Bouton "Tout"
            const allBtn = document.createElement("button");
            allBtn.className = "active btn";
            allBtn.dataset.filter = "*";
            allBtn.textContent = "Tout";
            menuContainer.appendChild(allBtn);

            // Autres catégories
            categories.forEach(cat => {
                const btn = document.createElement("button");
                btn.className = "btn";
                btn.dataset.filter = `.${cat.style}`;
                btn.textContent = cat.name;
                menuContainer.appendChild(btn);
            });

            // Activer le filtrage après création des boutons
            setupFiltering();
        });

    // Charger les images
    fetch("/static/data/portfolio.json")
        .then(res => res.json())
        .then(data => {
            createGallery(data);
        });

    function createGallery(items) {
        container.innerHTML = "";

        items.forEach(item => {
            const categoriesClass = item.categories.join(" ");

            const div = document.createElement("div");
            div.className = `col-12 col-sm-6 col-md-4 col-lg-3 column_single_gallery_item ${categoriesClass}`;

            div.innerHTML = `
                <img src="/static/${item.image}" alt="">
                <div class="hover_overlay">
                    <a class="gallery_img" href="/static/${item.image}">
                        <i class="fa fa-eye"></i>
                    </a>
                </div>
            `;

            container.appendChild(div);
        });
    }

    function setupFiltering() {
        const buttons = menuContainer.querySelectorAll(".btn"); // ⚠ Sélection après création
        buttons.forEach(btn => {
            btn.addEventListener("click", () => {
                buttons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");

                const filter = btn.dataset.filter;
                const items = document.querySelectorAll(".column_single_gallery_item");

                items.forEach(item => {
                    if (filter === "*" || item.classList.contains(filter.slice(1))) {
                        item.style.display = "block";
                    } else {
                        item.style.display = "none";
                    }
                });
            });
        });
    }
});
