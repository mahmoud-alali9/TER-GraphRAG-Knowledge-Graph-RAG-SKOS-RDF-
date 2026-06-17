# ForestGraphRAG — Evaluation Report v1
Generated: 2026-05-20 14:23 UTC  |  Questions: 26  |  DB: graph_rag_eval.db

---

## Summary

| Metric | Value |
|--------|-------|
| Average expert rating | **2.62/5** |
| Validated (5 or 4) | 7 |
| Corrected (3 or 2) | 10 |
| Rejected (1) | 9 |

### Rating Distribution

```
  5/5 [████                      ] 4
  4/5 [███                       ] 3
  3/5 [███████                   ] 7
  2/5 [███                       ] 3
  1/5 [█████████                 ] 9
```

### Top Issues

- `echec-retrieval` — 7×
- `EUDR-absent-du-corpus` — 3×
- `NOT_IN_CORPUS-incorrect` — 3×
- `reponse-insuffisante` — 2×
- `question-conceptuelle-mal-traitee` — 2×
- `definition-FAO-absente` — 1×
- `structure-axes-manquante` — 1×
- `mauvaise-definition-citee-en-premier` — 1×
- `FAO-2005-absente` — 1×
- `definition-UNFCCC-non-trouvee` — 1×

---

## Pipeline — What Changed in v1

**Baseline pipeline (pre-improvements)**

### Known issues / remaining problems

- UNFCCC retrieval fails — SPARQL CONTAINS filter hits Ethiopia instead of UN FCCC
- Conceptual questions (land use/cover) return NOT_IN_CORPUS — no intent for category synthesis
- EUDR questions answered with EU 2010/2013 data — EUDR not in corpus but not flagged
- Reranking uses bag-of-words overlap — international org rows deprioritised vs country rows
- TYPOLOGICAL_KEYWORDS too narrow — misses FAO FRA entries for 'regenerated' and 'plantation'

---

## Per-Question Results

### [1] Qu'est ce qu'une forêt ?

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définitions de forêt Il existe différentes définitions de forêt selon les juridictions et les années. Voici quelques exemples : - **A/R SSC A/R** : une forêt est un minimum de 0,05-1,0 hectare de terre avec un couvert de couronne d'arbres (ou niveau d'ensemencement équivalent) supérieur à 10-30 ...

**Expert note:** Partiellement correcte mais incomplete. FAO 2005 et FAO 1958 sont les references centrales pour cette question.

**Correction needed:** La reponse cite des seuils UNFCCC/A/R mais ne presente pas la definition canonique FAO 2005 (>0,5 ha, >5 m, >10% couvert) ni la definition FAO 1958. Les trois axes definitionnels (LandCover, LandUse, Ecologique) ne sont pas structures explicitement.

**Issues:** `definition-FAO-absente,structure-axes-manquante`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [2] Qu'est ce qu'une forêt au sens de la FAO ?

**Rating:** 2/5 ██░░░  ⚠️ `corrected`

**Answer preview:** ### Définition de forêt selon la FAO Il existe plusieurs définitions de forêt selon la FAO, qui varient en fonction de l'année et des critères utilisés. Voici quelques-unes des définitions trouvées : - **FAO (2002)** : Les arbres qui poussent en dehors de la forêt et n'appartiennent pas à la catégor...

**Expert note:** Erreur de contexte : le retriever a remonte une definition peripherique (arbres hors foret) plutot que la definition centrale FAO 2005.

**Correction needed:** La reponse cite FAO 2002 (arbres hors foret) comme premiere definition — ce n'est pas la definition principale. La reference est FAO 2005 : superficie >0,5 ha, hauteur >5 m, couvert >10%, excluant terres agricoles et urbaines.

**Issues:** `mauvaise-definition-citee-en-premier,FAO-2005-absente`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [3] Qu'est ce qu'une forêt au sens de l'UNFCCC ?

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** ### Définition de forêt selon l'UNFCCC La définition de forêt selon l'UNFCCC n'est pas directement disponible dans le contexte fourni. Cependant, nous pouvons trouver une référence à cette définition dans le contexte d'**Ethiopia Kafa Biosphere Reserve (2012)**.  - Catégorie : Administrative - Canop...

**Expert note:** Erreur critique de retrieval. Le corpus contient la definition UNFCCC mais le SPARQL n'a pas su la cibler.

