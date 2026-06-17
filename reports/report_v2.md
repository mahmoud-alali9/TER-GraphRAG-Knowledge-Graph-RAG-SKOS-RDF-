# ForestGraphRAG — Evaluation Report v2
Generated: 2026-05-20 14:33 UTC  |  Questions: 26  |  DB: graph_rag_eval.db

---

## Summary

| Metric | Value |
|--------|-------|
| Average expert rating | **3.69/5** |
| Validated (5 or 4) | 14 |
| Corrected (3 or 2) | 11 |
| Rejected (1) | 1 |
| vs previous version | ▲ +0.99 |

### Rating Distribution

```
  5/5 [███████                   ] 7
  4/5 [███████                   ] 7
  3/5 [██████████                ] 10
  2/5 [█                         ] 1
  1/5 [█                         ] 1
```

### Top Issues

- `FAO-2005-non-prioritisee` — 2×
- `Kyoto-Forest-non-citee` — 2×
- `ordre-des-references-incorrect` — 1×
- `FAO-1998-citee-en-premier` — 1×
- `reponse-oui-non-absente` — 1×
- `valeur-hauteur-incorrecte-dans-corpus` — 1×
- `label-structurel-absent-non-signale` — 1×
- `AFF-2011-non-priorisee` — 1×
- `FAO-1958-absente` — 1×
- `FAO-FRA-primaire-non-citee` — 1×

---

## Pipeline — What Changed in v2

**Pipeline improvements — jurisdiction mapping, conceptual intent, reranking, typological keywords**

### Changes made

- (a) planner.py — Added JURISDICTION_MAP with exact KG labels (UN FCCC, UN FAO, IPCC Kyoto Protocol, EU, UN EP…). SPARQL now uses IN() with exact labels instead of CONTAINS() for international orgs. Eliminated false positives (Ethiopia matching FCCC text).
- (b) planner.py + retriever.py — Added 'conceptual' intent for questions about the role/interest of a category (land use, land cover, ecological functions). Planner emits {intent: conceptual, keyword: LandUse/LandCover}. Retriever runs CONCEPTUAL_SPARQL filtering by :hasCategory label. Fixes NOT_IN_CORPUS on Q19/Q20.
- (c) retriever.py — Replaced bag-of-words _rerank_by_relevance() with jurisdiction-priority scoring. If the question mentions 'fao', 'unfccc', 'kyoto' etc., rows from matching KG labels score +100. Eliminates Ethiopia/random-country substitution on org-level questions.
- (d) retriever.py — Expanded TYPOLOGICAL_KEYWORDS for 'regenerated' (added: natural regrowth, naturally grown, spontaneous regenerat) and 'plantation' (added: reforestation, afforestation, monoculture, planted trees). Catches FAO FRA entries previously missed.
- (e) planner.py — Added 'not_in_corpus' intent for EUDR and other absent regulations. tools.py updated to return a clear disclaimer including an EUDR-specific note.

**Files modified:** `workflow/planner.py`, `workflow/retriever.py`, `workflow/tools.py`

### Known issues / remaining problems

- Comparative questions (primary vs regenerated, plantation vs regenerated) still rely on typological retrieval which may not return both types in one query.
- FAO 2005 canonical definition may still be diluted by peripheral FAO entries (FAO 2002 trees-outside-forest).

---

## Per-Question Results

### [1] Qu'est ce qu'une forêt ?

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définitions de forêt Il existe différentes définitions de forêt selon les juridictions et les années. Voici quelques exemples : - **A/R SSC A/R** : une forêt est un minimum de 0,05-1,0 hectare de terre avec un couvert de couronne d'arbres (ou niveau d'ensemencement équivalent) supérieur à 10-30 ...

**Expert note:** Amelioration vs v1 : la reponse est plus riche. Mais FAO 2005 reste noyee parmi d'autres definitions.

**Correction needed:** La reponse cite A/R SSC A/R comme premier exemple — ce sont des seuils UNFCCC generiques, pas la definition canonique. FAO 2005 (>0,5 ha, >5 m, >10% couvert) doit etre citee en premier comme reference internationale principale.

