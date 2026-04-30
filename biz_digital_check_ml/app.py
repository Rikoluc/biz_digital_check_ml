import os, json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from analysis import compute_cluster, compute_pca_data, get_recommendations, score_to_label

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')

# ─── Questions ────────────────────────────────────────────────────────────────

DOMAINS = [
    "Présence en ligne",
    "Outils internes",
    "Marketing digital",
    "Cybersécurité",
    "Data & Analytics",
    "Automatisation & IA",
]

QUESTIONS = [
    # D1 — Présence en ligne
    {"id":"q1_1","domain_id":1,"text":"Votre entreprise possède-t-elle un site web professionnel ?",
     "options":["Non","En cours de création","Oui, site basique","Oui, site optimisé & mobile"]},
    {"id":"q1_2","domain_id":1,"text":"Êtes-vous actif sur les réseaux sociaux ?",
     "options":["Non","1 réseau, inactif","1–2 réseaux actifs" ,"3+ réseaux, publications régulières"]},
    {"id":"q1_3","domain_id":1,"text":"Proposez-vous de la vente en ligne (e-commerce) ?",
     "options":["Non","Réflexion en cours","Marketplace/vente partielle","Boutique complète & optimisée"]},
    {"id":"q1_4","domain_id":1,"text":"Votre présence en ligne est-elle référencée (SEO/GMB) ?",
     "options":["Non","Peu visible","Google Business configuré","Stratégie SEO active"]},
    # D2 — Outils internes
    {"id":"q2_1","domain_id":2,"text":"Utilisez-vous un logiciel de gestion (ERP/CRM) ?",
     "options":["Non","Tableurs Excel uniquement","Logiciel sectoriel basique","ERP/CRM intégré & paramétré"]},
    {"id":"q2_2","domain_id":2,"text":"Vos documents sont-ils stockés dans le cloud ?",
     "options":["Non, serveur local/papier","Partiellement","Cloud basique (Drive/OneDrive)","Cloud + partage + versioning"]},
    {"id":"q2_3","domain_id":2,"text":"Utilisez-vous des outils de collaboration en ligne ?",
     "options":["Non","Email uniquement","1–2 outils (Slack, Teams…)","Suite collaborative complète"]},
    {"id":"q2_4","domain_id":2,"text":"Votre facturation et compta sont-elles numérisées ?",
     "options":["Non, papier","PDF manuels","Logiciel de facturation","Facturation auto + compta cloud"]},
    # D3 — Marketing digital
    {"id":"q3_1","domain_id":3,"text":"Lancez-vous des campagnes publicitaires en ligne ?",
     "options":["Non","Occasionnellement","Régulièrement","Stratégie structurée multi-canaux"]},
    {"id":"q3_2","domain_id":3,"text":"Utilisez-vous l'email marketing ?",
     "options":["Non","Emails manuels ponctuels","Newsletter mensuelle","Séquences automatisées"]},
    {"id":"q3_3","domain_id":3,"text":"Mesurez-vous vos performances marketing ?",
     "options":["Non","Rarement","Quelques KPIs suivis","Dashboard complet avec ROI"]},
    {"id":"q3_4","domain_id":3,"text":"Avez-vous une stratégie de contenu (blog, vidéo, etc.) ?",
     "options":["Non","Publications ponctuelles","Calendrier éditorial","Stratégie multicanal & SEO content"]},
    # D4 — Cybersécurité
    {"id":"q4_1","domain_id":4,"text":"Effectuez-vous des sauvegardes régulières de vos données ?",
     "options":["Non","Rarement / manuellement","Hebdomadaires","Automatiques, testées régulièrement"]},
    {"id":"q4_2","domain_id":4,"text":"Utilisez-vous une solution de cybersécurité ?",
     "options":["Non","Antivirus basique","Suite sécurité complète","Solution managée (MDR/XDR)"]},
    {"id":"q4_3","domain_id":4,"text":"Vos collaborateurs sont-ils sensibilisés à la cybersécurité ?",
     "options":["Non","Sensibilisation informelle","Formation annuelle","Formations régulières + tests"]},
    {"id":"q4_4","domain_id":4,"text":"Avez-vous une politique d'authentification forte (MFA) ?",
     "options":["Non","Mots de passe simples","Politique écrite","MFA + gestionnaire d'accès"]},
    # D5 — Data & Analytics
    {"id":"q5_1","domain_id":5,"text":"Utilisez-vous des outils d'analyse de données ?",
     "options":["Non","Stats basiques manuelles","Google Analytics/similaire","BI + reporting avancé"]},
    {"id":"q5_2","domain_id":5,"text":"Vos décisions sont-elles basées sur des données ?",
     "options":["Non, intuition seule","Parfois","Souvent, KPIs définis","Systématiquement, data-driven"]},
    {"id":"q5_3","domain_id":5,"text":"Disposez-vous de tableaux de bord de performance ?",
     "options":["Non","Tableaux Excel","Dashboard mis à jour mensuellement","Dashboard temps réel automatisé"]},
    {"id":"q5_4","domain_id":5,"text":"Collectez et exploitez-vous des données clients ?",
     "options":["Non","Peu structuré","Base de données clients","CRM + segmentation + personnalisation"]},
    # D6 — Automatisation & IA
    {"id":"q6_1","domain_id":6,"text":"Automatisez-vous des tâches répétitives ?",
     "options":["Non","1–2 tâches manuellement","Plusieurs tâches via outils","Automatisation systématique"]},
    {"id":"q6_2","domain_id":6,"text":"Utilisez-vous des outils d'IA dans votre activité ?",
     "options":["Non","Expérimentation ponctuelle","Quelques outils IA adoptés","IA intégrée aux processus clés"]},
    {"id":"q6_3","domain_id":6,"text":"Avez-vous un chatbot ou assistant digital client ?",
     "options":["Non","En réflexion","Chatbot FAQ basique","IA conversationnelle avancée"]},
    {"id":"q6_4","domain_id":6,"text":"Intégrez-vous des APIs/services tiers dans vos systèmes ?",
     "options":["Non","1–2 intégrations simples","Plusieurs APIs connectées","Architecture API-first"]},
]

