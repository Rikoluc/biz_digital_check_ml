# BizDigitalCheck ML 🚀

Plateforme web de diagnostic de maturité digitale pour PME — Flask + ML.

## Stack technique
- **Backend** : Flask 3, SQLite, Python 3.11+
- **ML** : scikit-learn (K-Means, PCA, StandardScaler)
- **Frontend** : Bootstrap 5.3, Chart.js 4, Google Fonts (Syne + DM Sans)
- **Déploiement** : Render (Gunicorn, disk persistant)

## Lancement local

```bash
cd biz_digital_check_ml
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

→ Ouvrir http://localhost:5000

## Structure

```
biz_digital_check_ml/
├── app.py            # Routes Flask + logique scoring
├── analysis.py       # ML : K-Means, PCA, recommandations
├── requirements.txt
├── Procfile          # Gunicorn (Render)
├── render.yaml       # Config déploiement Render
├── templates/
│   ├── base.html     # Layout premium dark UI
│   ├── index.html    # Landing page
│   ├── diagnostic.html  # Questionnaire multi-étapes
│   ├── result.html   # Rapport + radar chart
│   ├── dashboard.html   # Dashboard global
│   └── analysis.html    # PCA scatter + clusters
└── instance/
    └── database.db   # SQLite (auto-créé)
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page avec stats globales |
| `/diagnostic` | Questionnaire 24 questions, 6 domaines |
| `/result/<id>` | Rapport individuel avec radar + recommandations |
| `/dashboard` | Vue globale, KPIs, distribution, tendances |
| `/analysis` | Projection PCA 2D + clustering K-Means |

## Déploiement Render

1. Push sur GitHub
2. Créer un **Web Service** sur render.com
3. Pointer sur ce repo
4. Ajouter un **Disk** monté sur `/opt/render/project/src/instance` (1 GB)
5. Build: `pip install -r requirements.txt`
6. Start: `gunicorn app:app --bind 0.0.0.0:$PORT`

## ML — Fonctionnement

- **Score** : somme pondérée des réponses (0–3) → normalisé /100
- **Clustering** : K-Means (k=min(4, n)) sur les 6 scores de domaine, avec StandardScaler
- **PCA** : réduction 6D → 2D pour visualisation scatter
- **Recommandations** : règles expertes par domaine × niveau (low/medium/high)
