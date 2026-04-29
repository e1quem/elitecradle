# A Geographical Study of French Elites Origins

## Abstract

This project analyses the geographical origins of French political, corporate and academic prominent figures under the Fifth Republic. Using web-scraping to construct and enrich a comprehensive biographical database of 6,500 individuals, we quantify geographical hubs by cross-referencing our data with demographic and socio-economic factors. Our scope ranges from aggregated regions to Parisian arrondissements. Our results highlight a Parisian dominance and identify significant geographical outliers (overperformers like Neuilly-sur-Seine and Boulogne-Billancourt) through multivariate OLS regressions.
<br><br>

## Introduction

While the role of social origin [1] and education [2] in the making of elites is a well documented theme in French sociology, the geographical origin of these individuals is often treated as a secondary variable. This project seeks to find which parts of the French territory produce the most elites, and understand the way demographic, economic and social factors drive this production.

This project was conceived as a way to master automated internet scraping, and was driven out of curiosity to settle a familial debate. Using public sources, we build a dataset using the place of birth (```pob```) as a common variable. We focus on three clusters of individuals: political (including presidents, ministers, Parliament members and senators), scholars (professors of the Collège de France, relevant academic figures) and corporate (CEOs, executives, administrators and board members of large companies). 

In order to ensure that socio-economic and demographic characteristics remain broadly in line with the contemporary picture, we limit the scope of our study to the Fifth Republic. Geographically, we analyse mainland France and all DOMs except for Mayotte. This choice stems from data availability constraints from INSEE. 


[1] *Benveniste, S. (2026). Noble Lineage and Inequalities in Access to Elite Education. ; Benveniste, S., & Pavie, A. (2025). Elites: Origin, education, destination. ; Birnbaum, P., Barucq, C., Bellaiche, M., & Marié, A. (1978). La Classe dirigeante française: Dissociation, interpénétration, intégration. ; Bourdieu, P. (2002). La noblesse d’état: Grandes écoles et esprit de corps. ; Gavras, J. (2017). Les Bonnes Conditions.* 

[2] *Bourdieu, P., & Passeron, J.-C. (1994). Les héritiers: Les étudiants et la culture. ; Bourdieu, P., & Passeron, J.-C. (2005). La reproduction: Éléments pour une théorie du système d’enseignement.*
<br><br>

## Data acquisition and methodology

The ```fetch``` folder is dedicated to data acquisition, following a strict ```src```, ```interim```, ```out``` data pipeline. ```utils``` shares heuristics for Wikipedia scraping, geolocation and arrondissement finding. Each cohort presented different data acquisition challenges, that had to be overcome with dedicated methods.

#### ```fetch/parliament```

