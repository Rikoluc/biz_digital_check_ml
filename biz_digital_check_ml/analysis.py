"""
analysis.py — ML engine: K-Means clustering, PCA projection, recommendations.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# ─── Scoring helpers ──────────────────────────────────────────────────────────

def score_to_label(score: float):
    if score < 25:
        return "Débutant Digital", "danger", "🌱"
    elif score < 50:
        return "En Transition", "warning", "🚀"
    elif score < 75:
        return "Avancé Digital", "info", "⚡"
    else:
        return "Leader Digital", "success", "🏆"


# ─── K-Means clustering ───────────────────────────────────────────────────────

def compute_cluster(all_scores: list, current_idx: int) -> int:
    """
    Fit K-Means on all domain-score vectors and return the cluster
    index of the last entry (current_idx == index of new diagnostic).
    Falls back to 0 when not enough data.
    """
    if len(all_scores) < 4:
        return 0

    X = np.array(all_scores, dtype=float)
    n_clusters = min(4, len(all_scores))

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    return int(labels[current_idx])


# ─── PCA 2-D projection ───────────────────────────────────────────────────────

def compute_pca_data(domain_matrix: list, all_data: list) -> dict | None:
    """
    Project 6-D domain vectors onto 2 principal components.
    Returns a dict ready to be JSON-serialised for Chart.js scatter plot.
    """
    if len(domain_matrix) < 2:
        return None

    X = np.array(domain_matrix, dtype=float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_components = min(2, X.shape[0], X.shape[1])
    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    explained = pca.explained_variance_ratio_

    # Build loadings for axis labels
    loadings = pca.components_  # shape (n_components, 6)

    points = []
    for i, (coords, d) in enumerate(zip(X_pca, all_data)):
        points.append({
            "x": round(float(coords[0]), 4),
            "y": round(float(coords[1]), 4) if n_components > 1 else 0.0,
            "company": d["company_name"],
            "score": d["digital_score"],
            "cluster": d["cluster_label"],
            "color": d["color"],
            "id": d["id"],
        })

    return {
        "points": points,
        "explained_variance": [round(float(e) * 100, 1) for e in explained],
        "n_components": n_components,
    }


# ─── Personalised recommendations ─────────────────────────────────────────────

_RECS = {
    "Présence en ligne": {
        "low": [
            ("🌐", "Créez un site vitrine professionnel", "Utilisez WordPress, Webflow ou Wix. Un site mobile-first est la base de votre crédibilité digitale."),
            ("📱", "Ouvrez des comptes réseaux sociaux clés", "Choisissez 2 plateformes adaptées à votre cible (LinkedIn B2B, Instagram B2C) et publiez 3×/semaine."),
            ("🛒", "Évaluez l'e-commerce", "Démarrez avec une présence sur Amazon/Leboncoin avant d'investir dans une boutique propre."),
        ],
        "medium": [
            ("🔍", "Lancez une stratégie SEO", "Rédigez 2 articles de blog par mois ciblant des mots-clés longue traîne de votre secteur."),
            ("📊", "Configurez Google Business Profile", "Renseignez horaires, photos et répondez à tous les avis — impact immédiat sur le référencement local."),
            ("🎯", "Optimisez votre taux de conversion", "Ajoutez des CTA clairs, des témoignages clients et un formulaire de contact visible en haut de page."),
        ],
        "high": [
            ("🚀", "Adoptez une stratégie omnicanale", "Synchronisez votre stock entre boutique physique, site et marketplaces via un PIM."),
            ("📈", "Testez la publicité programmatique", "Explorez Display & Video 360 ou The Trade Desk pour toucher vos audiences hors Google/Meta."),
        ],
    },
    "Outils internes": {
        "low": [
            ("☁️", "Migrez vers Google Workspace ou M365", "Démarrez à 6€/utilisateur/mois — mail, Drive, agenda partagé, visioconférence inclus."),
            ("📋", "Adoptez un outil de gestion de projet", "Notion (gratuit) ou ClickUp centralise vos tâches, docs et wikis d'équipe."),
            ("💼", "Testez un CRM gratuit", "HubSpot Free ou Zoho CRM offrent un suivi client complet sans investissement initial."),
        ],
        "medium": [
            ("🔗", "Connectez vos outils via Make ou Zapier", "Automatisez les flux de données entre votre CRM, email et facturation sans coder."),
            ("📄", "Numérisez votre facturation", "Pennylane ou Indy automatisent facturation + rapprochement bancaire pour moins de 30€/mois."),
        ],
        "high": [
            ("⚙️", "Explorez les ERP PME", "Odoo Community (open source) ou Dolibarr couvrent ventes, stock, RH et compta de manière intégrée."),
            ("🏗️", "Conduisez un audit SI", "Faites cartographier votre système d'information par un consultant pour identifier les redondances et risques."),
        ],
    },
    "Marketing digital": {
        "low": [
            ("📧", "Lancez une newsletter mensuelle", "Brevo (ex-Sendinblue) est gratuit jusqu'à 300 emails/jour. Partagez vos actus et conseils sectoriels."),
            ("📣", "Testez Google Ads avec 100€/mois", "Ciblez des requêtes transactionnelles locales pour un ROI rapide et mesurable."),
            ("📅", "Créez un calendrier éditorial", "Planifiez 12 posts/mois sur 2 réseaux. Utilisez Buffer ou Later pour programmer."),
        ],
        "medium": [
            ("🎯", "Déployez le retargeting", "Configurez un pixel Meta et des audiences similaires pour récupérer les visiteurs non convertis."),
            ("✉️", "Automatisez vos emails", "Mettez en place une séquence de bienvenue (5 emails) + un workflow de relance panier abandonné."),
            ("📊", "Installez Google Tag Manager", "Centralisez tous vos tags de tracking sans toucher au code — déploiement en 1 heure."),
        ],
        "high": [
            ("🤖", "Adoptez un outil de marketing automation", "HubSpot Marketing Hub ou ActiveCampaign permettent lead scoring + nurturing personnalisé."),
            ("📐", "Lancez des A/B tests systématiques", "Testez vos landing pages avec VWO ou Optimizely — améliorations de 20-40% de conversion documentées."),
        ],
    },
    "Cybersécurité": {
        "low": [
            ("🔐", "Activez le MFA partout maintenant", "Google Authenticator ou Authy — 5 minutes de setup, 99% des attaques par credential bloquées."),
            ("💾", "Mettez en place la règle 3-2-1", "3 copies, 2 supports différents, 1 hors site (cloud chiffré). Testez la restauration trimestriellement."),
            ("🛡️", "Déployez un antivirus managé", "Bitdefender GravityZone Small Business couvre 5 postes pour ~150€/an."),
        ],
        "medium": [
            ("🔑", "Adoptez un gestionnaire de mots de passe", "Bitwarden Business (3$/user/mois) ou 1Password Teams — partagez les accès en toute sécurité."),
            ("🎓", "Organisez un exercice anti-phishing", "Proofpoint ou KnowBe4 proposent des simulations gratuites qui réduisent les clics dangereux de 60%."),
            ("📋", "Rédigez une politique de sécurité", "Un document d'une page couvrant mots de passe, appareils personnels et signalement d'incidents."),
        ],
        "high": [
            ("🏢", "Planifiez un audit de sécurité annuel", "Un test de pénétration par un prestataire certifié (PASSI) coûte 3000–8000€ et peut vous éviter le pire."),
            ("📜", "Vérifiez votre conformité RGPD", "Registre des traitements, mentions légales, DPD si nécessaire — obligatoire et source de confiance client."),
        ],
    },
    "Data & Analytics": {
        "low": [
            ("📊", "Installez Google Analytics 4 (GA4)", "Gratuit, puissant. Suivez le trafic, les sources, les conversions et le comportement utilisateur."),
            ("📈", "Définissez 5 KPIs métier essentiels", "CA/mois, taux de conversion, coût d'acquisition, panier moyen, NPS — affichez-les sur un tableau de bord hebdomadaire."),
            ("📋", "Créez un tableau de bord Google Sheets", "Connectez GA4 + votre CRM via des connecteurs natifs. Automatisez la mise à jour hebdomadaire."),
        ],
        "medium": [
            ("🔍", "Explorez Google Looker Studio", "Outil BI gratuit de Google — connectez GA4, Google Ads, Sheets pour des rapports visuels automatiques."),
            ("🗄️", "Centralisez vos données dans un CRM", "Toutes les interactions client dans un seul outil pour segmenter, analyser et personnaliser."),
        ],
        "high": [
            ("🧠", "Évaluez un outil BI avancé", "Metabase (open source), Power BI (10€/user) ou Tableau — pour des analyses multi-sources complexes."),
            ("🔮", "Explorez les modèles prédictifs", "Avec Python/scikit-learn ou un outil no-code, prévoyez vos ventes, votre churn ou votre stock."),
        ],
    },
    "Automatisation & IA": {
        "low": [
            ("🤖", "Identifiez vos 3 tâches les plus chronophages", "Saisie manuelle, relances email, reporting — chacune est automatisable avec Zapier ou Make."),
            ("💬", "Intégrez ChatGPT/Claude dans votre quotidien", "Rédaction, résumés, réponses email, analyse de données — gagnez 1h/jour par collaborateur."),
            ("📞", "Testez un chatbot FAQ sur votre site", "Tidio (gratuit) répond aux questions fréquentes 24h/24 et capte des leads pendant votre sommeil."),
        ],
        "medium": [
            ("⚡", "Déployez des workflows Make avancés", "Connectez CRM → email → Slack → tableur en flux automatisé. ROI visible en < 1 mois."),
            ("🖼️", "Adoptez l'IA générative pour vos visuels", "Midjourney ou Adobe Firefly pour créer vos visuels marketing sans graphiste, en minutes."),
            ("📝", "Explorez les LLMs spécialisés", "Des modèles fine-tunés existent pour votre secteur (juridique, médical, RH) — testez les APIs."),
        ],
        "high": [
            ("🏭", "Cartographiez tous vos processus", "Identifiez les 20% de processus qui représentent 80% des coûts — priorisez leur automatisation."),
            ("🔬", "Développez des outils IA sur mesure", "API Claude/OpenAI + Python = assistant interne, analyseur de docs, ou générateur de rapports custom."),
        ],
    },
}


def get_recommendations(domain_scores: dict, global_score: float) -> list:
    recs = []
    for domain, score in domain_scores.items():
        if score < 33:
            level = "low"
        elif score < 66:
            level = "medium"
        else:
            level = "high"

        if domain not in _RECS:
            continue

        items = _RECS[domain][level]
        # Show all 3 for low, 2 for medium, 1 for high
        shown = items if level == "low" else items[:2] if level == "medium" else items[:1]

        recs.append({
            "domain": domain,
            "score": score,
            "level": level,
            "actions": [{"icon": i[0], "title": i[1], "desc": i[2]} for i in shown],
        })

    # Sort: lowest score first (highest priority)
    recs.sort(key=lambda x: x["score"])
    return recs
