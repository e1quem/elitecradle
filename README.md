# EliteGeoCradle

**Visualiser la ville de naissance des puissants de la Ve République**. 

Le but est de visualiser sur une carte des points indiquant la ville de naissance de ces personnes, avec un différent ton coloré pour chaque grande famille thématique (une couleur pour chaque sous-thème). 

Rajouter un système évitant d'avoir des points superposés lorsque plusieurs personnes sont nées dans la même ville. 

Survoler chaque point donnerait le nom et les tags de cette personne. Cliquer dessus ouvrirait une fenêtre de navigateur dans la page Web, avec la page wikipédia.

Avoir l'année de naissance nous permet d'observer une répartition dans le temps : une visualisation dans laquelle les points s'affichent progressivement.

Avec le simple nombre de personnes dans chaque région/département, on peut faire des classements / cartes d'intensité de répartition territoriale.

Il faut inclure les DOM TOM. Centralisation VS décentralisation ? 

Idée de prolongation, plus tard : l'école/université de ces personnes.

On veut, pour chaque personne : 
- nom
- ville de naissance
- associer le département de cette ville
- associer la région de cette ville
- année de naissance
- rôle (député, sénateur...)

## Architecture et techniques principales

- **Pipelines `fetch/*`** : chaque cohorte (député·es, sénateurs·trices, ministers, présidents, professeurs du Collège de France, exécutifs CAC40) dispose de son propre dossier `fetch/<cohorte>` avec `raw/` (sources brutes Excel / CSV / listes), `interim/` (fichiers enrichis, logs et résultats partiels) et `processed/` (nettoyés). La collecte repose sur des scripts Python qui lisent ces sources, récupèrent Wikipedia (ou Sycomore pour les députés) via des helpers communs puis géolocalisent les villes avec l’API `api-adresse.data.gouv.fr`.
- **Dossier `utils/`** : `utils/utils.py` applique quelques tours malins : `force_ipv4()` contourne les problèmes DNS avec certains sites, `get_wikipedia_soup()` explore une palette de suffixes pour gérer les homonymes et les variations de nom, `extract_pob/dob/arrondissement()` scrutent infobox, catégories et paragraphes d’intro pour une robustesse maximale, et `finding_geo()` centralise la géolocalisation. Le module mémorise aussi les vérifications “est-ce que c’est en France” pour éviter de répéter les requêtes.
- **Députés (pagination cassée)** : on contourne la limite de 500 résultats sur Sycomore en lisant la liste des départements et en lançant une requête par département, puis on scrappe chaque fiche individuelle (en respectant la cadence) et on traite à part les colonies anciennes et les arrondissements parisiens (extraction via Wikipedia + standardisation manuelle des coordonnées).
- **Concurrence maîtrisée** : les scrapers utilisent `ThreadPoolExecutor` (10 threads pour la plupart, 1 pour les exécutifs faute d’être trop agressif) pour accélérer la recherche sur Wikipedia tout en limitant la charge. Le module fusion `analysis/merge.py` impose une hiérarchie de tags et déduplique sur `name+dob` avant d’exporter `merged_raw.csv`.
- **Jointures socio-économiques** : `analysis/cross_sourcing.py` fusionne `merged_clean.csv` avec des tables de population, revenus et pauvreté (fournies dans `analysis/sources/` et retraitées dans `analysis/interim/`) ; il calcule des exposants démographiques pondérés par décennie (via `birth_decade`), utilise des correspondances floues `rapidfuzz` pour aligner les noms de villes, et produit les tables `analysis/processed/analysis_*.csv` prêtes pour les visualisations.
- **Analyse finale** : `analysis/analyze.py` charge les tables traitées, crée classements, heatmaps (sauvegardées dans `analysis/outputs/`) et régressions log-linéaires avec repérage des sur- et sous-performeurs, de sorte qu’on peut reproduire les graphiques/insights à partir d’un seul script.

## Trucs malins à mentionner dans le README

- `utils.get_wikipedia_soup` tente des variantes autorisant `_(homme_politique)`, `_(personnalité_publique)` ou `_(PDG)` pour éviter d’échouer sur les pages à désambiguïser et affiche un log de réussite pour faciliter le debug.
- Les arrondissements parisiens sont extraits via `extract_arrondissement` (hypothèses sur les catégories, l’infobox et le paragraphe d’intro) puis standardisés avec des coordonnées fixes pour éviter les points qui flottent dans Paris.
- Les outils de géolocalisation `finding_geo` peuvent retourner `foreign` lorsqu’on détecte une naissance hors de France ; on complète ensuite à la main les DOM-TOM et anciennes colonies en s’appuyant sur des listes manuelles ou sur `geo_finding.py`/`mn_geo_*`.
- `analysis/cross_sourcing.py` normalise les codes INSEE, remplace les noms mal orthographiés via `rapidfuzz`, pondère les populations par décennie issue du dataset historique et ajoute des métriques comme `expo_demog` ou `politics` pour chaque niveau géographique.
- Les données intermédiaires (`fetch/*/interim`, `analysis/interim`) servent de checkpoints : elles sont le meilleur endroit pour inspecter les coupures (cities “Unknown”, `geo_missing`, arrondissements manquants) avant de procéder aux nettoyages finaux dans `processed/`.


