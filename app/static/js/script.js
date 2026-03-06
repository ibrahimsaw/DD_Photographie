function sendWhatsApp() {
    const name = document.getElementById("name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const subject = document.getElementById("subject").value.trim();
    const message = document.getElementById("message").value.trim();

    if (!name || !phone || !message) {
        alert("Veuillez remplir le nom, le numéro et le message.");
        return;
    }

    // On récupère le numéro depuis les réglages et on nettoie les espaces
    const DESTINATAIRE = "{{ site_settings.phone }}".replace(/\s+/g, '').replace('+', ''); 

    const text =
        "Nouveau message depuis le site\n\n" +
        "Nom : " + name + "\n" +
        "Téléphone : " + phone + "\n" +
        "Objet : " + subject + "\n\n" +
        "Message :\n" + message;

    const url = "https://wa.me/" + DESTINATAIRE + "?text=" + encodeURIComponent(text);
    window.open(url, "_blank");
}