**Issues:** `FAO-2005-non-prioritisee,ordre-des-references-incorrect`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [2] Qu'est ce qu'une forêt au sens de la FAO ?

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt selon la FAO La définition de la forêt selon la FAO varie légèrement selon les années et les catégories. Voici les informations disponibles : - **UN FAO (1998)** : Une plante pérenne ligneuse avec un tronc bien défini ou, dans le cas de taillis, avec plusieurs troncs, port...

**Expert note:** Amelioration partielle vs v1 : le retriever cible maintenant UN FAO mais ne trie pas par pertinence chronologique. FAO 2005 est la reference de reference.

**Correction needed:** La reponse cite UN FAO 1998 (plantes en dehors de la foret) comme premier resultat — meme erreur de contexte que v1. FAO 2005 (superficie >0,5 ha, hauteur >5 m, couvert >10%) est la reference principale et doit apparaitre en tete.

**Issues:** `FAO-1998-citee-en-premier,FAO-2005-non-prioritisee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [3] Qu'est ce qu'une forêt au sens de l'UNFCCC ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition de forêt selon l'UNFCCC Il existe plusieurs définitions de forêt au sens de l'UNFCCC, qui varient en fonction de la catégorie et de la période considérée. Voici les informations disponibles :  | Catégorie | Hauteur | Superficie | Texte | | --- | --- | --- | --- | | LandCover | - | - |...

**Expert note:** Nette amelioration vs v1 (etait rejete). Le pipeline retourne maintenant les definitions UN FCCC reelles avec categories et seuils. La definition Marrakech 2001 (plages nationales) devrait etre mise en avant mais la reponse est correcte.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [4] Est ce qu'une plantation forestière est une forêt au sens de l'UNFCCC ?

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de forêt selon l'UN FCCC (2001) - Catégorie : LandUse - Seuil de couverture du couvert forestier : non spécifié - Hauteur : non spécifié - Superficie minimale : 1 ha - Texte : « Forest » est une superficie minimale de terre de 0,05-1,0 hectare avec un couvert de couronne d'arbre (ou n...

**Expert note:** Amelioration vs v1 (etait rejete). Le retriever cible maintenant UN FCCC. Mais le raisonnement boolean sur les plantations est incomplet.

**Correction needed:** La reponse cite la definition UN FCCC 2001 (LandUse, 1 ha) mais ne repond pas explicitement a la question oui/non sur les plantations. La Kyoto Forest (plantation post-1990 sur terres non boisees) est la reponse directe et doit etre citee.

**Issues:** `Kyoto-Forest-non-citee,reponse-oui-non-absente`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [5] Est ce qu'une plantation forestière est une forêt au sens de l'EUDR ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Excellent. Pipeline retourne NOT_IN_CORPUS avec disclaimer EUDR explicite. Correction totale vs v1 (etait hallucination EU 2010).

---

### [6] Qu'est ce qu'une forêt au sens de l'EUDR ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Excellent. Pipeline retourne NOT_IN_CORPUS avec disclaimer EUDR explicite. Correction totale vs v1.

---

### [7] Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC en Albanie

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Définition de la forêt en Albanie (2007) La définition de la forêt en Albanie, s'adossant à la définition de l'UNFCCC, est la suivante : - Catégorie : LandCover - Canopy : 30% - Height : 3 m - Area : 0.1 ha - Texte : Une zone avec une couverture de couronne d'arbre minimale de 30%, une superfici...

**Expert note:** Correct : Albanie 2007 KP — couvert 30%, hauteur 3 m, superficie 0,1 ha. Identique a v1, toujours correct.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [8] Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Ghana

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt au Ghana (2006) selon l'UNFCCC Il existe deux définitions de la forêt au Ghana en 2006 : | Catégorie | Canopy | Hauteur | Superficie | Texte | | --- | --- | --- | --- | --- | | LandCover | 15% | 5 m | 0.1 ha | Canopy = 15% ; Superficie = 0.1 ha ; Hauteur des arbres = 5 m |...

**Expert note:** Meme probleme que v1. C'est une erreur dans les donnees du corpus, pas dans le pipeline.

**Correction needed:** La hauteur Ghana KP est de 2 m dans la soumission officielle. Le corpus montre 5 m — probablement une erreur dans les donnees sources. Couvert 15% et superficie 0,1 ha sont corrects.

**Issues:** `valeur-hauteur-incorrecte-dans-corpus`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [9] Donne moi la définition de la forêt s'adossant à la définition de l'UNFCCC au Brésil

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Brésil La définition de la forêt au Brésil s'adossant à la définition de l'UNFCCC est la suivante : - Catégorie : LandCover - Canopy : 30% - Hauteur : 5 m - Superficie : 1 ha - Texte : (Brésil 2006 KP) Couverture minimale de la canopée (%) = 30 Hauteur minimale des arbres (m) = 5 Superficie mini...

**Expert note:** Correct : Bresil KP 2006 — couvert 30%, hauteur 5 m, superficie 1 ha. Identique a v1, toujours correct.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [10] Donne moi une définition structurelle de la forêt

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition structurelle de la forêt Une définition structurelle de la forêt peut varier en fonction de la juridiction et de l'année. Cependant, voici quelques éléments clés qui peuvent être inclus dans une telle définition : - **Seuil de couverture du couvert forestier** : cela fait référence au...

**Expert note:** Amelioration vs v1 : contenu plus dense. Manque toujours le qualificatif 'approximation'.

**Correction needed:** Reponse plus riche qu'en v1 grace aux keywords elargis, mais ne signale toujours pas que 'structurelle' est une interpretation des criteres LandCover et non un type explicite dans le corpus.

**Issues:** `label-structurel-absent-non-signale`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [11] Donne moi une définition systémique de la forêt

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition systémique de la forêt Il est difficile de fournir une définition systémique unique de la forêt, car les définitions varient selon les juridictions et les années. Cependant, voici quelques éléments clés qui ressortent des définitions fournies : - Une forêt est souvent considérée comme...

**Expert note:** Meme probleme qu'en v1. Le reranking ameliore les questions org-level mais pas les questions typologiques.

**Correction needed:** Le pipeline dit qu'il est difficile de fournir une definition systemique unique — correct. Mais AFF 2011 (unite fonctionnelle) et FAO 1958 (influencant le climat et les regimes hydriques) sont les references systemiques directes du corpus et doivent etre citees en premier.

**Issues:** `AFF-2011-non-priorisee,FAO-1958-absente`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [12] Donne moi une définition de la forêt primaire

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt primaire Il n'y a pas de définition explicite de la forêt primaire dans le contexte fourni. Cependant, certaines définitions de forêt mentionnent des caractéristiques qui pourraient être liées à la forêt primaire : - **Belarus (2002)** : Mentionne "virgin, natural forest" ...

**Expert note:** Identique a v1. Les keywords 'primary' incluent maintenant 'intact forest' et 'climax' mais FAO FRA reste non retrouve.

**Correction needed:** La reponse admet l'absence de definition explicite — honnete. Mais Belarus 'virgin, natural forest' est cite comme approximation. FAO FRA definit explicitement la foret primaire (especes natives, aucune activite humaine visible, processus non perturbes).

**Issues:** `FAO-FRA-primaire-non-citee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [13] Donne moi une définition de la forêt naturellement régénérée

