from matplotlib.ticker import MaxNLocator
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats
import seaborn as sns
import pandas as pd
import numpy as np
import warnings
import os
import geopandas as gpd
from shapely.geometry import Point

warnings.filterwarnings('ignore')

# Clean df
df = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/interim/merged_clean.csv", sep=None, engine='python')

# Demographic and economic sources
df_city   = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/processed/analysis_city.csv",       sep=None, engine='python')
df_dept   = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/processed/analysis_department.csv", sep=None, engine='python')
df_region = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/processed/analysis_region.csv",     sep=None, engine='python')

# Creating df_city_merged : summing all Paris personalities in the Paris line
paris_mask = df_city['pob'].str.match(r'^Paris \d+', na=False)
count_cols = ['global', 'politics', 'college_de_france', 'depute', 'executive', 'ministre', 'president', 'senat']
paris_arr_sum = df_city[paris_mask][count_cols].sum()
df_city_merged = df_city[~paris_mask].copy()
paris_idx = df_city_merged[df_city_merged['pob'] == 'Paris'].index
df_city_merged.loc[paris_idx, count_cols] += paris_arr_sum.values

# Paris arrondissement only
df_arr = df_city[paris_mask].copy()

# Groups on which we iterate
GROUPS = ['global', 'politics', 'college_de_france', 'executive']

# Variables for each level
ECO_ARR = ['expo_demog', 'median']
ECO_CITY = ['expo_demog', 'median']
ECO_CITY_MERGED = ['expo_demog', 'median']
ECO_DEPT = ['expo_demog', 'median', 'poverty_rate']
ECO_REGION = ['expo_demog', 'median_euro', 'poverty_rate']

# Rankings and concentration

#def print_ranking(df, id_col, level_name, groups, top_n=10, show_bottom = False):
#    print(f"\n  \033[1mRANKING — {level_name.upper()}\033[0m")
#    for g in groups:
#        if g not in df.columns:
#            continue
#        sorted_df = df[[id_col, g]].dropna().sort_values(g, ascending=False)
#        total = sorted_df[g].sum()
#        print(f"\n  \033[1m{g}\033[0m : {int(total)}")
#        for i, (_, row) in enumerate(sorted_df.head(top_n).iterrows(), 1):
#            pct = row[g] / total * 100 if total > 0 else 0
#            print(f"  {i:<5} {str(row[id_col]):<35} {int(row[g]):>6}  {pct:>7.1f}%")
#        if show_bottom:
#            print(f"  ...")
#            bottom_df = sorted_df.tail(top_n)
#            total_rows = len(sorted_df)
#            for i, (_, row) in enumerate(bottom_df.iterrows(), 1):
#                rank = total_rows - top_n + i
#                pct = row[g] / total * 100 if total > 0 else 0
#                print(f"  {rank:<5} {str(row[id_col]):<35} {int(row[g]):>6}  {pct:>7.1f}%")
#
#print_ranking(df_region, id_col='region', level_name='Region',      groups=GROUPS, top_n=10, show_bottom = False)
#print_ranking(df_dept,   id_col='dept',   level_name='Department', groups=GROUPS, top_n=10, show_bottom = True)
#print_ranking(df_city,   id_col='pob',    level_name='City',       groups=GROUPS, top_n=10, show_bottom = False)
#print_ranking(df_city_merged,   id_col='pob',    level_name='City - Paris merged', groups=GROUPS, top_n=10, show_bottom = False)
#print_ranking(df_arr,   id_col='pob',    level_name='Arrondissements', groups=GROUPS, top_n=10, show_bottom = False)

def print_concentration(df, id_col, level_name, groups):
    print(f"\n  \033[1mCONCENTRATION — {level_name.upper()}\033[0m")
    for g in groups:
        if g not in df.columns:
            continue
        s = df[g].dropna().sort_values(ascending=False)
        total = s.sum()
        if total == 0:
            continue
        top1_pct  = s.iloc[0] / total * 100 if len(s) >= 1 else 0
        top3_pct  = s.iloc[:3].sum() / total * 100 if len(s) >= 3 else 0
        top5_pct  = s.iloc[:5].sum() / total * 100 if len(s) >= 5 else 0
        top10_pct = s.iloc[:10].sum() / total * 100 if len(s) >= 10 else 0

        print(f"\n  \033[1m{g}\033[0m  total={int(total)}, n entities={len(s)}")
        print(f"    Top 3  : {top3_pct:.1f}%")
        print(f"    Top 5  : {top5_pct:.1f}%")
        print(f"    Top 10 : {top10_pct:.1f}%")

