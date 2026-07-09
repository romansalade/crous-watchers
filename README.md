# CROUS Montpellier – Alerte logement 🏠🔔

Envoie une notification sur ton téléphone dès qu'une nouvelle offre de
logement CROUS apparaît à Montpellier. Gratuit, sans serveur à payer.

## Étape 1 — Installer l'app de notification (2 min)

1. Installe l'app **ntfy** sur ton téléphone :
   - Android : [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
   - iPhone : [App Store](https://apps.apple.com/app/ntfy/id1625396347)
2. Ouvre l'app, appuie sur **+ (Subscribe to topic)**.
3. Choisis un nom de "topic" **unique et un peu random** (ex :
   `mtp-logement-` suivi de quelques chiffres au hasard). N'importe qui
   connaissant ce nom peut voir tes notifs, donc évite un nom trop simple
   comme "montpellier".
4. Abonne-toi à ce topic dans l'app.

## Étape 2 — Créer le dépôt GitHub (5 min)

1. Va sur [github.com/new](https://github.com/new), crée un repo (public ou
   privé, peu importe), par exemple `crous-watcher`.
2. Mets tous les fichiers de ce dossier dedans (`watch_crous.py`,
   `.github/workflows/watch.yml`, `seen.json` vide `[]`, ce README).
   Le plus simple : upload direct des fichiers via l'interface GitHub
   ("Add file" → "Upload files"), ou via git en ligne de commande.
3. Crée un fichier vide `seen.json` contenant juste `[]` à la racine.

## Étape 3 — Configurer le topic ntfy

Dans ton repo GitHub :
1. Va dans **Settings → Secrets and variables → Actions**.
2. Onglet **Secrets** → **New repository secret** :
   - Nom : `NTFY_TOPIC`
   - Valeur : le nom de topic choisi à l'étape 1 (ex: `mtp-logement-4821`)
3. (Optionnel) Onglet **Variables** → **New repository variable** :
   - Nom : `CROUS_URL`
   - Valeur : l'URL exacte de ta recherche filtrée sur Montpellier — va sur
     [trouverunlogement.lescrous.fr](https://trouverunlogement.lescrous.fr),
     lance une recherche pour Montpellier, copie l'URL de la page de
     résultats. Si tu ne mets rien, le script utilise l'URL par défaut dans
     le code (à vérifier/adapter, voir note ci-dessous).

## Étape 4 — Activer et tester

1. Va dans l'onglet **Actions** de ton repo GitHub.
2. Clique sur le workflow "Surveille logements CROUS Montpellier".
3. Clique sur **Run workflow** pour le lancer manuellement une première fois.
4. Regarde les logs : ça doit dire combien de logements trouvés à Montpellier.
5. Ensuite, il tournera automatiquement toutes les 20 minutes tout seul.

## ⚠️ Notes importantes

- **Vérifie l'URL** : le site CROUS change parfois l'identifiant de la
  campagne dans l'URL (ex: `/tools/42/search` devient `/tools/47/search`
  d'une année sur l'autre). Si le script ne trouve plus rien alors qu'il y
  a des offres visibles sur le site, mets à jour la variable `CROUS_URL`
  avec l'URL actuelle.
- **"Vous êtes trop nombreux"** : le site CROUS limite parfois l'accès en
  période de forte affluence. Si ça arrive, le script échouera ce
  passage-là mais réessaiera au suivant — rien à faire.
- **Vie privée** : garde ton nom de topic ntfy secret (ne le partage pas
  publiquement), sinon d'autres personnes pourraient voir tes notifications.
- Ce script se contente de **regarder** la page publique et de comparer —
  il ne fait aucune action à ta place (il ne réserve rien). C'est toujours
  toi qui dois aller valider un vœu sur le site CROUS.
