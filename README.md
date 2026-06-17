# Forest GraphRAG

> **Graph Retrieval-Augmented Generation** pour interroger des définitions de la forêt à travers 497 juridictions mondiales.

Pipeline RAG basé sur un graphe de connaissances **SKOS/RDF**, servi par **Apache Jena Fuseki**, interrogé via **SPARQL**, et augmenté par **Llama 3.3 70B** (Groq). Comprend un système d'évaluation intégré combinant retour expert humain et scoring automatisé **RAGAS**.

---

## Fonctionnement

```
Question (FR / EN)
       │
       ▼
  [1] Planner  (Groq LLM)
      Classifie l'intention + génère une requête SPARQL
       │
       ▼
  [2] NERDLinking  (pycountry + fuzzy + SPARQL CONTAINS)
      Résout les juridictions : organisations (FAO, UNFCCC, EUDR…) et pays
       │
       ▼
  [3] SPARQL Executor  (Jena Fuseki)
      Exécute la requête — auto-corrige en cas d'erreur
      Fallback : fuzzy match + requête template
       │
       ▼
  [4] Generator  (Groq LLM)
      Produit une réponse Markdown (mode technique ou accessible)
       │
       ▼
  Réponse ──► EvaluationService ──► SQLite (graph_rag_eval.db)
                                         │
                                Expert (PATCH) + RAGAS (POST)
```

---

## Fonctionnalités

- **Requêtes multilingues** — français et anglais nativement pris en charge
- **NED (Named Entity Disambiguation)** — résolution des juridictions via alias d'organisation, traduction FR→EN, correspondance exacte, floue et SPARQL CONTAINS
- **Deux modes de réponse** — `technical` (expert) et `friendly` (grand public)
- **Correction automatique SPARQL** — le LLM relance en auto-fix si la requête échoue
- **Évaluation hybride** — feedback expert (note 1–5) + métriques RAGAS automatisées
- **API REST** — FastAPI avec documentation Swagger intégrée
- **Déploiement Docker** — Fuseki + chargeur TTL via Docker Compose

---

## Graphe de connaissances (SKOS/RDF)

Le schéma est défini en Turtle (`data/schema.ttl`) avec les préfixes standards :

| Préfixe | URI |
|---------|-----|
| `rdf` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#` |
| `rdfs` | `http://www.w3.org/2000/01/rdf-schema#` |
| `skos` | `http://www.w3.org/2004/02/skos/core#` |
| `dcterms` | `http://purl.org/dc/terms/` |
| `:` | `http://example.org/forest#` |

**Classes principales :**

| Classe | Description |
|--------|-------------|
| `:Definition` | Définition normative d'une juridiction |
| `:Jurisdiction` | Entité institutionnelle ou géographique auteure d'une définition |
| `:JurisdictionLevel` | Échelle de la définition (General, International, National, Local) |
| `:InterpretationCategory` | Angle de définition (Administrative, LandCover, LandUse, Ecological) |

---

## Structure du projet

