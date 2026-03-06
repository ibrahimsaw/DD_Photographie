fetch("/static/admin/assets/data/menu.json")
    .then(res => res.json())
    .then(data => {
        resolveMenuData(data); // <-- nouveau : résout les paths avant rendu
        renderBrand(data.brand);
        renderMenu(data.menu);
    });

const STATIC_BASE = "/static/admin/";

// Résout un chemin en le rendant absolu vers /static/admin/ sauf si déjà absolu/externe
function resolvePath(p) {
    if (!p) return p;
    // si c'est déjà une URL absolue ou chemin root, ne pas préfixer
    if (/^(https?:\/\/|\/|mailto:|#)/.test(p)) return p;
    return STATIC_BASE + p.replace(/^\/+/, "");
}

// retourne l'URL finale : si c'est externe on renvoie tel quel,
// sinon on cherche dans ROUTE_MAP (injeté par Jinja), sinon on fallback sur resolvePath
function getHref(p, external) {
    if (external) return p;
    if (window.ROUTE_MAP && window.ROUTE_MAP[p]) return window.ROUTE_MAP[p];
    return resolvePath(p);
}

// Parcourt le JSON du menu et remplace les "path" par les URL résolues
function resolveMenuData(data) {
    if (!data) return;

    // brand
    if (data.brand) {
        if (data.brand.home) data.brand.home = getHref(data.brand.home, false);
        if (data.brand.logoSvg) data.brand.logoSvg = getHref(data.brand.logoSvg, false);
    }

    // menu items (récursif)
    function traverse(items) {
        if (!Array.isArray(items)) return;
        items.forEach(item => {
            if (item.path) item.path = getHref(item.path, item.external);
            if (item.children) traverse(item.children);
        });
    }

    traverse(data.menu);
}

function renderBrand(brand) {
    const aside = document.getElementById("layout-menu");

    const brandHtml = `
        <div class="app-brand demo">
        <a href="${resolvePath(brand.home)}" class="app-brand-link">
            <span class="app-brand-logo demo">
            <img src="${resolvePath(brand.logoSvg)}" alt="logo" height="30">
            </span>
            <span class="app-brand-text demo menu-text fw-bolder ms-2">${brand.name}</span>
        </a>
        </div>
    `;

    aside.insertAdjacentHTML("afterbegin", brandHtml);
}

function renderMenu(items) {
    const container = document.getElementById("menu-container");

    items.forEach(item => {

        // HEADER
        if (item.type === "header") {
            container.innerHTML += `
            <li class="menu-header small text-uppercase">
            <span class="menu-header-text">${item.title}</span>
            </li>`;
        }

        // SIMPLE ITEM
        if (item.type === "item") {
            // calcule si active : soit item.active depuis le JSON, soit correspondance avec la variable Flask injectée
            console.log("CURRENT_NAME:", window.CURRENT_NAME, " - item.name:", item.name);
            const isActive = (typeof window.CURRENT_NAME === "string" && item.name && window.CURRENT_NAME === item.name) || !!item.active;
            const path = getHref(item.path, item.external);
            container.innerHTML += `
            <li class="menu-item ${isActive ? "active" : ""}">
            <a href="${path}" class="menu-link" ${item.external ? 'target="_blank"' : ""}>
                <i class="menu-icon tf-icons ${item.icon || ""}"></i>
                <div>${item.title}</div>
            </a>
            </li>`;
        }

        // PARENT WITH CHILDREN
        if (item.type === "parent") {
            const childrenHtml = item.children.map(child => `
            <li class="menu-item">
            <a href="${getHref(child.path)}" class="menu-link">
                <div>${child.title}</div>
            </a>
            </li>
        `).join("");

            container.innerHTML += `
            <li class="menu-item">
            <a href="javascript:void(0);" class="menu-link menu-toggle">
                <i class="menu-icon tf-icons ${item.icon}"></i>
                <div>${item.title}</div>
            </a>
            <ul class="menu-sub">
                ${childrenHtml}
            </ul>
            </li>`;
        }

    });
}