**Politiciens**
- [x] l'ensemble des députés (tout se trouve sur le site de l'AN) (jaune)
- [x] l'ensemble des sénateurs (liste des  / prénoms / dob en excel, information de naissance à trouver sur wikipedia) (orange)
- [x] l'ensemble des présidents (gérer les naissance à l'étranger) (violet)
- [ ] l'ensemble des ministers des gouvernements de la Ve république : tout se fait sur wikipedia, il faut trouver la liste des gouvernements de la Ve République, puis travailler par indentation pour aller visiter les pages de chaque minister de chaque gouvernement et en extraire leur nom, dob et pob (rouge)

**Entreprise**
- PDG d'entreprises du CAC40 (vert)
- top executives de ces entreprises

**Académie**
- [x] tous les professeurs ayant eu une chaire au Collège de France : on peut obtenir leurs noms en filtrant à partir de 1958 (bleu)

**Militaire**
- Quels types de hauts placés ?

Pour les doublons : 
- une personne ayant eu plusieurs mandats dans la même fonction : on garde une seule entrée, car la date ne compte pas
- une personne ayant eu différentes fonctions : on rajoute le tag de chaque fonction à son entrée

Visualisation: 
- densité : https://observablehq.com/@d3/choropleth/2
- bubbles : https://observablehq.com/@d3/bubble-map/2
- spikes : https://observablehq.com/@d3/spike-map/2
- dots over time : https://observablehq.com/@d3/walmarts-growth

1. Trouver les personnes
2. Trouver et extraire les informations
3. Visualiser et analyser les résultats

gérer les villes de naissance à l'étranger

# 1. Députés

**DÉPUTÉS**
- extraire csv à partir du site de l'assemblée nationale
- supprimer les doublons
- vérifier si il y a le mot député dans la page wikipédia pour éviter les homonymes.

Pagination is broken. Sur data.gouv.fr, ça ne va que jusqu'en 1997. Solution: faire une requête par département.
On doit extraire les départements du site et les nettoyer.

Attention, parfois il n'y a qu'un seul résultat, notre code n'est pas adapté car le site web fait une fiche biographique pour le député, par un tableau de résultat. On le fait manuellement

- **Côte d'Ivoire**
Félix Houphouët-Boigny, 1905
- **Gabon**
Jean-Hilaire Aubame, 1912
- **Gabon-Moyen-Congo**
Maurice, Albert, Henri Bayrou, 1905.
- **Mauritanie**
N'Diaye Sidi El Moktar, 1916.
- **Moyen Congo**
Jean Félix-Tchicaya, 1904.
- **Oubangui-Chari**
Barthélémy Boganda, 1910.
- **Oubangui-Chari-Tchad**
René Malbrant, 1903.

Au lieu d'utiliser wikipédia, on peut sûrement les rechercher sur le site de l'AN.

Il va falloir faire du scrapping page par page sur le site de l'AN pour obtenir le lieu de naissance : https://www2.assemblee-nationale.fr/sycomore/fiche/3874 il va falloir changer l'id de chaque page, recherche "Cinquième République - Assemblée nationale" et extraire le "Né le 8 décembre à Tarbes".

https://www2.assemblee-nationale.fr/sycomore/resultats?base=tous_departements&regle_nom=est&nom=René+Malbrant&departement=&choixdate=intervalle&debutmin=&finmin=&dateau=&legislature=&choixordre=chrono&submitbas=Lancer+la+recherche

### PROGRÈS POUR LES DÉPUTÉS
Site de l'AN: pagination cassée.
Solution: itérer sur chaque département pour ne pas dépasser les 500 résultats par requête. Bien, on obtient la liste de tous les prénoms.
On souhaite ensuite utiliser la base de donnée de l'AN au lieu de celle de wikipédia: plus fiable pour les députés. Mais leur moteur de recherche par nom ne fonctionne pas.
Il faut qu'on utilise les pages par députés. Au lieu de les brute force toutes, on les extrait quand on fait notre requête pour obtenir la liste de tous les prénoms. Ensuite, on fait une requête pour chaque id.