```
.
├── config.py              # Paramètres chargés depuis .env
├── main.py                # Factory FastAPI — assemble app/ + workflow/
├── run_server.py          # Point d'entrée : serveur API
├── run.py                 # Point d'entrée : CLI interactif
├── run_batch_eval.py      # Évaluation en lot (26 questions de référence)
├── run_ragas.py           # Scoring RAGAS post-évaluation
├── run_llm_comparison.py  # Comparaison de modèles LLM
│
├── app/                   # Couche API + évaluation
│   ├── models.py          # Dataclasses : EvaluationEntry, ExpertFeedback, RagasScores
│   ├── db.py              # EvaluationDB — SQLite CRUD
│   ├── ragas_runner.py    # RagasRunner — wraps RAGAS evaluate() avec juge OpenAI
│   ├── service.py         # EvaluationService — orchestre DB + RAGAS
│   └── routes.py          # Routes HTTP (FastAPI APIRouter)
│
├── workflow/              # Pipeline RAG (LlamaIndex Workflow)
│   ├── groq_client.py     # Wrapper Groq API — ask_llm()
│   ├── prompts.py         # Prompts système : modes technical/friendly + règles Markdown
│   ├── planner.py         # LLM → intention + requête SPARQL (+ auto-fix)
│   ├── nerd_linking.py    # Liaison d'entités juridiction (exact → fuzzy → SPARQL)
│   ├── context_formatter.py # Formate les bindings SPARQL pour le LLM
│   ├── retriever.py       # Retriever : LLM query → fix → synthesis → template fallback
│   ├── tools.py           # Wrappers appelés par les étapes du workflow
│   ├── steps.py           # Étapes LlamaIndex : prepare → plan → link → retrieve → generate
│   ├── pipeline.py        # ForestGraphRAGPipeline — charge les labels, expose query()
│   └── config.py          # WorkflowConfig, PipelineResult, types Event
│
├── graph/                 # Utilitaires SPARQL (sans LLM)
│   ├── label_loader.py    # Charge tous les labels juridiction/catégorie/concept depuis Fuseki
│   └── sparql_executor.py # Exécute une requête SPARQL, retourne (bindings, erreur)
│
├── data/
│   └── schema.ttl         # Graphe de connaissances (SKOS/RDF)
│
├── scripts/
│   └── load_ttl.sh        # Script de chargement du TTL dans Fuseki
│
├── reports/               # Rapports d'évaluation et changelog pipeline
├── docker-compose.yml     # Fuseki + fuseki-loader
└── Dockerfile
```

---

## Installation

### Prérequis

