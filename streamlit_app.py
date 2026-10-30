"""Streamlit demo of Forest GraphRAG.

    streamlit run streamlit_app.py

Tab 1 "Assistant" : ask a question, get the sourced answer + intent, SPARQL, context.
Tab 2 "Comparer les retrievers" : same question through dense (FAISS), BM25,
hybrid and see which jurisdictions come back. Works without any LLM key.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from workflow.tracing import tracing_enabled  # noqa: E402

ENDPOINT = os.getenv("SPARQL_ENDPOINT", "local")
EXAMPLES = [
    "Qu'est ce qu'une forêt au sens de l'UNFCCC ?",
    "Qu'est ce qu'une forêt au sens de la FAO ?",
    "Donne moi la définition de la forêt au Ghana",
    "Est ce que la FAO considère la forêt urbaine comme étant une forêt ?",
    "Qu'est ce qu'une forêt au sens de l'EUDR ?",
]

st.set_page_config(page_title="Forest GraphRAG", page_icon="🌳", layout="wide")


@st.cache_resource(show_spinner="Chargement du graphe de connaissances…")
def get_pipeline():
    from workflow.config import WorkflowConfig
    from workflow.pipeline import ForestGraphRAGPipeline

    return ForestGraphRAGPipeline(
        config=WorkflowConfig(endpoint=ENDPOINT, output_dir=Path("outputs"), timeout=120)
    )


@st.cache_resource(show_spinner="Chargement de l'index FAISS…")
def get_retrievers():
    from vector.index import build_retrievers

    return build_retrievers(ENDPOINT)


def llm_configured() -> bool:
    backend = os.getenv("LLM_BACKEND", "groq").lower()
    key = {"groq": "GROQ_API_KEY", "together": "TOGETHER_API_KEY", "mistral": "MISTRAL_API_KEY"}.get(backend)
    return bool(key and os.getenv(key))


# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌳 Forest GraphRAG")
    st.caption("2 553 définitions légales de la forêt, 497 pays et organisations (corpus de Lund, 2018).")
    st.divider()
    st.markdown("**Configuration**")
    st.write("Graphe :", "fichier local (rdflib)" if ENDPOINT == "local" else f"Fuseki `{ENDPOINT}`")
    st.write("LLM :", f"✅ {os.getenv('LLM_BACKEND', 'groq')}" if llm_configured() else "❌ clé API manquante")
    st.write("Traçage LangSmith :", "✅ actif" if tracing_enabled() else "désactivé")
    st.divider()
    question = st.selectbox("Exemples", [""] + EXAMPLES, format_func=lambda q: q or "Choisir un exemple…")

tab_answer, tab_compare = st.tabs(["💬 Assistant", "⚖️ Comparer les retrievers"])

# ── Tab 1: GraphRAG answer ──────────────────────────────────────────────────
with tab_answer:
    st.header("Poser une question")
    q = st.text_input("Question", value=question, placeholder="Qu'est ce qu'une forêt au sens de la FAO ?")
    mode = st.radio("Style de réponse", ["technical", "friendly"], horizontal=True,
                    format_func=lambda m: "Technique" if m == "technical" else "Grand public")

    if st.button("Répondre", type="primary", disabled=not q):
        if not llm_configured():
            st.error("Ajoutez GROQ_API_KEY (ou TOGETHER_API_KEY avec LLM_BACKEND=together) dans .env. "
                     "L'onglet « Comparer les retrievers » marche sans clé.")
        else:
            start = time.perf_counter()
            with st.spinner("Lien juridiction → plan JSON + SPARQL → graphe → réponse…"):
                result = get_pipeline().query(q, mode=mode)
            elapsed = time.perf_counter() - start

            st.markdown(result["answer"])
            c1, c2 = st.columns(2)
            c1.metric("Intention détectée", result["intent"])
            c2.metric("Temps de réponse", f"{elapsed:.1f} s")
            with st.expander("Requête SPARQL générée"):
                st.code(result["sparql_query"] or "(requête gabarit / aucune)", language="sparql")
            with st.expander("Contexte récupéré dans le graphe (sources)"):
                st.text(result["context"])

# ── Tab 2: retriever comparison ─────────────────────────────────────────────
with tab_compare:
    st.header("Graphe vs RAG vectoriel")
    st.caption("Mêmes données, trois façons de chercher. Regardez la colonne « Juridiction » : "
               "pour « UNFCCC », un RAG vectoriel ramène souvent des pays qui citent l'UNFCCC.")
    cq = st.text_input("Requête", value=question or EXAMPLES[0], key="compare_q")
    k = st.slider("Nombre de résultats", 3, 10, 5)

    if st.button("Comparer", disabled=not cq):
        retrievers = get_retrievers()
        columns = st.columns(3)
        labels = {"dense": "Dense (FAISS)", "bm25": "Mots-clés (BM25)", "hybrid": "Hybride (RRF)"}
        for col, name in zip(columns, ("dense", "bm25", "hybrid")):
            start = time.perf_counter()
            hits = retrievers[name].search(cq, k=k)
            ms = (time.perf_counter() - start) * 1000
            with col:
                st.subheader(labels[name])
                st.caption(f"{ms:.0f} ms")
                for hit in hits:
                    with st.container(border=True):
                        st.markdown(f"**{hit.rank}. {hit.doc.jurisdiction}** · score {hit.score:.3f}")
                        st.write(hit.doc.text[:280] + ("…" if len(hit.doc.text) > 280 else ""))
                        if hit.doc.source:
                            st.caption(hit.doc.source[:100])