SECTORS = [
    "Commerce & Retail","Restauration & Hôtellerie","Santé & Bien-être",
    "BTP & Artisanat","Services aux entreprises","Industrie & Fabrication",
    "Transport & Logistique","Éducation & Formation","Tech & Numérique","Autre",
]

SIZES = ["1–10 employés","11–50 employés","51–200 employés","200+ employés"]

# ─── DB ───────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS diagnostics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                sector TEXT NOT NULL,
                size TEXT NOT NULL,
                answers TEXT NOT NULL,
                domain_scores TEXT NOT NULL,
                digital_score REAL NOT NULL,
                cluster INTEGER DEFAULT 0,
                cluster_label TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

# ─── Scoring ──────────────────────────────────────────────────────────────────

def compute_score(answers):
    domain_scores = {}
    for idx, domain in enumerate(DOMAINS, start=1):
        qs = [q for q in QUESTIONS if q["domain_id"] == idx]
        total = sum(int(answers.get(q["id"], 0)) for q in qs)
        max_pts = len(qs) * 3
        domain_scores[domain] = round((total / max_pts) * 100, 1)
    global_total = sum(int(answers.get(q["id"], 0)) for q in QUESTIONS)
    global_score = round((global_total / (len(QUESTIONS) * 3)) * 100, 1)
    return global_score, domain_scores

def get_all_domain_scores():
    with get_db() as conn:
        rows = conn.execute("SELECT domain_scores FROM diagnostics").fetchall()
    return [[json.loads(r["domain_scores"]).get(d, 0) for d in DOMAINS] for r in rows]

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM diagnostics").fetchone()[0]
        avg = conn.execute("SELECT AVG(digital_score) FROM diagnostics").fetchone()[0]
    return render_template("index.html", count=count, avg=round(avg, 1) if avg else None)