1. extraire le codage des départements à partir du HTML du site de l'AN
2. nettoyer les départements qui n'affichent qu'un seul résultat
3. itérer sur cette liste de départements pour obtenir tous les députés à partir de 09/12/1958 (Ve République)
4. pour chaque résultat, on extrait du tableau le nom, l'année de naissance et l'id qui mène à la fiche de ce député
5. à partir de cette liste d'id, on scrappe le site de l'AN pour extraire nom, dob, pob et dept ob
6. à partir de cette liste, on utilise la pob et le dept ob avec l'API geo gouv.fr pour obtenir le numéro du département, la localisation GPS de la ville et le nom de la région

Nettoyage de parliaments_data.csv:
- After running the code, we have a few connection errors. We manually clean up the results. On recode manuellement les noms de ville suivant différents orthographe, accents, ou conventions de tirets (Paris 16e becomes Paris 16 all the time), Aix les bains devient Aix-les-bains.
- On recode André Godin comme né à Bourg-en-Bresse.
- Pour tous les parisiens, il faudrait distinguer l'arrondissement.
- On cherche manuellement les 12 N/A et empty pour pob. C'est un succès : notre code a trouvé un pob pour la quasi-totalité des députés. Il manque cependant les informations geo pour une partie d'entre eux : we populate using ``geo_finding.py``

```
(base) eyquem@MacBook-Air-de-Eyquem EliteGeoCradle % python3 fetch_parliaments_data.py
[1242/4555] Jean-Noël Kerdraon...Error on 3620: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/3620 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab2350>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1243/4555] ID 3620 : Error fetching data.Error on 11050: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/11050 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab1bd0>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1244/4555] ID 11050 : Error fetching data.Error on 2061: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/2061 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab1450>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1245/4555] ID 2061 : Error fetching data.Error on 529: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/529 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab3110>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1400/4555] Véronique Hammerer...Error on 19482: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/19482 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab11d0>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1401/4555] ID 19482 : Error fetching data.Error on 18575: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/18575 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab25d0>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1402/4555] ID 18575 : Error fetching data.Error on 18509: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/18509 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab3110>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1403/4555] ID 18509 : Error fetching data.Error on 19111: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/19111 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab1bd0>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1404/4555] ID 19111 : Error fetching data.Error on 17318: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/17318 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab1450>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1405/4555] ID 17318 : Error fetching data.Error on 19282: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/19282 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab2fd0>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1406/4555] ID 19282 : Error fetching data.Error on 18409: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/18409 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab1950>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1407/4555] ID 18409 : Error fetching data.Error on 18424: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/18424 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab34d0>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1408/4555] ID 18424 : Error fetching data.Error on 5909: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/5909 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab1950>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1409/4555] ID 5909 : Error fetching data.Error on 2352: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/2352 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab2fd0>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1536/4555] Jean-Luc Reitzer...Error on 10648: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/10648 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab3390>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[1537/4555] ID 10648 : Error fetching data.Error on 887: HTTPSConnectionPool(host='www2.assemblee-nationale.fr', port=443): Max retries exceeded with url: /sycomore/fiche/887 (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x146ab16d0>: Failed to resolve 'www2.assemblee-nationale.fr' ([Errno 8] nodename nor servname provided, or not known)"))
[4555/4555] René Malbrant...                       name     tag   dob  ...       lon confidence     id
```

On a 365 personnes nées à Paris. On crée ``wikipedia_arr`` afin de scraper l'arrondissement de naissance dans wikipedia (en checkant catégories, infobox et paragraphe d'introduction).
Lorsque les pages ne sont pas trouvées, on vérifie manuellement l'arrondissement (quelques dizaines de personnes).

Found 233 arr. out of 365 entries (63.84%) (250 after manual inspection).

pour lon et lat des arrondissements: filtrer et entrer la réelle lon et lat, pour l'instant c'est un peu partout les mêmes. On recode manuellement les coordonnées des GPS des arrondissements dans ``parliaments_data_arr_enriched`` et de ``parliaments_data_clean``. Dans ``parliaments_data_clean``, on remplace les 365 pob "Paris" par celles de ``parliaments_data_arr_enriched`` avec arrondissement.

On a maintenant une liste propre avec peu de trous, des arrondissements parisiens et des dob recodées.

On recode les 10 lignes qui ont des pob mais pas de dept ou foreing : ce sont des communes disparues.

On a notre version finale clean (on rencontrera de nouveaux problèmes au moment de mapper).




# 2. Sénateurs

1. à partir du excel, on fait un df avec : 
- une colonne name (avec dedans Prénom usuel suivi de Nom usuel, respectivement 4e et 3e colonnes du excel)
- une colonne tag (le tag est senat pour tous)  
- une colonne dob (colonne F Date naissance sous format 19/06/1930  00:00:00, on extrait 1930)