print_concentration(df_region, 'region', 'Region',      GROUPS)
print_concentration(df_dept,   'dept',   'Department', GROUPS)
print_concentration(df_city,   'pob',    'City',       GROUPS)
print_concentration(df_city_merged, 'pob', 'City - Paris merged', GROUPS)
print_concentration(df_arr, 'pob', 'Arrondissements', GROUPS)

# Output
POLITICS_STACKS = ['depute', 'senat', 'ministre', 'president']
GLOBAL_STACKS = ['depute', 'senat', 'ministre', 'executive', 'college_de_france', 'president']
OUTPUT_DIR = "/Users/eyquem/Desktop/LeadersMap/analysis/outputs"
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial']

# Style
def apply_d3_style(ax, title, is_stacked=False):
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.tick_params(axis='both', which='major', labelsize=9, colors='#444444')
    ax.set_title(title, loc='left', pad=20, color='#222222')

# Simple bar chart for college_de_france and executive
def plot_simple_bar(ax, df, id_col, group, title):
    total_n = int(df[group].sum())
    title = f"{title} (n = {total_n})"
    top_df = df.dropna(subset=[group]).sort_values(group, ascending=False).head(10)
    x_labels = top_df[id_col].astype(str).tolist()
    y_values = top_df[group].values
    x_pos = np.arange(len(x_labels))

    ax.bar(x_pos, y_values, color='steelblue', width=0.95)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.set_xlim(-0.5, len(x_labels) - 0.5)
    
    apply_d3_style(ax, title)

# Stacked bar chart for global and political
def plot_stacked_bar(ax, df, id_col, group_total, stack_cols, title):
    total_n = int(df[group_total].sum())
    title = f"{title} (n = {total_n})"

    top_df = df.dropna(subset=[group_total]).sort_values(group_total, ascending=False).head(10)
    
    x_labels = top_df[id_col].astype(str).tolist()
    x_pos = np.arange(len(x_labels))
    
    valid_cols = [c for c in stack_cols if c in df.columns]
    
    if not valid_cols:
        ax.bar(x_pos, top_df[group_total].values, color='#abdda4', width=0.95)
    else:
        bottom = np.zeros(len(top_df))
        for col in valid_cols:
            values = top_df[col].fillna(0).values
        cmap = plt.get_cmap('Spectral')
        colors = cmap(np.linspace(0.1, 0.9, len(valid_cols)))
        
        for i, col in enumerate(valid_cols):
            values = top_df[col].fillna(0).values
            ax.bar(x_pos, values, bottom=bottom, label=col.capitalize(), color=colors[i], width=0.95)
            bottom += values
            
        ax.legend(frameon=False, fontsize='small', loc='upper right', prop={'family': 'sans-serif', 'size': 9})

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.set_xlim(-0.5, len(x_labels) - 0.5)
    apply_d3_style(ax, title, is_stacked=True)