@app.route("/diagnostic", methods=["GET", "POST"])
def diagnostic():
    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip() or "Anonyme"
        sector = request.form.get("sector", "")
        size = request.form.get("size", "")
        answers = {q["id"]: int(request.form.get(q["id"], 0)) for q in QUESTIONS}

        global_score, domain_scores = compute_score(answers)
        label, color, emoji = score_to_label(global_score)

        all_scores = get_all_domain_scores()
        domain_vals = [domain_scores[d] for d in DOMAINS]
        cluster = compute_cluster(all_scores + [domain_vals], len(all_scores))

        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO diagnostics (company_name,sector,size,answers,domain_scores,digital_score,cluster,cluster_label,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (company_name, sector, size, json.dumps(answers), json.dumps(domain_scores),
                 global_score, cluster, label, datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
            diag_id = cursor.lastrowid
            conn.commit()

        return redirect(url_for("result", diag_id=diag_id))

    questions_by_domain = {}
    for idx, domain in enumerate(DOMAINS, start=1):
        questions_by_domain[domain] = [q for q in QUESTIONS if q["domain_id"] == idx]

    return render_template("diagnostic.html", questions_by_domain=questions_by_domain,
                           domains=DOMAINS, sectors=SECTORS, sizes=SIZES)


@app.route("/result/<int:diag_id>")
def result(diag_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM diagnostics WHERE id=?", (diag_id,)).fetchone()
    if not row:
        return redirect(url_for("index"))

    row = dict(row)
    row["domain_scores"] = json.loads(row["domain_scores"])
    row["answers"] = json.loads(row["answers"])
    score = row["digital_score"]
    label, color, emoji = score_to_label(score)
    recommendations = get_recommendations(row["domain_scores"], score)

    radar_data = {
        "labels": DOMAINS,
        "data": [row["domain_scores"].get(d, 0) for d in DOMAINS],
    }

    return render_template("result.html", row=row, score=score, label=label,
                           color=color, emoji=emoji, recommendations=recommendations,
                           radar_data=json.dumps(radar_data), domains=DOMAINS)


@app.route("/dashboard")
def dashboard():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM diagnostics ORDER BY created_at DESC").fetchall()

    diagnostics = []
    for r in rows:
        d = dict(r)
        d["domain_scores"] = json.loads(r["domain_scores"])
        d["label"], d["color"], d["emoji"] = score_to_label(r["digital_score"])
        diagnostics.append(d)

    count = len(diagnostics)
    avg_score = round(sum(d["digital_score"] for d in diagnostics) / count, 1) if count else 0
    max_score = max((d["digital_score"] for d in diagnostics), default=0)
    min_score = min((d["digital_score"] for d in diagnostics), default=0)

    distribution = {"Débutant Digital": 0, "En Transition": 0, "Avancé Digital": 0, "Leader Digital": 0}
    for d in diagnostics:
        if d["label"] in distribution:
            distribution[d["label"]] += 1

    avg_domains = {}
    for domain in DOMAINS:
        avg_domains[domain] = (
            round(sum(d["domain_scores"].get(domain, 0) for d in diagnostics) / count, 1) if count else 0
        )

    # Trend data: last 10 by date
    trend = [{"date": d["created_at"][:10], "score": d["digital_score"]} for d in reversed(diagnostics[-10:])]

    return render_template("dashboard.html", diagnostics=diagnostics, count=count,
                           avg_score=avg_score, max_score=max_score, min_score=min_score,
                           distribution=json.dumps(distribution), avg_domains=json.dumps(avg_domains),
                           domains=DOMAINS, trend=json.dumps(trend))


@app.route("/analysis")
def analysis():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM diagnostics").fetchall()

    all_data = []
    for r in rows:
        d = dict(r)
        d["domain_scores"] = json.loads(r["domain_scores"])
        d["label"], d["color"], d["emoji"] = score_to_label(r["digital_score"])
        all_data.append(d)

    pca_json = "null"
    cluster_stats = {}
    has_ml = len(all_data) >= 4

    if has_ml:
        domain_matrix = [[d["domain_scores"].get(dom, 0) for dom in DOMAINS] for d in all_data]
        pca_result = compute_pca_data(domain_matrix, all_data)
        pca_json = json.dumps(pca_result)

        for d in all_data:
            c = d["cluster_label"]
            if c not in cluster_stats:
                cluster_stats[c] = {"count": 0, "scores": [], "color": d["color"]}
            cluster_stats[c]["count"] += 1
            cluster_stats[c]["scores"].append(d["digital_score"])

        for c in cluster_stats:
            s = cluster_stats[c]["scores"]
            cluster_stats[c]["avg"] = round(sum(s) / len(s), 1)
            cluster_stats[c]["min"] = min(s)
            cluster_stats[c]["max"] = max(s)

    avg_domains = {}
    if all_data:
        for domain in DOMAINS:
            avg_domains[domain] = round(sum(d["domain_scores"].get(domain, 0) for d in all_data) / len(all_data), 1)

    return render_template("analysis.html", all_data=all_data, pca_json=pca_json,
                           cluster_stats=cluster_stats, has_ml=has_ml,
                           avg_domains=json.dumps(avg_domains), domains=DOMAINS, count=len(all_data))

if __name__ == "__main__":
    init_db()                                                                                       
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