**Rating:** 1/5 █░░░░  ❌ `rejected`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Pas d'amelioration vs v1. Les nouveaux keywords (natural regrowth, spontaneous regenerat) n'ont pas suffi. Verifier le label exact dans le KG.

**Correction needed:** NOT_IN_CORPUS malgre l'ajout de nouveaux keywords. FAO FRA contient la definition. Le retriever TYPOLOGICAL ne trouve toujours pas cette entree. Probleme de donnees ou de label dans le KG.

**Issues:** `echec-retrieval-persistant,NOT_IN_CORPUS-incorrect`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [14] Donne moi une définition de la plantation forestière

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la plantation forestière Il n'y a pas de définition spécifique de la plantation forestière dans le contexte fourni. Cependant, certaines définitions de forêt incluent les plantations forestières : - **Australie (2003)** : inclut les plantations dans sa définition de forêt. - **Aust...

**Expert note:** Amelioration partielle vs v1. Plus de contexte mais reponse toujours indirecte.

**Correction needed:** La reponse cite des pays incluant les plantations mais pas la definition FAO/KP directe. Amelioration vs v1 grace aux keywords 'reforestation' et 'afforestation'. Kyoto Forest toujours non citee explicitement.

**Issues:** `definition-FAO-plantation-incomplete,Kyoto-Forest-non-citee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [15] Donne moi une définition d'une agroforêt

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition d'une agroforêt Une agroforêt est définie comme un **forest qui est géré plus ou moins intensivement par de petits propriétaires produisant du bois et des produits non ligneux**. Cette définition est issue de **Zomer RJ, Trabucco A, Coe R et Place F. (2009)**.  - Catégorie : LandUse -...

**Expert note:** Correct. Entree Agroforest (LandUse) retrouvee. Legere amelioration de formulation vs v1.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [16] Donne moi une définition de la forêt urbaine

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définition de la forêt urbaine Il n'y a pas de définition spécifique de la forêt urbaine dans le contexte fourni. Cependant, certaines définitions mentionnent les arbres en milieu urbain : - **Aruba (1998)** : Les parcs urbains et les arbres à des fins agricoles et commerciales sont considérés c...

**Expert note:** Identique a v1. Donnees du corpus limitees sur la foret urbaine.

**Correction needed:** Toujours pas de definition specifique. Les nouveaux keywords 'peri-urban' et 'street tree' n'ont pas apporte de nouvelles entrees. La reponse doit mentionner explicitement que la FAO exclut l'usage urbain.

**Issues:** `exclusion-FAO-urbaine-non-mentionnee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [17] Quelles sont les principales différences entre forêt primaire et forêt naturellement régénérée ?