def export_level_charts(df, id_col, level_name):
    fig, axes = plt.subplots(1, 4, figsize=(24, 6))
    n_entities = len(df)
    display_name = level_name.replace('_', ' ')

    fig.suptitle(f"{display_name} ({n_entities} entities)", fontsize=14, fontname='Helvetica')

    plot_stacked_bar(axes[0], df, id_col, 'global', GLOBAL_STACKS, 'Global')
    plot_stacked_bar(axes[1], df, id_col, 'politics', POLITICS_STACKS, 'Political')
    plot_simple_bar(axes[2], df, id_col, 'college_de_france', 'Collège de France')
    plot_simple_bar(axes[3], df, id_col, 'executive', 'Executives')
    plt.tight_layout()
    
    filename = os.path.join(OUTPUT_DIR, f"top10_{level_name.lower().replace(' ', '_')}.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight', transparent=False, facecolor='white')
    plt.close()

levels_to_export = [
    (df_region,      'region', 'Region'),
    (df_dept,        'dept',   'Department'),
    (df_city_merged, 'pob',    'City_Merged'),
    (df_city,        'pob',    'City'),
    (df_arr,         'pob',    'Arrondissements')
]

for df_level, id_col, level_name in levels_to_export:
    export_level_charts(df_level, id_col, level_name)


# Plotting coordinates on map
MAP_CACHE = os.path.join(OUTPUT_DIR, "france_regions.geojson")

GROUP_COLORS = {
    "Global": "#A52A2A",
    "Political": "#E63946",
    "Collège de France": "#6D597A",
    "Executives": "#F4A261"
    
}

SCALE = 1.2 
MAX_BUBBLE_SIZE = 2000 
GLOBAL_MAX_POP = df.groupby(['lat', 'lon']).size().max()

def get_metropolitan_france():
    if not os.path.exists(MAP_CACHE):
        import requests
        url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson"
        r = requests.get(url)
        with open(MAP_CACHE, 'wb') as f: f.write(r.content)
    france = gpd.read_file(MAP_CACHE)
    # Need to figure out a clean render of DOMs (without Mayotte, not included in INSEE data)
    france = france[~france['nom'].isin(['Guadeloupe', 'Martinique', 'Guyane', 'La Réunion'])]
    return france

def prepare_bubble_data(df_subset):
    bubbles = df_subset.groupby(['lat', 'lon']).size().reset_index(name='population')
    # Filtering
    bubbles = bubbles[(bubbles['lon'] > -5.5) & (bubbles['lon'] < 10) & 
                     (bubbles['lat'] > 41) & (bubbles['lat'] < 52)]
    gdf = gpd.GeoDataFrame(bubbles, geometry=gpd.points_from_xy(bubbles.lon, bubbles.lat))
    return gdf.sort_values('population', ascending=False)

france_geo = get_metropolitan_france()

configs = [
    ("Global", df),
    ("Political", df[df['tag'].isin(['depute', 'senat', 'president', 'ministre'])]),
    ("Collège de France", df[df['tag'] == 'college_de_france']),
    ("Executives", df[df['tag'] == 'executive']),
]

fig, axes = plt.subplots(1, 4, figsize=(20, 6), facecolor='white')

for i, (name, data_subset) in enumerate(configs):
    ax = axes[i]
    for spine in ax.spines.values(): spine.set_visible(False)
    
    france_geo.plot(ax=ax, color='#eeeeee', edgecolor='white', linewidth=0.7)
    
    gdf_bubbles = prepare_bubble_data(data_subset)
    total_n = len(data_subset)
    
    if not gdf_bubbles.empty:
        ratios = (gdf_bubbles['population'] / GLOBAL_MAX_POP) ** SCALE
        sizes = ratios * MAX_BUBBLE_SIZE
        ax.scatter(gdf_bubbles.geometry.x, gdf_bubbles.geometry.y,
                   s=sizes, color=GROUP_COLORS[name],
                   alpha=0.5, edgecolors='white', linewidths=0.5, zorder=3)
    
    ax.set_title(f"{name} (n = {total_n})", x=0.06, loc='left', pad=10, 
                 fontsize=12, color='#222222', fontweight='bold')
    
    ax.set_xlim(-5.5, 10)
    ax.set_ylim(41, 51.5)
    ax.axis('off')

fig.suptitle(f"Bubble Map of Personnalities in Mainland France", fontsize=14, fontname='Helvetica')

plt.tight_layout(rect=[0, 0.03, 1, 0.97])
plt.savefig(os.path.join(OUTPUT_DIR, "bubble_map.png"), dpi=300, bbox_inches='tight')



# URLs des fonds de carte
GEO_URLS = {
    'region': "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson",
    'department': "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson",
    'city': "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson" # Attention : fichier lourd
}

def export_choropleths(df_data, id_col, level_name, geo_url):
    print(f"Génération : {level_name}...")
    
    # 1. Chargement du fond de carte
    gdf_geo = gpd.read_file(geo_url)
    
    # 2. Nettoyage et Préparation
    if level_name == 'Region':
        geo_key = 'nom'
    elif level_name == 'Department':
        geo_key = 'code'
        gdf_geo['code'] = gdf_geo['code'].astype(str).str.zfill(2)
        df_data[id_col] = df_data[id_col].astype(str).str.zfill(2)
    elif level_name in ['City', 'Arrondissements']:
        geo_key = 'nom'
        # FIX : Filtrage des DOM via le code INSEE (commence par 97)
        # On suppose que la colonne du code INSEE dans le GeoJSON s'appelle 'code'
        if 'code' in gdf_geo.columns:
            gdf_geo = gdf_geo[~gdf_geo['code'].str.startswith('97', na=False)]
        
        # Pour Paris, on restreint aux arrondissements
        if level_name == 'Arrondissements':
            gdf_geo = gdf_geo[gdf_geo['nom'].str.contains('Paris ', na=False) | (gdf_geo['nom'] == 'Paris')]

    # 3. Jointure
    gdf_merged = gdf_geo.merge(df_data, left_on=geo_key, right_on=id_col, how='left')
    
    # 4. Tracé
    fig, axes = plt.subplots(1, 4, figsize=(24, 7), facecolor='white')
    
    groups = [
        ('global', 'Global', '#A52A2A'),
        ('politics', 'Political', '#E63946'),
        ('college_de_france', 'Collège de France', '#6D597A'),
        ('executive', 'Executives', '#F4A261')
    ]
    
    for i, (col, title, base_color) in enumerate(groups):
        ax = axes[i]
        gdf_merged[col] = gdf_merged[col].fillna(0)
        
        cmap = mcolors.LinearSegmentedColormap.from_list("custom", ["#eeeeee", base_color])
        
        # Dessin
        gdf_merged.plot(
            column=col,
            cmap=cmap,
            linewidth=0.1 if level_name == 'City' else 0.6,
            edgecolor='white',
            ax=ax
        )
        
        # ZOOM automatique pour Paris
        if level_name == 'Arrondissements':
            # On définit les limites autour de Paris (approx lon 2.2 à 2.5, lat 48.8 à 48.9)
            ax.set_xlim(2.22, 2.48)
            ax.set_ylim(48.81, 48.91)
        
        ax.axis('off')
        total_n = int(df_data[col].sum())
        ax.set_title(f"{title} (n = {total_n})", loc='left', x=0.06, 
                     fontsize=12, fontweight='bold', color='#222222')

    fig.suptitle(f"Choropleth Maps by {level_name}", fontsize=15, fontweight='bold', y=0.96)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    filename = os.path.join(OUTPUT_DIR, f"choropleth_{level_name.lower()}.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()


# 1. Régions (Utilise les noms)
export_choropleths(df_region, 'region', 'Region', GEO_URLS['region'])

# Changer l'échelle, parce que là on ne voit rien d'autres que Paris
# 2. Départements (Utilise dept_num)
export_choropleths(df_dept, 'dept_num', 'Department', GEO_URLS['department'])

# 3. Communes (Utilise pob de df_city_merged pour inclure Paris agrégé)
export_choropleths(df_city_merged, 'pob', 'City', GEO_URLS['city'])

# Ne fonctionne pas
# 4. Paris Arrondissements (Utilise df_arr)
# Note: On filtre le fond de carte 'city' pour ne garder que Paris
export_choropleths(df_arr, 'pob', 'Arrondissements', GEO_URLS['city'])








#def print_correlation(df, level_name, groups, eco_vars):
#    print(f"\n\033[1m  CORRELATION — {level_name.upper()}\033[0m")
#    cols = [c for c in groups + eco_vars if c in df.columns]
#    corr = df[cols].corr(method='pearson').round(3)
#    print(corr.to_string())
#
#print_correlation(df_region, 'Region',      GROUPS, ECO_REGION)
#print_correlation(df_dept,   'Department', GROUPS, ECO_DEPT)
#print_correlation(df_city,   'City',       GROUPS, ECO_CITY)
#print_correlation(df_city_merged, 'City - Paris merged', GROUPS, ECO_CITY)
#print_correlation(df_arr, 'Arrondissements', GROUPS, ECO_CITY)

def heatmap_correlation(df, level_name, groups, eco_vars):
    cols = [c for c in groups + eco_vars if c in df.columns]
    corr = df[cols].apply(pd.to_numeric, errors='coerce').corr(method='pearson').round(3)
    
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(
        corr,
        ax=ax,
        cmap='RdBu',
        vmin=-1, vmax=1, center=0,
        annot=True, fmt='.2f', annot_kws={'size': 11},
        linewidths=0.5, linecolor='white',
        cbar_kws={'ticks': [-1, 0, 1]},
    )
    ax.set_title(f'{level_name} Correlation Matrix', pad=12, fontname='Helvetica')
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=10, fontname='Helvetica')
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=10, fontname='Helvetica')
    ax.tick_params(axis='both', length=0)

    plt.tight_layout()
    path = f"/Users/eyquem/Desktop/LeadersMap/analysis/outputs/correlation_{level_name.lower().replace(' ', '_')}.png"
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")

