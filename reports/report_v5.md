# ForestGraphRAG — Evaluation Report v5
Generated: 2026-05-20 16:29 UTC  |  Questions: 26  |  DB: graph_rag_eval.db

---

## Summary

| Metric | Value |
|--------|-------|
| Average expert rating | **3.73/5** |
| Validated (5 or 4) | 16 |
| Corrected (3 or 2) | 9 |
| Rejected (1) | 1 |
| vs previous version | ▲ +3.73 |

### Rating Distribution

```
  5/5 [███████                   ] 7
  4/5 [█████████                 ] 9
  3/5 [███████                   ] 7
  2/5 [██                        ] 2
  1/5 [█                         ] 1
```

### Top Issues

- `synthese-incomplete` — 3×
- `FAO-FRA-absente-du-KG` — 3×
- `regression` — 1×
- `NOT_IN_CORPUS-incorrect` — 1×
- `intent-failure` — 1×
- `reponse-oui-non-absente` — 1×
- `valeur-hauteur-incorrecte-dans-corpus` — 1×
- `label-structurel-absent-non-signale` — 1×
- `reponse-approximative` — 1×
- `definition-plantation-indirecte` — 1×

---

## Pipeline — What Changed in v5

**Pipeline improvements — FAO year ordering, tree concept, dual-typological, Kyoto injection, AFF systemic, prompt grounding**

### Changes made

- (a) retriever.py — FAO year-preference in reranking: preferred_years {2005,2006,2010,2013,2015} get +10 score. FAO 2005 now consistently first.
- (b) retriever.py + planner.py — Tree concept direct query: TREE_CONCEPT_SPARQL uses :defines :Tree. keyword='tree' routes to _run_tree_concept(). Q23 now returns FAO canonical tree definition.
- (c) retriever.py + planner.py — Dual-typological for comparatives: COMPARATIVE_PAIRS runs two typological queries and merges results. Few-shot examples added for primary_vs_regenerated and plantation_vs_regenerated.
- (d) retriever.py + tools.py + steps.py — Kyoto Forest injection: KYOTO_FOREST_SPARQL targets UN FCCC/FAO entries with planted stand/plantation/afforestation. Injected into boolean_reasoning when question contains plantation+unfccc. Question now propagated through steps→tools→retrieve.
- (e) retriever.py — AFF systemic lookup: AFF_SYSTEMIC_SPARQL targets AFF + functional unit/dynamic complex/ecosystem. systemic intent now tries this first. Q11 now cites AFF 2011.
- (f) prompts.py — Stronger corpus grounding: 'Use ONLY the provided context, never fill gaps from general knowledge' and 'Never synthesise a definition not explicitly stated in the context'.

**Files modified:** `workflow/planner.py`, `workflow/retriever.py`, `workflow/tools.py`, `workflow/steps.py`, `workflow/prompts.py`

### Known issues / remaining problems

- Q1 regression: generic question 'Qu est ce qu une foret' now returns NOT_IN_CORPUS — planner emits wrong intent without explicit org keyword.
- FAO FRA not in KG: 'foret naturellement regeneree' (Q13), 'foret primaire' (Q12), comparatives (Q17) remain limited — data gap.
- Plantation vs regenerated (Q18) slight regression vs v2 — dual-typological context present but LLM synthesis weaker.
- UNFCCC plantation (Q4) Kyoto context now retrieved but LLM still not giving clear yes/no conclusion.

---

## Per-Question Results

### [1] Qu'est ce qu'une forêt ?

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Regression par rapport a v2 (rating 3). Le nouveau planner est trop strict sur les questions generiques sans mot-cle org.

**Correction needed:** Regression vs v2 : retourne NOT_IN_CORPUS. Le planner a probablement emis un intent incorrect pour une question generique. FAO 2005 est la reference principale et doit etre retournee.

**Issues:** `regression,NOT_IN_CORPUS-incorrect,intent-failure`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [2] Qu'est ce qu'une forêt au sens de la FAO ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition de la forêt selon la FAO La définition de la forêt selon la FAO varie légèrement selon les années et les catégories. Voici les informations disponibles :  - **UN FAO (2005)** : La forêt est définie comme un bois ou une forêt, naturelle ou plantée, qui a ou aura de la valeur pour le bo...

