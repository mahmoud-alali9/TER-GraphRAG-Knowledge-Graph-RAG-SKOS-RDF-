#!/bin/sh
# !/bin/sh = indique quel interpréteur utiliser (sh = shell POSIX)
# ce script s'exécute dans un conteneur Docker au démarrage

set -e
# si UNE commande échoue → le script s'arrête immédiatement
# sans ça, les erreurs seraient ignorées et le script continuerait

FUSEKI_URL="${FUSEKI_URL:-http://fuseki:3030}"
# ${VARIABLE:-valeur_par_defaut}
# si la variable FUSEKI_URL est définie → on l'utilise
# sinon → on utilise "http://fuseki:3030"
# "fuseki" = nom du conteneur Docker (résolution DNS interne)

DATASET="${DATASET:-forestKG}"
# si DATASET défini → on l'utilise, sinon "forestKG"

TTL_FILE="${TTL_FILE:-/data/schema.ttl}"
# chemin du fichier TTL dans le conteneur Docker

ADMIN_PASSWORD="${FUSEKI_ADMIN_PASSWORD:-admin}"
# mot de passe admin Fuseki, par défaut "admin"

echo "[loader] Waiting for Fuseki at ${FUSEKI_URL}..."
# affiche un message de démarrage

until curl -sf "${FUSEKI_URL}/\$/ping" > /dev/null; do
  sleep 2
done
# until = boucle "jusqu'à ce que la condition soit vraie"
# curl -sf = envoie une requête HTTP silencieuse (-s) et échoue en cas d'erreur (-f)
# "${FUSEKI_URL}/$/ping" = http://fuseki:3030/$/ping
#   c'est l'endpoint de santé de Fuseki (répond 200 OK quand prêt)
# > /dev/null = redirige la sortie vers nulle part (on veut juste savoir si ça marche)
# sleep 2 = attend 2 secondes avant de réessayer
#
# la boucle tourne jusqu'à ce que Fuseki réponde :
# tentative 1 → Fuseki pas encore prêt → curl échoue → sleep 2
# tentative 2 → Fuseki pas encore prêt → curl échoue → sleep 2
# tentative 3 → Fuseki prêt → curl réussit → on sort de la boucle

echo "[loader] Fuseki is up."

curl -sf -X POST "${FUSEKI_URL}/\$/datasets" \
  -u "admin:${ADMIN_PASSWORD}" \
  --data "dbName=${DATASET}&dbType=tdb2" \
  && echo "[loader] Dataset created." \
  || echo "[loader] Dataset may already exist, continuing."
# curl -X POST = envoie une requête HTTP POST
# -u "admin:admin" = authentification HTTP basique
# --data "dbName=forestKG&dbType=tdb2" = données du formulaire
#   dbName = nom du dataset à créer
#   dbType = tdb2 = format de stockage persistant de Fuseki
# && = si la commande réussit → affiche "Dataset created."
# || = si la commande échoue  → affiche "may already exist" (pas d'arrêt)

curl -sf -X POST "${FUSEKI_URL}/${DATASET}/data" \
  -u "admin:${ADMIN_PASSWORD}" \
  -H "Content-Type: text/turtle" \
  --data-binary "@${TTL_FILE}"
# charge le fichier TTL dans le dataset
# -X POST = requête POST
# "${FUSEKI_URL}/forestKG/data" = endpoint pour charger des données
# -H "Content-Type: text/turtle" = on dit que le fichier est en format Turtle (RDF)
# --data-binary "@/data/schema.ttl" = envoie le fichier tel quel (binaire)
#   le @ signifie "lis ce fichier et envoie son contenu"

echo "[loader] TTL loaded successfully into /${DATASET}."
# message de confirmation