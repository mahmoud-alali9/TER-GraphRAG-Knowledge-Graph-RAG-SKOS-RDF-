import difflib
import re
import sys
import unicodedata

sys.path.insert(0, '/home/salah/Desktop/Study/TER/terragv2-main/venv/lib/python3.12/site-packages')

def _normalize(s):
    s = unicodedata.normalize('NFC', s).lower()
    s = s.replace("'", " ").replace("'", " ").replace("-", " ").replace("(", " ").replace(")", " ")
    return re.sub(r'\s+', ' ', s).strip()


try:
    import pycountry
    from babel import Locale as BabelLocale
    _BABEL_LOCALE = BabelLocale('fr')
    _COUNTRY_FR_TO_EN = {}
    _COUNTRY_EN_TO_EN = {}  # normalized English name → canonical English name
    for _c in pycountry.countries:
        en_name = _c.name
        # French names
        _fr = _BABEL_LOCALE.territories.get(_c.alpha_2, '')
        if _fr:
            for _variant in _fr.replace('/', ',').split(','):  # split "Myanmar (Birmanie)" variants
                _key = _normalize(_variant)
                if _key:
                    _COUNTRY_FR_TO_EN[_key] = en_name
        # English names + common_name + official_name
        for _en in filter(None, [en_name, getattr(_c, 'common_name', None), getattr(_c, 'official_name', None)]):
            _key = _normalize(_en)
            if _key:
                _COUNTRY_EN_TO_EN[_key] = en_name
        # also index alpha-2 code
        _COUNTRY_EN_TO_EN[_c.alpha_2.lower()] = en_name
    # historical/common aliases + accent-stripped variants babel misses
    _EXTRA = {
        'burma':          'Myanmar',
        'birmanie':       'Myanmar',
        'ivory coast':    "Cote d'Ivoire",
        'south korea':    'Korea, Republic of',
        'north korea':    "Korea, Democratic People's Republic of",
        'czech republic': 'Czechia',
        'russia':         'Russian Federation',
        'bresil':         'Brazil',
    }
    for k, v in _EXTRA.items():
        _COUNTRY_FR_TO_EN[k] = v
        _COUNTRY_EN_TO_EN[k] = v
    _HAS_PYCOUNTRY = True
except Exception:
    _COUNTRY_FR_TO_EN = {}
    _COUNTRY_EN_TO_EN = {}
    _HAS_PYCOUNTRY = False

from graph.sparql_executor import execute_sparql

STOPWORDS = {
    "what", "is", "the", "in", "of", "a", "an", "are", "how", "does", "do", "can",
    "define", "definition", "forest", "tree", "forêt", "arbre",
    "déforestation", "afforestation", "reforestation", "reboisement",
    "forestation", "deforestation", "degradation", "dégradation",
    "quelle", "est", "la", "le", "les", "de", "du", "des", "une", "un",
    "selon", "pour", "par", "sur", "avec", "between", "and", "or", "to",
    "définit", "définition", "comment", "donne", "moi", "différence", "difference",
    "entre", "quels", "quel", "quelles",
}

ORG_ALIASES = {
    "fao":        ["UN FAO", "UN-FAO", "FAO"],
    "unfccc":     ["UN FCCC", "UN-FCCC", "UNFCCC", "IPCC Kyoto"],
    "ipcc":       ["IPCC"],
    "eu":         ["European Community", "European Environment Agency", "EU JRC", "EU"],
    "eudr":       ["EU", "European"],
    "world bank": ["World Bank"],
    "unep":       ["UN-EP", "UN EP"],
    "ilo":        ["ILO"],
}

ORG_TRIGGER_WORDS = set(ORG_ALIASES.keys()) | {"unfccc", "kyoto", "european", "eudr"}


def _word_match(key, text):
    return bool(re.search(r'(?<!\w)' + re.escape(key) + r'(?!\w)', text))


def _translate_fr_country(text):
    """Return English country name if a French or English country name is found in text."""
    if not _COUNTRY_FR_TO_EN:
        return None
    normalized = _normalize(text)
    # French names — longest first, require whole-word match, min length 4
    for fr_key in sorted(_COUNTRY_FR_TO_EN, key=len, reverse=True):
        if len(fr_key) >= 4 and _word_match(fr_key, normalized):
            return _COUNTRY_FR_TO_EN[fr_key]
    # English names — same constraints
    for en_key in sorted(_COUNTRY_EN_TO_EN, key=len, reverse=True):
        if len(en_key) >= 4 and _word_match(en_key, normalized):
            return _COUNTRY_EN_TO_EN[en_key]
    return None


def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def _resolve_org(question_lower, endpoint):
    """Check if the question is about a known international organization.

    Returns a list of matching KG labels if found, else empty list.
    """
    for trigger, aliases in ORG_ALIASES.items():
        if trigger in question_lower:
            for alias in aliases:
                bindings, error = execute_sparql(endpoint, f"""
                    PREFIX : <http://example.org/forest#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    SELECT ?label WHERE {{
                        ?s a :Jurisdiction ; rdfs:label ?label .
                        FILTER(CONTAINS(LCASE(?label), "{alias.lower()}"))
                    }} LIMIT 3
                """)
                if error:
                    continue
                matches = [r["label"]["value"] for r in bindings]
                if matches:
                    return matches
    return []


def find_jurisdiction(question, labels, endpoint):
    question_lower = question.lower()
    results = []

    # 0a. Organization alias resolution
    if any(t in question_lower for t in ORG_TRIGGER_WORDS):
        org_matches = _resolve_org(question_lower, endpoint)
        if org_matches:
            results.extend(org_matches)

    # 0b. French/English country name translation via pycountry+babel
    # Always run even if org was found (question may reference both org AND country)
    en_country = _translate_fr_country(question)
    if en_country:
        lower_map = {l.lower(): l for l in labels}
        en_lower = en_country.lower()
        if en_lower in lower_map:
            results.append(lower_map[en_lower])
        else:
            close = difflib.get_close_matches(en_lower, list(lower_map.keys()), n=1, cutoff=0.75)
            if close:
                results.append(lower_map[close[0]])

    if results:
        return results

    keywords = extract_keywords(question)
    if not keywords:
        return []

    # 1. Exact match
    lower_map = {l.lower(): l for l in labels}
    for kw in keywords:
        if kw in lower_map:
            return [lower_map[kw]]

    # 2. Fuzzy match
    lower_labels = list(lower_map.keys())
    for kw in keywords:
        close = difflib.get_close_matches(kw, lower_labels, n=1, cutoff=0.75)
        if close:
            return [lower_map[close[0]]]

    # 3. SPARQL CONTAINS
    for kw in keywords:
        if len(kw) < 4:
            continue
        bindings, error = execute_sparql(endpoint, f"""
            PREFIX : <http://example.org/forest#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?label WHERE {{
                ?s a :Jurisdiction ; rdfs:label ?label .
                FILTER(CONTAINS(LCASE(?label), "{kw}"))
            }} LIMIT 3
        """)
        if error:
            raise RuntimeError(error)
        matches = [r["label"]["value"] for r in bindings]
        if matches:
            return matches

    return []