heatmap_correlation(df_region,      'Region',              GROUPS, ECO_REGION)
heatmap_correlation(df_dept,        'Department',          GROUPS, ECO_DEPT)
heatmap_correlation(df_city,        'City',                GROUPS, ECO_CITY)
heatmap_correlation(df_city_merged, 'City - Paris merged', GROUPS, ECO_CITY)
heatmap_correlation(df_arr,         'Arrondissements',     GROUPS, ECO_CITY)


# II. Regressions
# For each level : univariate (expo_demog, poverty_rate, median) then multivariate

# on transforme en logs
def run_regressions(df, id_col, level_name, groups, eco_vars, log_transform = True):
    print(f"\n\033[1m  REGRESSIONS — {level_name.upper()}\033[0m")
    for g in groups:
        if g not in df.columns:
            continue

        y_raw = pd.to_numeric(df[g], errors='coerce')
        y = np.log1p(y_raw) if log_transform else y_raw
        available_eco = [v for v in eco_vars if v in df.columns]

        # Multivariate regression
        if len(available_eco) >= 2:
            eco_df = df[available_eco].apply(pd.to_numeric, errors='coerce')
            if log_transform:
                eco_df = np.log1p(eco_df)
            mask = y.notna() & eco_df.notna().all(axis=1)
            if mask.sum() >= len(available_eco) + 1:
                X = sm.add_constant(eco_df[mask])
                model = sm.OLS(y[mask], X).fit()
                label = f"log({g}) ~ {' + '.join([f'log({v})' for v in available_eco])}" if log_transform \
                        else f"{g} ~ {' + '.join(available_eco)}"
                print(f"\n  \033[1m{level_name} - Multivariate: {label}  (n={mask.sum()})\033[0m")
                print(model.summary().tables[0])
                print(model.summary().tables[1])

            # Residuals
            residuals = model.resid
            ids = df.loc[mask.values, id_col].values
            resid_df = pd.DataFrame({'entity': ids, 'residual': residuals}).sort_values('residual', ascending=False)
            print(f"\n\033[2m  Overperformers:\033[0m")
            for _, row in resid_df.head(5).iterrows():
                print(f"    {str(row['entity']):<35}  residual={row['residual']:+.3f}  ({(np.expm1(row['residual'])*100):+.1f}%)")
            print(f"\033[2m  Underperformers:\033[0m")
            for _, row in resid_df.tail(5).iloc[::-1].iterrows():
                print(f"    {str(row['entity']):<35}  residual={row['residual']:+.3f}  ({(np.expm1(row['residual'])*100):+.1f}%)")

run_regressions(df_region, 'region', 'Region', GROUPS, ECO_REGION)
run_regressions(df_dept, 'dept', 'Department', GROUPS, ECO_DEPT)
run_regressions(df_city, 'pob', 'City', GROUPS, ECO_CITY)
run_regressions(df_city_merged, 'pob', 'City - Paris merged', GROUPS, ECO_CITY_MERGED)
run_regressions(df_arr, 'pob', 'Arr.', GROUPS, ECO_ARR)