No database of all Parliament Members of the Fifth Republic is publicly downloadable [3]. The main reference is the [National Assembly Sycomore](https://www2.assemblee-nationale.fr/sycomore/recherche) whose search engine outdated pagination only displays the first 500 results of a query. To bypass this, we extract the HTML encoding of departments of the search engine (```src/departments_raw.txt```) and implement a department-by-department recursive query so as never to exceed the functional pagination limit.

From this list of ids, we scrape 4,539 standardised biographical profiles on the National Assembly websites. Using multithreading, we enrich this data using [geo.api.gouv.fr](https://geo.api.gouv.fr) for geographical information. For Parisian Parliament members, we use a Wikipedia scraping system with a cascading fallback mechanism to find their arrondissement of birth, achieving a 68.4% recovery rate. 

After manual cleaning, ```out/an_clean.csv``` contains a clean dataset of 4,539 National Assembly members.

[3] *This [data.gouv.fr dataset](https://www.data.gouv.fr/datasets/fichier-historique-des-deputes-et-de-leurs-mandats) produced by the National Assembly only goes back to 1997.  We don't use the [BRÉF database](https://zenodo.org/records/14628510) : while it contains data for 3,266 senate members, it only has data for 2,500 National Assembly Members.*


#### ```fetch/senators```

We use the [General Information on Senators](https://data.senat.fr/les-senateurs/) database published by the French Senate as a starting point for Wikipedia scraping. We try various thematic URL suffixes and different arrangements of compound names to ensure high match rates, and check for specific keywords on the page before extracting any data. After arrondissement checking and geographical enrichment, ```out/sn_clean.csv``` contains a dataset of 1,477 senators.

#### ```fetch/ministers```

Instead of navigating within the tree structure of Wikipedia's [List of French Governments](https://fr.wikipedia.org/wiki/Liste_des_gouvernements_de_la_France), we use this [unofficial but unified list of all ministers of the Fifth Republic](http://www.histoire-france-web.fr/Documents/ministres.htm). ```out/mn_clean.csv``` contains a dataset of 430 ministers. 


#### ```fetch/scholars```

Our first source is the [Historical List of Chairs at the Collège de France](https://www.college-de-france.fr/fr/actualites/liste-historique-des-chaires-du-college-de-france) maintained by the Collège de France, from which we extract all chairs that were ongoing during the Fifth Republic. Many professors at the Collège de France were born abroad: we find full data for only 182 scholars. 

To counter this issue, we scrape Wikipedia's [French Scholars](https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Universitaire_fran%C3%A7ais_du_XXe_si%C3%A8cle) category as a secondary source to further enrich our dataset, raising the total amount of scholars to 589. 


#### ```fetch/executives```

There isn't any official list of CEOs and top executives of CAC40 companies. We use this [amateur list of historical CAC40 companies](https://www.bnains.org/archives/histocac/histocac.php) as a source of [Pappers](https://www.pappers.fr) URLs, from which our Selenium Chrome scraper extracts names of administrators of these firms. We only find biographical data for 406 out of the 1,340 names that were extracted. Accounting for those born abroad, this method has a low success rate, with full data for only 232 individuals.

To further populate this category, we scrape Wikipedia's [French CEOs](https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Chef_d%27entreprise_fran%C3%A7ais) and [French Business Personalities](https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Personnalit%C3%A9_fran%C3%A7aise_du_monde_des_affaires_du_XXIe_si%C3%A8cle) categories. This raises the total of executives to 603.

#### ```fetch/merging```

When merging all those datasets, we handle career progression by applying a strict tag hierarchy : ```president > minister > scholar > executive > senator > depute```. 

Before manual cleaning, ```interim/merged_raw.csv``` contains 7,745 individuals. We delete individuals born before 1870 and those born in foreign cities with french homonyms, we correct names of municipalities that have ceased to exist, etc. We are left with an exploitable dataset of 6,500 individuals structured in the following way:

| Category    | Sub-category     | Headcount | % of the total | Sources                      |
| ----------- | ---------------- | --------- | -------------- | ---------------------------- |
| *Political* | ```parliament``` | 3,590      | 55.23%         | Sycomore, Wikipédia          |
| *Political* | ```senat```      | 1,280      | 19.69%         | Senate, Wikipedia             |
| *Political* | ```ministers```  | 430        | 6.61%          | Other, Wikipedia             |
| *Political* | ```president```  | 8          | 0.1%           | Wikipedia                    |
| *Academic*  | ```scholar```    | 589        | 9.06%          | Collège de France, Wikipedia |
| *Corporate* | ```executive```  | 603        | 9.27%          | Pappers, Wikipedia           |
| **Global**  |                  | **6,500**  | **100%**       |                              |

<br><br>

### Exogenous data sources

Our analysis is based on demographic, economic and social data.

For demographic data, we use INSEE's [History of municipal populations - 1876 - 2023 population censuses](https://www.insee.fr/fr/statistiques/3698339Historique) dataset (```src/base-pop-historiques-1876-2023.xlsx```). These historical censuses are not conducted at regular intervals: we group them by calculating the average of each decade from 2009 to the beginning of the 20th century. For missing data, we estimate population growth at a 5% per decade rate, based on the most recent census. To avoid comparing a 1940 birth to 2023 population figures, we create a demographic exposure index giving us a unique metric per geographical entity:


$$\text{expo}\_\text{demog} = \sum (\text{Population}_{\text{decade}} \times \text{Weight}_{\text{decade}})$$

Where: 

- $\text{Population}_\text{decade}$ is the average municipal population for a given decade of birth.

- $\text{Weight}\_{\text{decade}} = \frac{n_{\text{born in decade}}}{N_{\text{total}}}$
<br><br>

For economic data at the departmental and regional scale, we obtain median income and poverty rate from INSEE's [Standard of living and poverty by region](https://www.insee.fr/fr/statistiques/7941411?sommaire=7941491) dataset (```src/RPM2024-F21.xlsx```) and DREES's [2023 Statistical Overview](https://data.drees.solidarites-sante.gouv.fr/explore/dataset/panorama-statistique-toutes-thematiques/information/) (```Panorama_statistique_2024.xlsx```). For municipalities, we obtain the median income from Geoptis's 2021 [Income of the French at the municipal scale](https://www.data.gouv.fr/datasets/revenu-des-francais-a-la-commune) dataset. 

For various social data at each scale (population density, share of diploma holders, etc.), we rely on the [Territory Observatory database](https://www.observatoire-des-territoires.gouv.fr/outils/cartographie-interactive/#bbox=-211484,6329234,794317,830849&c=indicator&selcodgeo=95176&view=map76). 

For educational data at the departmental and regional scale, we use INSEE's [Secondary schools at the start of the 2024 academic year](https://www.insee.fr/fr/statistiques/2012787#tableau-TCRD_061_tab1_regions2016) list. For municipal count, we use the [2024 Ministry of Higher Education enrolment figures for higher education](https://data.enseignementsup-recherche.gouv.fr/explore/assets/fr-esr-atlas_regional-effectifs-d-etudiants-inscrits/). For preparatory classes, we rely on the [Ministry of Higher Education count of students enrolled in preparatory classes](https://data.enseignementsup-recherche.gouv.fr/explore/assets/fr-esr-atlas_regional-effectifs-d-etudiants-inscrits-detail_etablissements/export/) dataset. 

We use ```cross_sourcing.py``` to combine our biographical dataset with demographic and socio-economic data per geographical aggregation. Cities with similar names are distinguished by verifying their department number. We use a 85% threshold fuzzy matching to allow matches despite minor differences with the official INSEE nomenclature. 
<br><br>

## Analysis

In ```/analysis```, we describe our dataset using maps and rankings before analysing it with multivariate regressions using socio-economic factors.
<br><br>

### Rankings

On a regional scale **[Figure 1]**, there is a clear predominance of Île-de-France across all categories in terms of personalities count. It is also the most populated French region, counting 12.38 million inhabitants in 2025, whereas the second most populous region, Auverge-Rhône-Alpes, had a population of 8.16 million according to [INSEE](https://www.insee.fr/fr/statistiques/8290644?sommaire=8290669). This ranking mostly follows the demographic ranking of regions, as most of them are similarly sized.

The global top three regions accounts for 42.2% of all prominent figures while the top five account for 59.9%. This dominancy of the podium is emphasized for executives and scholars, representing respectively 49.9% and 61.2% of the total count.

For the departmental ranking **[Figure 2]**, Paris has a pronounced lead across all categories. The three first global departments account for 21% of all personalities, while the ten first account for 35.5% - a noticeable share out of 100 departments. The top three lead is most pronounced for executives, at 40.6%, and least marked for politics, at 17.7%.

**Figure 1: Ranking of personalities count per region** 
![Regional ranking](analysis/out/top_region.png)

**Figure 2: Ranking of personalities count per department**
![Departmental ranking](analysis/out/top_department.png)

**Figure 3** further highlights the Parisian lead. The top ranking cities - Paris, Lyon and Marseille - are the three major cities of the country. However, it is surprising to observe thtat Neuilly-sur-Seine ([59 200 inhabitants](https://www.insee.fr/fr/statistiques/2011101?geo=COM-92051)) ranks fourth on the global ranking, followed by Boulogne-Billancourt ([120 205 inhabitants](https://www.insee.fr/fr/statistiques/2011101?geo=COM-92012)) and the 16th arrondissement of Paris, in front of Toulouse, the [fourth largest city of the country](https://www.insee.fr/fr/statistiques/2011101?geo=COM-31555). This is substantial for scholars and executives, where Neuilly-sur-Seine and Boulogne-Billancourt produce more individuals than cities like Marseille Lyon.

This over-representation of affluent western Parisian suburbs questions the role played by the geographical concentration of economic capital in elite production. Merging all arrondissements under "Paris" **[Figure 4]** further highlights the high ranking of the capital, [a well studied historical case](https://books.openedition.org/psorbonne/868#anchor-resume). The ranking of Parisian arrondissements **[Figure 5]** shows that over half (51.1%) of the global personalities count come from five Parisian arrondissements out of twenty.

**Figure 3: Ranking of personalities count per city** 
![Municipal ranking](analysis/out/top_city.png)

**Figure 4: Ranking of personalities count per city (Paris merged)** 
![Municipal ranking - Paris merged](analysis/out/top_city_merged.png)

**Figure 5: Ranking of personalities count per arrondissement**
![Arrondissement ranking](analysis/out/top_arrondissements.png)

These descriptive rankings underline peculiar cases like that of Neuilly-sur-Seine and Boulogne-Billancourt and justify the use of socio-economic variables for a thorough analysis of these observations. 
<br><br>

### Maps

A bubble map per category **[Figure 6]** gives a macro perspective of elites origins in mainland France. Visually, we notice a high concentration around Paris and its peripheral municipalities. The Nord department distinguishes itself by having multiple mid-size clusters instead of a unique large one. The weight of large cities is clearly distinguishable: Paris, Lyon, Marseille, etc. There is also a significant concentration along the south-east coastline of the country.

**Figure 6: Bubble map of elites origins per category in mainland France**
![Bubble map](analysis/out/bubble_map.png)

On a regional choropleth map **[Figure 7]**, the weight of Île-de-France is particularly evident. On a departmental scale **[Figure 8]**, highlighted departments are those containing major cities, such as Nord (Lille), Rhône (Lyon) and Bouches-du-Rhône (Marseille). At the municipal level **[Figure 9]**, is apparent that origin cities are distributed evenly across the territory when intensity is disregarded. Finally, plotting a map per Parisian arrondissement **[Figure 10]** shows the high count of elites coming from the West and South of Paris whereas the North-East is less represented in our dataset.

**Figure 7: Choropleth map of elites origins per category on a regional scale in mainland France**
![Regional choropleth](analysis/out/choropleth_region.png)

**Figure 8: Choropleth map of elites origins per category on a departmental scale in mainland France**
![Departmental choropleth](analysis/out/choropleth_department.png)

**Figure 9: Choropleth map of elites origins per category on a municipal scale in mainland France**
![Municipal choropleth](analysis/out/choropleth_city.png)

**Figure 10: Choropleth map of elites origins per category for Parisian arrondissements**
![Arrondissements choropleth](analysis/out/choropleth_arrondissements.png)
<br><br>

### Correlations

To go beyond a basic visual analysis, we use multivariate linear regressions to examine the role of demographic and socio-economic factors in the origins of elites. 

On a regional scale **[Figure 11]**, most categories of figures are highly positively correlated together, and poverty rate shows a negative correlation across all variables. This negative effect of the poverty rate is significantly reduced at the departmental scale, albeit the correlation remains neutral or slightly negative. Between the city dataset and the paris merged dataset **[Figure 12]**, correlations are similar across all categories. For Paris arrondissements **[Figure 13]**, our demographic exposure index is negatively correlated to the median income: we expect the median incomoe to decrease as the population increase. 

**Figure 11: Correlation matrix heatmaps for variables at the regional and departmental scale**
<p align="center">
  <img src=analysis/out/correlation_region.png width="400">
  <img src=analysis/out/correlation_department.png width="400">
</p>

**Figure 12: Correlation matrix heatmaps for variables at the city and city - Paris merged scale**
<p align="center">
  <img src=analysis/out/correlation_city.png width="400">
  <img src=analysis/out/correlation_city_-_paris_merged.png width="400">
</p>

**Figure 13: Correlation matrix heatmap for variables per Parisian arrondissement**
<p align="center">
  <img src=analysis/out/correlation_arrondissements.png width="500">
</p>
<br><br>

### Regressions

We run log-linear multivariate regressions modeling the observed count of elite individuals by place of birth.

On a regional scale and for the global cohort **[Appendix 1]**, we use two explanatory variables for this small quantity of observations (17):  our demographic exposition metric and the rate of preparatory classes per ten thousand inhabitants. We obtain significant results ($***$ and $*$) and a high R-squared value (0.961) - which might indicate overfit given the small sample size. An increase of 1% in our demographic exposure index is correlated with a 0.83% increase in elite individuals count. The presence of preparatory classes is associated with a much larger increase of 2.64% in elite count. According to this model, Île-de-France (1,405 observed, 1,192.8 expected), Occitanie (563 observed, 486.6 expected) and Nouvelle-Aquitaine (606 observed, 531.3 expected) are among the overperforming regions **[Figure 14]**. Pays de la Loire (277 observed, 355 expected), Normandie (262 observed, 330.3 expected) and La Réunion (60 observed, 74.5 expected) are among the underperformers.

**Figure 14: Regional plot of observed values, global cohort**
<p align="center">
  <img src=analysis/out/regression_multi_regions.png width="600">
</p>

The departmental scale, with its 100 observations, allows us to use more variables in our model. We keep these two previous variables, and add the rate of managers and intellectual professions among the po**pulation as well as the poverty rate as supplementary variables. Our model obtains a 0.838 R-squared, with significant results ($***$ and $*$) **[Appendix 2]. The demographic index and the rate of preparatory classes maintain a strong coefficient, respectively 0.77 and 2.06. The rate of managers and poverty are less decisive, with respective coefficients of 0.25 each. The positive coefficient of the poverty rate is a paradoxal result: the more elites come from a department the higher rate of managers, but also the higher the poverty rate. This could arise from high inequalities in richer departments, since areas of wealth production (Paris, Lyon) are also those that attract or create high levels of poverty, leading to a certain degree of social polarisation. 

On a global basis **[Figure 15]**, overperforming departments include Hauts-de-Seine (305 observed, 148.9 expected), Corse-du-Sud and Haute-Corse (36 and 31 observed, 15.7 and 19.1 expected) and Meurthe-et-Moselle (112 observed, 72.1 expected). The close-knit power network of Corse and the rich industrial legacy of Meurthe-et-Moselle help contextualize these results. The fact that Paris is not among the overperformers highlights that this department's elite production is consistent with what our explanatory variables predict. Underperformers include Seine-Saint-Denis (64 observed, 110.4 expected), Orne (18 observed, 33.4 expected), Essonne, Aube and Seine-et-Marne. For the executives model, Hauts-de-Seine is an especially pronounced outlier: 100 executives were observed, when our model was only expecting 14.7 individuals.

**Figure 15: Departmental plot of observed values, global cohort**
<p align="center">
  <img src=analysis/out/regression_multi_departments.png width="600">
</p>

At the city scale, analysing 34,868 French cities at once reveals to be challenging: they share highly different socio-economic situation, and uneven elite production. There is a huge number of small municipalities that have no secondary schools, no preparatory classes, and few managers and intellectual professions. In fact, only 2,232 cities produced an elite, and only a hundred of them produced more than 10. These highly concentrated origins mask the statistical relationships that we observed at the departmental level. To ensure that socio-economic variables are meaningful along elite production, we must therefore compare like with like. Hence, we begin by analysing the first quantile of cities in terms of our demographic index.

For this Q1 set of 3,468 cities  **[Appendix 3]**, we use our demographic exposure index, the rate of tertiary employment, the number of high schools (general path), and the number of preparatory classes. We obtain a 0.619 R-squared, with meaningful variables ($***$ and $*$). The coefficient of demographic exposure is only 0.43, that of tertiary is 0.08, that of high schools is 0.26 and that of preparatory classes is 0.18. Overperforming cities **[Figure 16]** include Boulogne-Billancourt (87 observed, 10.6 expected) and Neuilly-sur-Seine (105 observed, 13.3 expected). We observed highly similar results when using the *Paris merged* dataset. 

**Figure 16: Departmental plot of observed values, global cohort**
<p align="center">
  <img src=analysis/out/regression_multi_city.png width="600">
</p>

For the remaining cities of the dataset, regardless of how we arrange our explanatory variables, our model never explains more than 20% of the observations. This is significant in itself: it seems that in small towns, the emergence of a leader is unexplained by our variables, or is linked to factors not captured by INSEE’s socio-economic metrics, such as a particular family or an exceptional teacher. The statistical laws governing geographical wealth and educational infrastructure only apply once a certain critical mass is reached, as shown with our Q1 model.
<br><br>

## Conclusion

### Results

Our study confirms that while France is an ["indivisible, secular, democratic and social Republic"](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000019240997/2022-01-22), the origin of its elites is geographically concentrated. The distribution of publicly visible French elites is amassed in urban and economically dense areas. Prominent figures originating from Paris highlight the significance of geographical and social factors such as the concentration of *Grandes Écoles*, political institutions, [symbolic, social and cultural capital](https://books.openedition.org/psorbonne/868) of the capital. We observe a strong overrepresentation of affluent Paris suburbs such as the Hauts-de-Seine department, and more specifically cities such as Neuilly-sur-Seine and Boulogne-Billancourt. Underperforming departments include Seine-Saint-Denis, Essonne and Orne among others. This concentration of elites origin is largely explained by demographic dynamics and educational infrastructure at macro territorial levels, but become weakly predictable for municipalities producing few elites, suggesting the presence of non-structural or idiosyncratic mechanisms in elite production for smaller localities.
<br><br>

### Limits
Our study has a number of limitations. First, 44.7% of the biographical data we analyse (all categories except for Parliament members) is fetched from Wikipedia. This part of the dataset is by definition biased: instead of reflecting pure elite origins, it induces a significant notoriety effect. We do not focus on elites in the broadest sense, but rather on elites having a visible digital footprint. Hence, our research question might be closer to "*What is the geographical origin of French elites referenced on Wikipedia?*" for almost half of the individuals we study. 

Secondly, due to our imperfect scraping methods, our dataset is likely missing a significant number of individuals. We are for example missing the place of birth of over a thousand National Assembly members, and we cannot draw any meaningful conclusions from incomplete data. 

Third, studying the *place of birth* is a fragile proxy that reflects administrative and infrastructural constraints biased towards major cities and urban areas: the presence of maternity wards and hospitals. The data we analyse is influenced by infrastructures and administrative geography. However, the place of birth remains a clear and recorded set of administrative information that is easy to analyse. It would be almost impossible to identify the exact city in which these individuals were born, or would further reinforce the notoriety bias by retaining only extremely popular individuals whose biographical background is clearly documented.
<br><br>

## Appendix

**Appendix 1: Regional linear regression | log(global) ~ log(expo_demog) + log(prepa_rate)**
```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:                 global   R-squared:                       0.966
Model:                            OLS   Adj. R-squared:                  0.962
Method:                 Least Squares   F-statistic:                     201.1
Date:                Thu, 02 Apr 2026   Prob (F-statistic):           4.88e-11
Time:                        12:23:52   Log-Likelihood:                 2.1800
No. Observations:                  17   AIC:                             1.640
Df Residuals:                      14   BIC:                             4.140
Df Model:                           2                                         
Covariance Type:            nonrobust                                         
==============================================================================
                 coef    std err          t      P>|t|      [0.025      0.975]
------------------------------------------------------------------------------
const         -6.6146      0.720     -9.187      0.000      -8.159      -5.070
expo_demog     0.8324      0.046     18.117      0.000       0.734       0.931
prepa_rate     2.6457      1.067      2.479      0.026       0.357       4.934
==============================================================================
Omnibus:                        2.801   Durbin-Watson:                   1.599
Prob(Omnibus):                  0.247   Jarque-Bera (JB):                1.136
Skew:                           0.579   Prob(JB):                        0.567
Kurtosis:                       3.511   Cond. No.                         298.
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
```

**Appendix 2: Departmental linear regression | log(global) ~ log(expo_demog) + log(prepa_rate) + log(cadres_and_pro) + log(poverty_rate)**
```                            OLS Regression Results                            
==============================================================================
Dep. Variable:                 global   R-squared:                       0.838
Model:                            OLS   Adj. R-squared:                  0.831
Method:                 Least Squares   F-statistic:                     122.6
Date:                Thu, 02 Apr 2026   Prob (F-statistic):           1.27e-36
Time:                        12:23:52   Log-Likelihood:                -5.9039
No. Observations:                 100   AIC:                             21.81
Df Residuals:                      95   BIC:                             34.83
Df Model:                           4                                         
Covariance Type:            nonrobust                                         
==================================================================================
                     coef    std err          t      P>|t|      [0.025      0.975]
----------------------------------------------------------------------------------
const             -7.4193      0.790     -9.391      0.000      -8.988      -5.851
expo_demog         0.7798      0.047     16.568      0.000       0.686       0.873
prepa_rate         2.0663      0.484      4.273      0.000       1.106       3.026
cadres_and_pro     0.2504      0.081      3.103      0.003       0.090       0.411
poverty_rate       0.2547      0.115      2.207      0.030       0.026       0.484
==============================================================================
Omnibus:                        3.209   Durbin-Watson:                   2.266
Prob(Omnibus):                  0.201   Jarque-Bera (JB):                3.262
Skew:                           0.091   Prob(JB):                        0.196
Kurtosis:                       3.866   Cond. No.                         425.
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
```

**Appendix 3: City linear regression | log(global) ~ log(expo_demog) + log(tertiaire) + log(lycees_gt) + log(prepa_count)**
```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:                 global   R-squared:                       0.619
Model:                            OLS   Adj. R-squared:                  0.619
Method:                 Least Squares   F-statistic:                     1409.
Date:                Thu, 02 Apr 2026   Prob (F-statistic):               0.00
Time:                        12:23:53   Log-Likelihood:                -2030.6
No. Observations:                3468   AIC:                             4071.
Df Residuals:                    3463   BIC:                             4102.
Df Model:                           4                                         
Covariance Type:            nonrobust                                         
===============================================================================
                  coef    std err          t      P>|t|      [0.025      0.975]
-------------------------------------------------------------------------------
const          -3.6789      0.179    -20.588      0.000      -4.029      -3.329
expo_demog      0.4371      0.013     33.444      0.000       0.411       0.463
tertiaire       0.0859      0.040      2.148      0.032       0.008       0.164
lycees_gt       0.2665      0.022     11.919      0.000       0.223       0.310
prepa_count     0.1881      0.017     10.968      0.000       0.154       0.222
==============================================================================
Omnibus:                      243.106   Durbin-Watson:                   1.946
Prob(Omnibus):                  0.000   Jarque-Bera (JB):              428.287
Skew:                           0.517   Prob(JB):                     9.97e-94
Kurtosis:                       4.376   Cond. No.                         234.
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
```