- Python 3.10+
- Docker + Docker Compose
- [Clé API Groq](https://console.groq.com) — niveau gratuit disponible
- [Clé API OpenAI](https://platform.openai.com) — uniquement pour le scoring RAGAS

### 1. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Remplir le fichier `.env` :

```env
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
SPARQL_ENDPOINT=http://localhost:3030/forestKG/sparql
```

### 2. Installer les dépendances Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Démarrer Fuseki et charger le graphe

```bash
docker compose up fuseki fuseki-loader
```

Attendre le message : `fuseki-loader | [loader] TTL loaded successfully`

Interface Fuseki : http://localhost:3030

### 4. Lancer l'application

```bash
# Serveur API
python run_server.py          # → http://localhost:8000/docs

# CLI interactif
python run.py
```

---

## Modes de réponse

Chaque requête passe par un des deux modes, passé en `"mode"` dans la requête :

| Mode | Audience | Style |
|------|----------|-------|
| `technical` | Experts | Terminologie précise, citations exactes, seuils numériques |
| `friendly` | Grand public | Langage simple, définitions inline, section **Key Takeaway** |

**Formats Markdown selon l'intention détectée :**

| Intention | Format de sortie |
|-----------|-----------------|
| `definitional` | Titre `###` + bullets par seuil |
| `comparative` | Tableau : Pays \| Année \| Couvert % \| Hauteur \| Superficie \| Catégorie |
| `synthesis` | Sections `##` + tableau récapitulatif |
| `filtering` | Tableau trié par l'attribut filtré |
| `alignment` | Tableau : Organisation \| Définition \| Couvert % \| Notes |

---

## Référence API

### Requête

| Méthode | Chemin | Description |
|---------|--------|-------------|
| `POST` | `/message` | Poser une question, obtenir une réponse Markdown |
| `POST` | `/message/both-modes` | Exécuter la même question dans les deux modes |

**`POST /message`**
```json
{ "message": "Qu'est-ce qu'une forêt au sens de la FAO ?", "mode": "technical" }
```

**`POST /message/both-modes`**
```json
{ "message": "Compare les définitions de la forêt entre la France et l'Allemagne" }
```

### Évaluation

| Méthode | Chemin | Description |
|---------|--------|-------------|
| `POST`  | `/evaluations` | Créer manuellement une entrée d'évaluation |
| `PATCH` | `/evaluations/{id}/feedback` | Soumettre une note expert (1–5) |
| `POST`  | `/evaluations/{id}/ragas` | Lancer le scoring RAGAS (nécessite `OPENAI_API_KEY`) |
| `GET`   | `/evaluations` | Lister les évaluations (`?status=WRONG\|PARTIAL\|CORRECT`) |
| `GET`   | `/evaluations/{id}` | Détail complet d'une évaluation |
| `GET`   | `/stats` | Métriques agrégées sur toutes les évaluations |

**Note expert → statut :**

| Note | Statut |
|------|--------|
| 1 – 2 | `WRONG` |
| 3 | `PARTIAL` |
| 4 – 5 | `CORRECT` |

**Métriques RAGAS :**

| Métrique | Nécessite `expert_correction` ? |
|----------|---------------------------------|
| `faithfulness` | Non |
| `context_precision` | Non |
| `context_recall` | Oui |
| `factual_correctness` | Oui |
| `semantic_similarity` | Oui |

Les scores vont de **0 → 1** (plus élevé = meilleur).

---

## Flux d'évaluation complet

```bash
# 1. Poser une question — enregistrée automatiquement en base
curl -X POST http://localhost:8000/message \
     -H "Content-Type: application/json" \
     -d '{"message": "Quelle est la définition de la forêt en Albanie ?", "mode": "friendly"}'

# 2. Lister les évaluations pour récupérer l'eval_id
curl http://localhost:8000/evaluations | python3 -m json.tool

# 3. Soumettre le feedback expert
curl -X PATCH http://localhost:8000/evaluations/<eval_id>/feedback \
     -H "Content-Type: application/json" \
     -d '{"expert_rating": 4, "expert_note": "Précis et bien cité"}'

# 4. Lancer le scoring RAGAS
curl -X POST http://localhost:8000/evaluations/<eval_id>/ragas \
     -H "Content-Type: application/json" \
     -d '{}'

# 5. Stats agrégées
curl http://localhost:8000/stats | python3 -m json.tool
```

### Évaluation en lot

Pour évaluer les 26 questions de référence en une seule exécution :

```bash
python run_batch_eval.py
```

Les résultats sont sauvegardés dans `graph_rag_eval.db` avec un numéro de version incrémental permettant de comparer les runs.

---

## Référence de configuration

Tous les paramètres sont dans `config.py` et surchargeables via `.env` :

| Paramètre | Variable env | Défaut | Description |
|-----------|-------------|--------|-------------|
| `sparql_endpoint` | `SPARQL_ENDPOINT` | `localhost:3030/forestKG/sparql` | Endpoint SPARQL Fuseki |
| `output_dir` | `OUTPUT_DIR` | `outputs/` | Dossier de sauvegarde des réponses `.txt` |
| `workflow_timeout` | `WORKFLOW_TIMEOUT` | `120` | Durée max (secondes) par exécution pipeline |
| `db_path` | `DB_PATH` | `graph_rag_eval.db` | Base SQLite des évaluations |
| `logger_enabled` | `LOGGER_ENABLED` | `true` | Log automatique des réponses en base sur `/message` |
| `ragas_model` | `RAGAS_MODEL` | `gpt-4o-mini` | Modèle OpenAI utilisé comme juge RAGAS |
| `admin_password` | `ADMIN_PASSWORD` | _(vide)_ | Protège les endpoints admin |

---

## Exemples de requêtes

| Intention | Exemple |
|-----------|---------|
| Définition | Qu'est-ce qu'une forêt au sens de la FAO ? |
| Définition | What is the forest definition in Albania? |
| Comparative | Quelles sont les principales différences entre forêt primaire et forêt naturellement régénérée ? |
| Filtrage | Which countries require more than 30% canopy cover? |
| Synthèse | What are the global trends in forest definitions? |
| Booléen | Est-ce qu'une plantation forestière est une forêt au sens de l'UNFCCC ? |
| Alignment | L'EUDR reprend-elle essentiellement les définitions de la FAO ? |

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Graphe de connaissances | Apache Jena Fuseki 5.0 (SPARQL 1.1) |
| Ontologie | SKOS / RDF / RDFS / Dublin Core |
| LLM planning & génération | Llama 3.3 70B via Groq API |
| Évaluation automatisée | RAGAS + GPT-4o-mini (OpenAI) |
| Framework RAG | LlamaIndex Workflow |
| API REST | FastAPI + Uvicorn |
| Base évaluation | SQLite |
| Liaison d'entités | pycountry + Babel + difflib |
| Conteneurisation | Docker + Docker Compose |