**Rating:** 2/5 ██░░░  ⚠️ `corrected`

**Answer preview:** ### Définitions de forêt Les principales différences entre forêt primaire et forêt naturellement régénérée ne sont pas explicitement définies dans le contexte fourni. Cependant, nous pouvons identifier certaines caractéristiques qui pourraient être liées à ces types de forêts.  - La **forêt primaire...

**Expert note:** Amelioration vs v1 (etait rejete 1/5). La reponse tente une synthese mais reste insuffisante faute de donnees FAO FRA.

**Correction needed:** La reponse dit que les differences ne sont pas explicitement definies puis tente une synthese partielle. FAO FRA distingue clairement : primaire = aucune activite humaine visible, processus non perturbes ; naturellement regeneree = inclut forets secondaires en recuperation.

**Issues:** `FAO-FRA-non-retrouvee,synthese-incomplete`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [18] Quelles sont les principales différences entre plantation forestière et forêt naturellement régénérée ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Principales différences entre plantation forestière et forêt naturellement régénérée Les principales différences entre plantation forestière et forêt naturellement régénérée sont souvent basées sur les critères de définition des forêts utilisés par différents pays et organisations.   - **Définit...

**Expert note:** Nette amelioration vs v1 (etait rejete 1/5). La reponse synthetise correctement : plantation = plantee, gestion intensive ; naturellement regeneree = especes natives, recuperation naturelle. Les nouveaux keywords ont permis de retrouver des entrees pertinentes.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [19] En quoi l'usage du sol (land use) peut être d'intérêt quand on cherche à caractériser la forêt ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Intérêt de l'usage du sol pour caractériser la forêt L'usage du sol (land use) peut être d'intérêt pour caractériser la forêt car il permet de comprendre les différentes activités humaines et les pratiques de gestion qui ont un impact sur la forêt.  - Il aide à identifier les zones où la forêt e...

**Expert note:** Correction totale vs v1 (etait NOT_IN_CORPUS rejete 1/5). Le nouvel intent 'conceptual' avec CONCEPTUAL_SPARQL retrouve les definitions LandUse et la reponse explique correctement l'interet de cet axe pour la politique et la comptabilite carbone.

---

### [20] En quoi la couverture du sol (land cover) peut être d'intérêt quand on cherche à caractériser la forêt ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Intérêt de la couverture du sol pour caractériser la forêt La couverture du sol (land cover) est un aspect crucial pour caractériser la forêt, car elle permet de définir les différents types de forêts et leurs caractéristiques. Voici quelques points clés qui expliquent pourquoi la couverture du ...