``fetch_sent_data`` prend les prénoms de ce excel et les recherche sur internet. Utiliser le site du sénat n'est pas fiable, il n'y a pas toujours la ville de naissance. Flemme de faire deux scrappers puis de combiner les résultats.

Il faut ensuite nettoyer ce résultat, manuellement, je m'en occupe. Parenthèses avec le département ou la région, phrase qui déborde, arrondissement de Lyon.

1943 sénateurs : 233 unknown et 234 not found.

Ensuite, on enrichit avec geo.data.gouvernement. Et pour les arrondissement, on hard code les lon et lat avec ``paris_replacement``.



# 3. Collège de France

On extrait les prénoms des chaires débutées après 1958 dans ce excel : 
https://www.college-de-france.fr/fr/actualites/liste-historique-des-chaires-du-college-de-france
On se sert de ces prénoms pour notre habituel scrapping wikipedia, cette fois pob + dob.

Nettoyage manuel du fichier cf_geo_missing.

finding_geo to obtain cf_geo_enriched.
arr_replace to obtain proper arr. localisation.
manuellement: on vérifie les dept_num foreign qui ont un pob qui n'est pas foreign ni Not found ni Unknown. On repasse ça dans finding_geo, puis dans arr_replace, et on l'ajoute à cf_geo_enriched, qui devient cf_clean. 


# 4. ministers

Au lieu de faire du scrapping indenté dans wikipédia, on a direct trouvé une liste des ministers de la Ve et on fait le scrapping habituel.

On a notre code qui nous donne mn_geo_missing. On fait un micro nettoyage manuel.
Ensuite, on utilise finding_geo.py pour l'enrichir avec des données GPS. On a 182 foreign. On a 32 dept_num foreign qui ont des pob correctes. On les extrait et on les réutilise dans finding_geo. On insère le résultat dans mn_geo_enriched.

On utilise arr_replace. On obtient mn_clean.py après avoir vérifié manuellement si les données étaient correctes. 



# 5. PDG CAC 40

On liste les entreprises actuellement dans le cac40 ou ayant été dans le CAC40, étant encore en activité et ayant une activité d'une échelle suffisante : exec_list.txt
On donne les liens pappers à un algorithme qui vient scrapper le nom et l'entreprise des administrateurs et directeurs généraux de ces entreprises : exec_fetch.py. Output : exec_staff.csv. 
On recode les nom des firms pour que le nom de l'entreprise soit facilement identifiable.
On a 1340 staff.

# Sources

**SOURCES**
To develop the rest of the functions, we manually look presidents up: https://fr.wikipedia.org/wiki/Liste_des_présidents_de_la_République_française

**AN**
https://www2.assemblee-nationale.fr/sycomore/recherche
check on wikipedia when information isn't available

Sénat
**Informations générales sur les sénateurs**
https://data.senat.fr/les-senateurs/

**Pour l'API geo**
https://www.data.gouv.fr

**Liste historique des chaires du Collège de France**
https://www.college-de-france.fr/fr/actualites/liste-historique-des-chaires-du-college-de-france

**ministers**
http://www.histoire-france-web.fr/Documents/ministers.htm

**Historique des entreprises du CAC40**
https://www.bnains.org/archives/histocac/histocac.php

Note : avoir un classement par ville, c'est cool mais inutile. Il faut faire un classement ratio population/nombre de personnes.

Biais : en cherchant sur wikipedia, on a uniquement les personnes suffisamment importantes.


  Reorganization proposal:

  - Introduce src/ with subfolders by concern (src/fetch/ for each cohort, src/db/ for the DB-building scripts, src/analysis/ for
    geographic/demographic work, src/utils/ for shared helpers). This keeps the python scripts grouped logically instead of scattered at
    the top level.
  - Move raw inputs from sources/ into data/raw/ and ensure every script pulls from there; add data/interim/ for intermediate cleans
    (e.g., an_raw.csv), and data/processed/ for the final tables currently living in outputs/. Rename outputs/ to data/processed/
    outcomes/ or similar so downstream consumers know it’s the DB output.
  - Create a db/ directory (or data/warehouse/) holding the schema/ETL for “the database” you’re assembling; expose a single
    populate_db.py that ingests the processed CSVs and writes to a sqlite/Postgres file or SQL scripts.
  - Reserve analysis/ (or notebooks/) for future geographic/demographic joins, keeping the exploratory work separate from production
    scripts.
  - Add a short README or pipeline.md documenting: how to refresh raw data, how to rebuild the DB, and where to drop in demographic
    layers later.