**Correction needed:** La definition UNFCCC est dans le corpus (Marrakech 2001 : 0,05-1 ha, couvert 10-30%, hauteur 2-5 m, choix national dans ces plages). Le pipeline a remonte la definition de l'Ethiopie au lieu de la definition UNFCCC directe.

**Issues:** `echec-retrieval,definition-UNFCCC-non-trouvee,substitution-par-pays-tiers`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [4] Est ce qu'une plantation forestière est une forêt au sens de l'UNFCCC ?

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** ### Définition de forêt selon l'UNFCCC La définition de forêt selon l'UNFCCC n'est pas directement disponible dans le contexte fourni. Cependant, nous pouvons utiliser les informations fournies pour **Ethiopia Kafa Biosphere Reserve (2012)**, qui mentionne que la définition de forêt du gouvernement ...

**Expert note:** Erreur critique. Le corpus contient la definition Kyoto Forest. Le retriever a echoue a la localiser.

**Correction needed:** Sous le Protocole de Kyoto/UNFCCC, les plantations etablies apres le 1er janvier 1990 sur terres non boisees sont explicitement incluses (Kyoto Forest). Le pipeline a cite l'Ethiopie hors contexte.

**Issues:** `echec-retrieval,reponse-hors-sujet`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [5] Est ce qu'une plantation forestière est une forêt au sens de l'EUDR ?

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** ### Réponse **Oui**, une plantation forestière peut être considérée comme une forêt au sens de l'**EU (2010)**, car elle est incluse dans la définition de « Continuously forested areas » avec un seuil de couverture de canopy de **30%** et une hauteur minimale de **5 m**.  - La définition de l'**EU (...

**Expert note:** Reponse incorrecte — le pipeline a confondu EU 2010 avec EUDR.

**Correction needed:** L'EUDR (Reglement UE 2023/1115) n'est pas dans le corpus. La reponse affirme a tort que la plantation est une foret au sens de EU 2010. Il fallait indiquer que l'EUDR est absent du corpus.

**Issues:** `hallucination,EUDR-absent-du-corpus,confusion-EU-2010-vs-EUDR`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [6] Qu'est ce qu'une forêt au sens de l'EUDR ?

**Rating:** 2/5 ██░░░  ⚠️ `corrected`

**Answer preview:** ### EU (2013) La définition d'une forêt au sens de l'EUDR (EU) en **2013** est : - Catégorie : LandUse - Seuil de couverture de la canopée : non spécifié - Hauteur : non spécifié - Superficie : non spécifié - Texte : ‘Forest’ means an area of land defined by the minimum values for area size, tree cr...

**Expert note:** Partiellement honnete (cite EU 2013) mais n'identifie pas que l'EUDR specifiquement est absent.

**Correction needed:** L'EUDR n'est pas dans le corpus. La reponse cite EU 2013 sans valeurs de seuil. La bonne reponse : le corpus ne contient pas la definition EUDR. Les definitions EU disponibles (JRC, EEA, Copernicus) s'alignent sur la FAO mais ne peuvent pas etre attribuees a l'EUDR.

**Issues:** `EUDR-absent-du-corpus,reponse-sans-seuils,confusion-EU-2013-vs-EUDR`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [7] Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC en Albanie

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Définition de la forêt en Albanie (2007) La définition de la forêt en Albanie, s'adossant à la définition de l'UNFCCC, est la suivante : - Catégorie : LandCover - Canopy : 30% - Height : 3 m - Area : 0.1 ha - Texte : Une zone avec une couverture de couronne d'arbre minimale de 30%, une superfici...

**Expert note:** Correct : Albanie 2007 KP — couvert 30%, hauteur 3 m, superficie 0,1 ha. Bien scope a la soumission nationale KP.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [8] Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Ghana

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt au Ghana (2006) selon l'UNFCCC Il existe deux définitions de la forêt au Ghana en 2006 : | Catégorie | Canopy | Hauteur | Superficie | Texte | | --- | --- | --- | --- | --- | | LandCover | 15% | 5 m | 0.1 ha | Canopy = 15%; Superficie = 0.1 ha; Hauteur des arbres = 5 m | |...

**Expert note:** Couvert et superficie corrects. La hauteur de 5 m est probablement une erreur dans le corpus ou de retrieval.

**Correction needed:** La hauteur pour le Ghana KP 2006 est de 2 m dans la soumission officielle. Le corpus montre 5 m mais la valeur KP Ghana confirmee est 2 m. Couvert 15% et superficie 0,1 ha sont corrects.