**Expert note:** Correction totale vs v1 (etait NOT_IN_CORPUS rejete 1/5). Le nouvel intent 'conceptual' fonctionne. Reponse correcte sur la compatibilite teledetection et monitoring global.

---

### [21] Est ce que la FAO considère la forêt urbaine comme étant une forêt ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Réponse **Non**, la FAO n'inclut pas la forêt urbaine dans sa définition de forêt.  ### Contexte Selon les définitions de la FAO pour les années **2001**, **2004**, **2005**, **2006** et **2010**, les forêts sont définies comme des terres de plus de 0,5 hectares avec une couverture de canopy sup...

**Expert note:** Excellent. FAO exclut explicitement l'usage urbain. Identique a v1, toujours parfait.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [22] Est ce que l'UNFCCC considère la forêt urbaine comme étant une forêt ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Réponse L'information fournie ne permet pas de déterminer si l'UNFCCC considère la forêt urbaine comme étant une forêt, car les définitions fournies ne mentionnent pas spécifiquement les forêts urbaines.  - Les définitions de l'UNFCCC fournies se concentrent sur les caractéristiques générales de...

**Expert note:** Bonne reponse. Incertitude correctement signalee, criteres UNFCCC bien expliques. Identique a v1.

**SPARQL used:** `PREFIX : <http://example.org/forest#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?jurisdiction ?year ?canopy ?height ?area ?text ?category
`

---

### [23] Qu'est ce qu'un arbre ?

**Rating:** 3/5 ███░░  ⚠️ `corrected`

**Answer preview:** ### Définitions d'arbre Il existe plusieurs définitions d'arbre selon les juridictions et les années. Voici quelques-unes des définitions trouvées :  | Pays | Année | Catégorie | Canopy | Hauteur | Superficie | Texte | | --- | --- | --- | --- | --- | --- | --- | | Antigua et Barbuda | 1941 | Ecologi...

**Expert note:** Identique a v1. Le reranking aide pour les orgs mais pas pour les questions sur les concepts generaux.

**Correction needed:** Tableau de definitions nationales fourni — utile mais la definition FAO centrale (plante ligneuse perenne >=5 m a maturite) n'est pas mise en avant. Le seuil 5 m est crucial car il est utilise dans FAO 2005.

**Issues:** `definition-FAO-arbre-non-prioritisee`

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [24] Est ce que je peux définir une forêt à partir des services écosystémiques qu'elle est en capacité de fournir ?

**Rating:** 4/5 ████░  ✅ `validated`

**Answer preview:** ### Définition d'une forêt à partir des services écosystémiques Il est difficile de définir une forêt uniquement à partir des services écosystémiques qu'elle est en capacité de fournir, car les définitions de forêt fournies dans le contexte se concentrent principalement sur les caractéristiques phys...

**Expert note:** Amelioration vs v1. Le nouvel intent 'conceptual' apporte des definitions ecologiques. La reponse correctement conclut que les services sont des consequences, non des criteres definitoires.

---

### [25] Est ce que je peux définir une forêt à partir de ses fonctions écologiques ?

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** ### Définition d'une forêt à partir de ses fonctions écologiques Oui, certaines définitions de forêt sont basées sur les fonctions écologiques.  - **AFF (2011)** : définit un écosystème forestier comme un complexe dynamique de communautés de plantes, d'animaux et de micro-organismes et de l'environn...

**Expert note:** Excellent. AFF 2011 correctement citee. Identique a v1, toujours parfait.

**SPARQL used:** `PREFIX : <http://example.org/forest#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX xsd: <`

---

### [26] L'EUDR reprend essentiellement les définitions (forêt en particulier) de la FAO

**Rating:** 5/5 █████  ✅ `validated`

**Answer preview:** Cette information n'est pas présente dans le corpus de définitions forestières.  Le corpus contient des définitions nationales et internationales de la forêt (FAO, UNFCCC/KP, définitions nationales de plus de 150 pays). Si votre question porte sur une organisation ou un pays spécifique, veuillez vér...

**Expert note:** Correction totale vs v1 (etait rejete 1/5 auto-contradictoire). Le pipeline retourne maintenant NOT_IN_CORPUS avec disclaimer clair. Aucune affirmation non fondee.

---