**Expert note:** Amelioration vs v2 (rating 3). FAO 2005 cite en premier grace au reranking par annee. Tableau structure. Bon.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [3] Qu'est ce qu'une forêt au sens de l'UNFCCC ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition de forêt selon l'UNFCCC Il existe plusieurs définitions de forêt au sens de l'UNFCCC, qui varient en fonction de la catégorie et des critères spécifiques. Voici les informations disponibles :  | Catégorie | Canopy | Hauteur | Superficie | Texte | | --- | --- | --- | --- | --- | | Land...

**Expert note:** Stable vs v2. Definitions UN FCCC correctement retournees avec tableau.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [4] Est ce qu'une plantation forestière est une forêt au sens de l'UNFCCC ?

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Réponse La question nécessite une analyse des définitions de forêt fournies par les différentes organisations et pays.   ### Définitions de forêt - **UN FAO** : La définition de l'UN FAO inclut les terres sous couvert forestier naturel ou planté, qu'elles soient productives ou non. - **UNFCCC** ...

**Expert note:** Amelioration vs v2 (rating 3) : le contexte Kyoto est maintenant present. Le probleme est dans la generation de reponse, pas le retrieval.

**Correction needed:** La reponse cite UN FAO et IPCC Kyoto Protocol mais ne conclut pas clairement oui/non. La Kyoto Forest injection fonctionne (IPCC Kyoto Protocol cite) mais le LLM n'en tire pas une reponse directe. Doit dire : Oui, les plantations etablies post-1990 sur terres non boisees sont explicitement incluses.

**Issues:** `reponse-oui-non-absente,synthese-incomplete`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [5] Est ce qu'une plantation forestière est une forêt au sens de l'EUDR ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Stable. NOT_IN_CORPUS correct avec disclaimer EUDR.

---

### [6] Qu'est ce qu'une forêt au sens de l'EUDR ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Stable. NOT_IN_CORPUS correct.

---

### [7] Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC en Albanie

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Définition de la forêt en Albanie selon l'UNFCCC La définition de la forêt en Albanie qui s'adossa à la définition de l'UNFCCC est disponible pour les années **2006** et **2007**. - Catégorie : LandCover - Seuil de couverture du couvert forestier : 30% - Hauteur minimale des arbres : 3 m - Super...

**Expert note:** Stable. Albanie 2006/2007 KP : 30%, 3m, 0.1ha. Correct.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [8] Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Ghana

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt au Ghana selon l'UNFCCC La définition de la forêt au Ghana qui s'adossant à la définition de l'UNFCCC est disponible pour les années **2006** et **2009**.   Voici les détails : - **Ghana (2006)** :    - Catégorie : LandCover   - Canopy : 15%   - Height : 5 m   - Area : 0.1...

**Expert note:** Stable vs v2. Erreur de donnee persistante.

**Correction needed:** Ghana 2006 et 2009 cites. Hauteur toujours 5m dans le corpus (valeur attendue 2m). Erreur dans les donnees sources, pas dans le pipeline.