**Issues:** `valeur-hauteur-incorrecte`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [9] Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Brésil

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Brésil La définition de la forêt au Brésil, s'adossant à la définition de l'UNFCCC, est la suivante : - Catégorie : LandCover - Canopy : 30% - Hauteur : 5 m - Superficie : 1 ha - Texte : (Brésil 2006 KP) Couverture minimale de la canopée (%) = 30 Hauteur minimale des arbres (m) = 5 Superficie mi...

**Expert note:** Correct : Bresil KP 2006 — couvert 30%, hauteur 5 m, superficie 1 ha. Valeurs maximales dans les plages UNFCCC.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [10] Donne moi une définition structurelle de la forêt

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition structurelle de la forêt Une définition structurelle de la forêt peut varier en fonction de la juridiction et de l'année. Cependant, voici quelques éléments clés qui sont souvent utilisés pour définir une forêt : - **Seuil de couverture du couvert forestier** : cela fait référence au ...

**Expert note:** Demarche correcte mais le pipeline aurait du preciser que 'definition structurelle' est une interpretation des criteres LandCover.

**Correction needed:** Le corpus ne contient pas de definition explicitement etiquetee 'structurelle'. La reponse s'appuie sur des seuils LandCover ce qui est correct comme approximation, mais cela doit etre signale comme une interpretation, pas une definition directe.

**Issues:** `label-structurel-absent-du-corpus,approximation-non-signalee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [11] Donne moi une définition systémique de la forêt

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition systémique de la forêt Il existe différentes définitions de la forêt selon les juridictions et les années. Voici quelques exemples : - **ADB (1997)** : Un écosystème avec un minimum de 10 pour cent de couverture de couronne d'arbres et/ou de bambous, généralement associé à une flore e...

**Expert note:** ADB 1997 est une definition de couverture, pas systemique. AFF 2011 est la reference correcte.

**Correction needed:** La meilleure reference systemique du corpus est AFF 2011 : complexe dynamique de communautes de plantes, animaux et micro-organismes et de l'environnement non vivant agissant comme une unite fonctionnelle. FAO 1958 est aussi pertinente. ADB 1997 est trop axee LandCover.

**Issues:** `AFF-2011-non-citee,FAO-1958-absente,mauvaise-reference-principale`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [12] Donne moi une définition de la forêt primaire

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt primaire Il n'y a pas de définition explicite de la forêt primaire dans le contexte fourni. Cependant, certaines définitions de forêt peuvent être liées à la notion de forêt primaire.  - **Belarus (2002)** : La définition de la forêt inclut la notion de "virgin, natural fo...

**Expert note:** Honnete sur l'absence de definition explicite, mais la reference FAO FRA devait etre citee.

**Correction needed:** Le corpus contient via FAO FRA 2005/2010 la notion de foret primaire : foret naturellement regeneree d'especes natives sans activite humaine clairement visible et a processus ecologiques non perturbes. Le pipeline a reconnu l'absence de definition explicite mais aurait du citer cette reference.

**Issues:** `reference-FAO-FRA-manquante`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [13] Donne moi une définition de la forêt naturellement régénérée

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Erreur critique de retrieval. La definition existe dans le corpus (FAO FRA) mais n'a pas ete trouvee.

**Correction needed:** FAO FRA 2005/2010 definit la foret naturellement regeneree : foret a predominance d'especes natives se regenerant naturellement, sans plantation humaine, incluant les forets secondaires. Cette information est dans le corpus.

**Issues:** `echec-retrieval,NOT_IN_CORPUS-incorrect`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [14] Donne moi une définition de la plantation forestière

**Rating:** 2/5 ██░░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la plantation forestière Il n'y a pas de définition spécifique de la plantation forestière dans le contexte fourni. Cependant, certaines définitions de forêt mentionnent les plantations forestières : - **Australie (2003)** : inclut les plantations dans la définition de la forêt. - ...

**Expert note:** La reponse cite des pays mentionnant les plantations mais ne donne pas la definition centrale FAO/KP.

**Correction needed:** Le corpus contient via FAO et KP une definition de la plantation : foret etablie par plantation ou ensemencement, gestion intensive, souvent monoculture. Kyoto Forest (plantation post-1990 sur terres non boisees) est une sous-categorie. Ces definitions devaient etre citees directement.

**Issues:** `definition-FAO-plantation-absente,Kyoto-Forest-non-citee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [15] Donne moi une définition d'une agroforêt

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition d'une agroforêt Une agroforêt est définie comme un **LandUse** qui combine la production de bois et de produits non ligneux, gérée de manière plus ou moins intensive par de petits propriétaires. - Catégorie : LandUse - Canopée : non spécifiée - Hauteur : non spécifiée - Superficie : n...

**Expert note:** Correct : le corpus contient une entree Agroforest (LandUse) — foret combinant production de bois et produits non ligneux, geree par petits proprietaires. Definition fidele au corpus.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [16] Donne moi une définition de la forêt urbaine

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt urbaine Il n'y a pas de définition spécifique de la forêt urbaine dans le contexte fourni. Cependant, certaines définitions mentionnent les arbres en milieu urbain : - **Aruba (1998)** : inclut les arbres en milieu urbain dans sa définition de la forêt. - **Canada Calgary*...

**Expert note:** Honnete sur l'absence de definition specifique, mais manque le point cle : la FAO exclut explicitement l'usage urbain.

**Correction needed:** Le corpus ne contient pas de definition formelle de la foret urbaine. La reponse aurait du preciser que la FAO exclut les terres a usage urbain de ses statistiques forestieres. La mention d'Aruba et Canada est anecdotique sans valeurs definitoires.

**Issues:** `exclusion-FAO-urbaine-non-mentionnee,reponse-anecdotique`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [17] Quelles sont les principales différences entre forêt primaire et forêt naturellement régénérée ?

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** ### Réponse Il n'y a pas suffisamment d'informations dans le contexte pour répondre à cette question. Les définitions fournies ne spécifient pas les caractéristiques des forêts primaires et des forêts naturellement régénérées, telles que la catégorie, le pourcentage de couverture du couvert forestie...

**Expert note:** Le retriever a remonte des definitions vides. FAO FRA devait etre ciblee.

**Correction needed:** FAO FRA distingue : foret primaire = especes natives, aucune activite humaine visible, processus non perturbes. Foret naturellement regeneree = inclut les forets secondaires en recuperation apres perturbation. La difference principale est le degre d'intervention humaine passee.

**Issues:** `echec-retrieval,reponse-insuffisante`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [18] Quelles sont les principales différences entre plantation forestière et forêt naturellement régénérée ?

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** ### Réponse Il n'y a pas suffisamment d'informations dans le contexte pour répondre à cette question. Les données fournies ne contiennent aucune information spécifique sur les définitions de plantation forestière et de forêt naturellement régénérée, car toutes les catégories sont indiquées comme « n...

**Expert note:** Meme probleme que Q17. Le retriever n'a pas cible les bonnes definitions.

**Correction needed:** FAO distingue : plantation = plantee/ensemencee, gestion intensive, souvent monoculture. Foret naturellement regeneree = especes natives, sans plantation, recuperation naturelle. Ce sont deux sous-categories officielles distinctes dans la classification FAO.

**Issues:** `echec-retrieval,reponse-insuffisante`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [19] En quoi l'usage du sol (land use) peut être d'intérêt quand on cherche à caractériser la forêt ?

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Question conceptuelle qui necessite une synthese des definitions LandUse du corpus. Le retriever n'a pas su gerer ce type de question.

**Correction needed:** Le corpus contient de nombreuses definitions LandUse. L'interet du LandUse est qu'il capture l'intention de gestion plutot que l'etat physique — pertinent pour la comptabilite carbone et les politiques. Le pipeline aurait du exploiter ces definitions LandUse presentes dans le corpus.

**Issues:** `echec-retrieval,NOT_IN_CORPUS-incorrect,question-conceptuelle-mal-traitee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [20] En quoi la couverture du sol (land cover) peut être d'intérêt quand on cherche à caractériser la forêt ?

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Meme probleme que Q19. Questions conceptuelles non gerees par le retriever.

**Correction needed:** Le corpus contient de nombreuses definitions LandCover (FAO 2005 : >0,5 ha, >5 m, >10% couvert). L'interet du LandCover est qu'il decrit l'etat physique reel, compatible avec la teledetection et le monitoring global.

**Issues:** `echec-retrieval,NOT_IN_CORPUS-incorrect,question-conceptuelle-mal-traitee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [21] Est ce que la FAO considère la forêt urbaine comme étant une forêt ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Réponse La **FAO** considère-**t-**elle la forêt urbaine comme étant une forêt ? **Non** La définition de la forêt par la **FAO** exclut les terres principalement sous usage urbain.  ### Contexte Les définitions de la **FAO** pour les années **2001**, **2004**, **2005**, **2006** et **2010** exc...