**Issues:** `valeur-hauteur-incorrecte-dans-corpus`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [9] Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Brésil

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Définition de la forêt au Brésil La définition de la forêt au **Brésil** varie selon les années et les sources. Voici les informations disponibles : | Année | Catégorie | Canopy | Hauteur | Superficie | Texte | | --- | --- | --- | --- | --- | --- | | 2006 | LandCover | 30% | 5 m | 1 ha | (Brazil...

**Expert note:** Stable. Bresil KP : 30%, 5m, 1ha. Correct.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [10] Donne moi une définition structurelle de la forêt

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition structurelle de la forêt Il existe différentes définitions de la forêt selon les juridictions et les années. Voici quelques exemples :  | Pays | Année | Catégorie | Canopy | Hauteur | Superficie | | --- | --- | --- | --- | --- | --- | | A/R SSC A/R | - | LandUse | non spécifié | non s...

**Expert note:** Stable vs v2.

**Correction needed:** Tableau de seuils LandCover fourni — pertinent. Mais ne signale toujours pas que 'structurelle' est une interpretation et non un type explicite du corpus.

**Issues:** `label-structurel-absent-non-signale`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [11] Donne moi une définition systémique de la forêt

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition systémique de la forêt Il existe différentes définitions de la forêt selon les pays et les organisations. Voici quelques exemples : - **ADB (1997)** : Un écosystème avec un minimum de 10 pour cent de couvert forestier d'arbres et/ou de bambous, généralement associé à une flore et une ...

**Expert note:** Amelioration vs v2 (rating 3). AFF 2011 maintenant cite grace a AFF_SYSTEMIC_SPARQL. ADB 1997 aussi present. Reponse plus riche et correcte.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [12] Donne moi une définition de la forêt primaire

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt primaire Il n'y a pas de définition explicite de la forêt primaire dans le contexte fourni. Cependant, certaines définitions de forêt mentionnent des caractéristiques qui pourraient être liées à la forêt primaire.  - La définition de la **Belarus (2002)** mentionne "virgin...

**Expert note:** Stable vs v2. Limitation du corpus.

**Correction needed:** Honnete sur l'absence de definition explicite. Belarus 'virgin forest' cite comme approximation. FAO FRA primaire toujours absente du KG.

**Issues:** `FAO-FRA-absente-du-KG`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [13] Donne moi une définition de la forêt naturellement régénérée

**Rating:** 2/5 ██░░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt naturellement régénérée Il n'y a pas de définition explicite de la forêt naturellement régénérée dans le contexte fourni. Cependant, certaines définitions de forêt mentionnent la régénération ou la re-growth de la forêt.  - **Gambia** : Une zone terrestre avec au moins 10%...

**Expert note:** Amelioration partielle vs v2 (rating 1). Le pipeline tente une synthese mais sans la source directe.

**Correction needed:** Amelioration vs v1/v2 (etait NOT_IN_CORPUS rejete). Le pipeline tente maintenant une reponse en citant 're-growth' et des definitions proches. Mais FAO FRA absente du KG — la reponse reste incomplete et approximative.

**Issues:** `FAO-FRA-absente-du-KG,reponse-approximative`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [14] Donne moi une définition de la plantation forestière

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la plantation forestière Il n'y a pas de définition spécifique de la plantation forestière dans le contexte fourni. Cependant, certaines définitions de forêt incluent les plantations forestières : - **UN FAO (2001)** : Les forêts incluent les forêts naturelles et les plantations fo...

**Expert note:** Stable vs v2.

**Correction needed:** UN FAO 2001 cite (forêts incluant plantations). Kyoto injection presente. Mais pas de definition directe FAO/KP de la plantation comme type distinct.

**Issues:** `definition-plantation-indirecte`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [15] Donne moi une définition d'une agroforêt

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition d'une agroforêt Une agroforêt est définie comme un **forest qui est géré plus ou moins intensivement par de petits propriétaires produisant du bois et des produits non ligneux**. Cette définition est issue de la référence **Zomer RJ, Trabucco A, Coe R et Place F. 2009**.  - Catégorie ...

**Expert note:** Stable. Entree Agroforest correctement citee avec reference Zomer RJ.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [16] Donne moi une définition de la forêt urbaine

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt urbaine Il n'y a pas de définition explicite de la forêt urbaine dans le contexte fourni. Cependant, certaines définitions mentionnent les arbres en milieu urbain : - **Aruba (1998)** : inclut les arbres en milieu urbain dans sa définition de la forêt. - **Canada Calgary**...

**Expert note:** Stable vs v2. Limitation du corpus.

**Correction needed:** Toujours pas de definition specifique. FAO exclusion urbaine non mentionnee explicitement.

**Issues:** `exclusion-FAO-urbaine-non-mentionnee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [17] Quelles sont les principales différences entre forêt primaire et forêt naturellement régénérée ?

**Rating:** 2/5 ██░░░  ⚠️ `corrected`

**Answer preview:** ### Définitions de forêt primaire et forêt naturellement régénérée Les principales différences entre forêt primaire et forêt naturellement régénérée ne sont pas explicitement définies dans le contexte fourni. Cependant, certaines définitions de forêt peuvent être comparées pour identifier les critèr...

**Expert note:** Stable vs v2. Dual-typological fonctionne mais les donnees FAO FRA manquent dans le KG.

**Correction needed:** La reponse tente une synthese mais conclut que les differences ne sont pas explicitement definies. Manque FAO FRA. Amelioration vs v1 (rejete) mais insuffisant.

**Issues:** `FAO-FRA-absente-du-KG,synthese-incomplete`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [18] Quelles sont les principales différences entre plantation forestière et forêt naturellement régénérée ?

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Principales différences entre plantation forestière et forêt naturellement régénérée Les principales différences entre plantation forestière et forêt naturellement régénérée ne sont pas explicitement définies dans le contexte fourni. Cependant, certaines informations peuvent être déduites des dé...

**Expert note:** Legere regression vs v2 (rating 4). Le contexte dual-typologique est present mais la reponse ne l'exploite pas.

**Correction needed:** La reponse dit que les differences ne sont pas explicitement definies alors que v2 avait fourni une synthese plus complete (rating 4). Regression legere. Le dual-typological retourne des resultats mais le LLM ne les synthetise pas bien.

**Issues:** `regression-legere-vs-v2,synthese-incomplete`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [19] En quoi l'usage du sol (land use) peut être d'intérêt quand on cherche à caractériser la forêt ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Intérêt de l'usage du sol pour caractériser la forêt L'usage du sol (land use) peut être d'intérêt pour caractériser la forêt car il permet de définir les zones qui sont principalement utilisées pour la production forestière, la conservation de la biodiversité ou d'autres activités liées à la fo...

**Expert note:** Stable vs v2. Intent conceptual fonctionne bien.

---

### [20] En quoi la couverture du sol (land cover) peut être d'intérêt quand on cherche à caractériser la forêt ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Intérêt de la couverture du sol pour caractériser la forêt La couverture du sol (land cover) est un aspect crucial pour caractériser la forêt, car elle permet de définir et de distinguer les différentes zones forestières en fonction de leur état et de leur usage.   - Elle aide à identifier les z...

**Expert note:** Stable vs v2. Intent conceptual fonctionne bien.

---

### [21] Est ce que la FAO considère la forêt urbaine comme étant une forêt ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Réponse Non, selon les définitions fournies par la **FAO (2005)**, **FAO (2006)**, **FAO (2010)**, **FAO (2013)** et **FAO RAP (2010)**, la forêt urbaine n'est pas considérée comme une forêt car ces définitions excluent spécifiquement les terres principalement sous usage urbain.  - Les définitio...

**Expert note:** Excellent. FAO 2005/2006/2010/2013/RAP 2010 cites. Reponse directe et correcte.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [22] Est ce que l'UNFCCC considère la forêt urbaine comme étant une forêt ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Réponse L'information disponible ne permet pas de déterminer si l'UNFCCC considère la forêt urbaine comme étant une forêt, car les définitions fournies ne mentionnent pas spécifiquement les forêts urbaines.  - Les définitions de l'UNFCCC fournies se concentrent sur les caractéristiques générales...

**Expert note:** Stable. Incertitude correctement signalee.

**SPARQL used:** `PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
`

---

### [23] Qu'est ce qu'un arbre ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition d'un arbre Il est difficile de donner une définition unique et précise d'un arbre en fonction des données fournies, car les définitions varient selon les juridictions et les années. Cependant, voici quelques éléments communs et des différences notables :  - La plupart des définitions ...

**Expert note:** Amelioration vs v2 (rating 3). Intent typological/tree fonctionne. Definitions :Tree directement citees. FAO 2000/2005 (plante ligneuse perenne) maintenant dans le contexte.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [24] Est ce que je peux définir une forêt à partir des services écosystémiques qu'elle est en capacité de fournir ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition d'une forêt à partir des services écosystémiques Il n'est pas possible de définir une forêt uniquement à partir des services écosystémiques qu'elle est en capacité de fournir, car les définitions de forêt fournies dans le contexte se basent sur des caractéristiques physiques et biolog...

**Expert note:** Stable. Reponse correcte : services = consequences, non criteres.

---

### [25] Est ce que je peux définir une forêt à partir de ses fonctions écologiques ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Définition d'une forêt à partir de ses fonctions écologiques Oui, certaines définitions de forêt sont basées sur les fonctions écologiques.  - **AFF (2011)** : Une forêt est définie comme un écosystème dynamique complexe de plantes, d'animaux et de micro-organismes et de l'environnement non viva...

**Expert note:** Excellent. AFF 2011 correctement citee.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [26] L'EUDR reprend essentiellement les définitions (forêt en particulier) de la FAO

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Stable. NOT_IN_CORPUS avec disclaimer clair. Question piege correctement geree.

---