**Expert note:** Excellent. La FAO exclut explicitement les terres a usage urbain (FAO 2001, 2004, 2005, 2006, 2010). Reponse directe, correcte et bien sourcee.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [22] Est ce que l'UNFCCC considère la forêt urbaine comme étant une forêt ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Réponse L'information fournie ne permet pas de déterminer avec certitude si l'UNFCCC considère la forêt urbaine comme une forêt.  - Les définitions de forêt fournies par l'UNFCCC se concentrent sur des critères tels que la hauteur des arbres, le couvert forestier et la superficie, mais ne mentio...

**Expert note:** Bonne reponse : l'UNFCCC ne mentionne pas explicitement l'exclusion urbaine. Le pipeline a correctement indique l'incertitude et explique que les criteres UNFCCC ne mentionnent pas l'usage urbain. Honnetete epistemique appropriee.

**SPARQL used:** `PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
`

---

### [23] Qu'est ce qu'un arbre ?

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définitions d'arbre Il existe plusieurs définitions d'arbre selon les juridictions et les années. Voici quelques-unes d'entre elles :  | Pays | Année | Catégorie | Canopy | Hauteur | Superficie | Texte | | --- | --- | --- | --- | --- | --- | --- | | Antigua et Barbuda | 1941 | Ecologique | - | -...

**Expert note:** Le tableau de definitions nationales est utile mais la definition FAO devait etre identifiee comme reference principale.

**Correction needed:** La definition de reference FAO : plante ligneuse perenne atteignant generalement >=5 m de hauteur a maturite in situ. Cette definition est centrale car le seuil de 5 m est utilise dans FAO 2005. Le pipeline a fourni des definitions nationales multiples sans identifier la reference FAO centrale.

**Issues:** `definition-FAO-arbre-non-mise-en-avant,dispersion-sans-synthese`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [24] Est ce que je peux définir une forêt à partir des services écosystémiques qu'elle est en capacité de fournir ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition d'une forêt à partir des services écosystémiques Il n'est pas possible de définir une forêt uniquement à partir des services écosystémiques qu'elle est en capacité de fournir, car les définitions fournies se basent sur des caractéristiques physiques et écologiques.  - Les définitions ...

**Expert note:** Bonne reponse : le pipeline a correctement indique que les definitions du corpus reposent sur des criteres physiques et ecologiques, pas sur les services. Les services sont des consequences de l'existence de la foret, non des criteres definitoires.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [25] Est ce que je peux définir une forêt à partir de ses fonctions écologiques ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Définition d'une forêt à partir de ses fonctions écologiques Oui, **AFF (2011)** définit une forêt comme un "écosystème forestier dynamique complexe de communautés de plantes, d'animaux et de micro-organismes et de l'environnement non vivant agissant comme une unité fonctionnelle dans l'environn...

**Expert note:** Excellent. AFF 2011 correctement citee : complexe dynamique de communautes de plantes, animaux et micro-organismes agissant comme une unite fonctionnelle. C'est la definition fonctionnelle/ecologique de reference dans le corpus.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [26] L'EUDR reprend essentiellement les définitions (forêt en particulier) de la FAO

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** ### Définition de forêt L'EUDR reprend essentiellement les définitions (forêt en particulier) de la **FAO**. Cependant, le contexte fourni ne contient pas d'information spécifique sur la définition de forêt utilisée par l'EUDR.  - Les définitions de forêt fournies par la **FAO** varient selon les an...

**Expert note:** Question piege. Toute affirmation ou negation confiante est non fondee. Le pipeline a partiellement succombe au piege.

**Correction needed:** L'EUDR n'est pas dans le corpus. Le pipeline a affirme dans son titre que l'EUDR reprend les definitions FAO puis a immediatement admis ne pas avoir l'information. Reponse auto-contradictoire. La bonne reponse : cette affirmation ne peut pas etre verifiee depuis le corpus.

**Issues:** `auto-contradiction,hallucination-titre,EUDR-absent-du-corpus`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---
