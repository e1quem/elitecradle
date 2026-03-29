from matplotlib.ticker import MaxNLocator
from shapely.geometry import Point
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import statsmodels.api as sm
import geopandas as gpd
from scipy import stats
import seaborn as sns
import pandas as pd
import numpy as np
import warnings
import os

warnings.filterwarnings('ignore')

# Clean df
df = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/fetch/merging/out/merged_clean.csv", sep=None, engine='python')

# Demographic and economic sources
df_city   = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/processed/analysis_city.csv",       sep=None, engine='python')
df_dept   = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/processed/analysis_department.csv", sep=None, engine='python')
df_region = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/processed/analysis_region.csv",     sep=None, engine='python')

# Creating df_city_merged : summing all Paris personalities in the Paris line
paris_mask = df_city['pob'].str.match(r'^Paris \d+', na=False)
count_cols = ['global', 'politics', 'college_de_france', 'parliament', 'executive', 'minister', 'president', 'senat']
paris_arr_sum = df_city[paris_mask][count_cols].sum()
df_city_merged = df_city[~paris_mask].copy()
paris_idx = df_city_merged[df_city_merged['pob'] == 'Paris'].index
df_city_merged.loc[paris_idx, count_cols] += paris_arr_sum.values

# Paris arrondissement only
df_arr = df_city[paris_mask].copy()

df_cities_q1 = df_city[df_city['expo_demog'] > df_city['expo_demog'].quantile(0.90)]
df_cities_merged_q1 = df_city_merged[df_city_merged['expo_demog'] > df_city_merged['expo_demog'].quantile(0.90)]
df_cities_else = df_city[df_city['expo_demog'] < df_city['expo_demog'].quantile(0.90)]

# Groups on which we iterate
GROUPS = ['global']#, 'politics', 'college_de_france', 'executive']

# Variables for each level
ECO_ARR = ['expo_demog', 'lycees_pro', 'lycees_gt', 'lycees', 'edu', 'prepa', 'prepa_count', 'median']
ECO_CITY = ['expo_demog', 'activity_rate', 'lycees_pro', 'lycees_gt', 'lycees', 'edu', 'prepa', 'prepa_count', 'cadres', 'median', 'tertiaire']
ECO_DEPT = ['expo_demog', 'activity_rate', 'colleges', 'lycees_pro', 'lycees_gt', 'lycees', 'second_degre', 'prepa_count', 'cadres_and_pro', 'median', 'poverty_rate', 'tertiaire']
ECO_REGION = ['expo_demog', 'activity_rate', 'colleges', 'lycees_pro', 'lycees_gt', 'lycees', 'second_degre', 'prepa_count', 'cadres_and_pro', 'median', 'poverty_rate', 'tertiaire']


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

#def print_concentration(df, id_col, level_name, groups):
#    print(f"\n  \033[1mCONCENTRATION — {level_name.upper()}\033[0m")
#    for g in groups:
#        if g not in df.columns:
#            continue
#        s = df[g].dropna().sort_values(ascending=False)
#        total = s.sum()
#        if total == 0:
#            continue
#        top1_pct  = s.iloc[0] / total * 100 if len(s) >= 1 else 0
#        top3_pct  = s.iloc[:3].sum() / total * 100 if len(s) >= 3 else 0
#        top5_pct  = s.iloc[:5].sum() / total * 100 if len(s) >= 5 else 0
#        top10_pct = s.iloc[:10].sum() / total * 100 if len(s) >= 10 else 0
#
#        print(f"\n  \033[1m{g}\033[0m  total={int(total)}, n entities={len(s)}")
#        print(f"    Top 3  : {top3_pct:.1f}%")
#        print(f"    Top 5  : {top5_pct:.1f}%")
#        print(f"    Top 10 : {top10_pct:.1f}%")
#
#print_concentration(df_region, 'region', 'Region',      GROUPS)
#print_concentration(df_dept,   'dept',   'Department', GROUPS)
#print_concentration(df_city,   'pob',    'City',       GROUPS)
#print_concentration(df_city_merged, 'pob', 'City - Paris merged', GROUPS)
#print_concentration(df_arr, 'pob', 'Arrondissements', GROUPS)
#
#
## BAR CHARTS
POLITICS_STACKS = ['parliament', 'senat', 'minister', 'president']
GLOBAL_STACKS = ['parliament', 'senat', 'minister', 'executive', 'college_de_france', 'president']
OUTPUT_DIR = "/Users/eyquem/Desktop/LeadersMap/analysis/out"
REG_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "regressions")
#plt.rcParams['font.family'] = 'sans-serif'
#plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial']
#
#def apply_d3_style(ax, title, is_stacked=False):
#    for spine in ax.spines.values():
#        spine.set_visible(False)
#    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
#    ax.tick_params(axis='both', which='major', labelsize=9, colors='#444444')
#    ax.set_title(title, loc='left', pad=20, color='#222222')
#
## Simple bar chart for college_de_france and executive
#def plot_simple_bar(ax, df, id_col, group, title):
#    total_n = int(df[group].sum())
#    title = f"{title} (n = {total_n})"
#    top_df = df.dropna(subset=[group]).sort_values(group, ascending=False).head(10)
#    x_labels = top_df[id_col].astype(str).tolist()
#    y_values = top_df[group].values
#    x_pos = np.arange(len(x_labels))
#    ax.bar(x_pos, y_values, color='steelblue', width=0.95)
#    ax.set_xticks(x_pos)
#    ax.set_xticklabels(x_labels, rotation=45, ha='right')
#    ax.set_xlim(-0.5, len(x_labels) - 0.5)
#    
#    apply_d3_style(ax, title)
#
## Stacked bar chart for global and political
#def plot_stacked_bar(ax, df, id_col, group_total, stack_cols, title):
#    total_n = int(df[group_total].sum())
#    title = f"{title} (n = {total_n})"
#    top_df = df.dropna(subset=[group_total]).sort_values(group_total, ascending=False).head(10)
#    x_labels = top_df[id_col].astype(str).tolist()
#    x_pos = np.arange(len(x_labels))
#
#    valid_cols = [c for c in stack_cols if c in df.columns]
#    if not valid_cols:
#        ax.bar(x_pos, top_df[group_total].values, color='#abdda4', width=0.95)
#    else:
#        bottom = np.zeros(len(top_df))
#        for col in valid_cols:
#            values = top_df[col].fillna(0).values
#        cmap = plt.get_cmap('Spectral')
#        colors = cmap(np.linspace(0.1, 0.9, len(valid_cols)))
#        
#        for i, col in enumerate(valid_cols):
#            values = top_df[col].fillna(0).values
#            ax.bar(x_pos, values, bottom=bottom, label=col.capitalize(), color=colors[i], width=0.95)
#            bottom += values
#            
#        ax.legend(frameon=False, fontsize='small', loc='upper right', prop={'family': 'sans-serif', 'size': 9})
#
#    ax.set_xticks(x_pos)
#    ax.set_xticklabels(x_labels, rotation=45, ha='right')
#    ax.set_xlim(-0.5, len(x_labels) - 0.5)
#    apply_d3_style(ax, title, is_stacked=True)
#
#def export_level_charts(df, id_col, level_name):
#    fig, axes = plt.subplots(1, 4, figsize=(24, 6))
#    n_entities = len(df)
#    display_name = level_name.replace('_', ' ')
#
#    fig.suptitle(f"{display_name} ({n_entities} entities)", fontsize=14, fontname='Helvetica')
#
#    plot_stacked_bar(axes[0], df, id_col, 'global', GLOBAL_STACKS, 'Global')
#    plot_stacked_bar(axes[1], df, id_col, 'politics', POLITICS_STACKS, 'Political')
#    plot_simple_bar(axes[2], df, id_col, 'college_de_france', 'Collège de France')
#    plot_simple_bar(axes[3], df, id_col, 'executive', 'Executives')
#    plt.tight_layout()
#    
#    filename = os.path.join(OUTPUT_DIR, f"top_{level_name.lower().replace(' ', '_')}.png")
#    plt.savefig(filename, dpi=300, bbox_inches='tight', transparent=False, facecolor='white')
#    plt.close()
#
#levels_to_export = [
#    (df_region,      'region', 'Region'),
#    (df_dept,        'dept',   'Department'),
#    (df_city_merged, 'pob',    'City_Merged'),
#    (df_city,        'pob',    'City'),
#    (df_arr,         'pob',    'Arrondissements')]
#
#for df_level, id_col, level_name in levels_to_export:
#    export_level_charts(df_level, id_col, level_name)
#
#
## BUBBLE MAPS
#MAP_CACHE = os.path.join(OUTPUT_DIR, "france_regions.geojson")
#GROUP_COLORS = {"Global": "#A52A2A", "Political": "#E63946", "Collège de France": "#6D597A", "Executives": "#F4A261"}
#SCALE = 1.2 
#MAX_BUBBLE_SIZE = 2000 
#GLOBAL_MAX_POP = df.groupby(['lat', 'lon']).size().max()
#
#def get_metropolitan_france():
#    if not os.path.exists(MAP_CACHE):
#        import requests
#        url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson"
#        r = requests.get(url)
#        with open(MAP_CACHE, 'wb') as f: f.write(r.content)
#    france = gpd.read_file(MAP_CACHE)
#    # Need to figure out a clean render of DOMs (without Mayotte, not included in INSEE data)
#    france = france[~france['nom'].isin(['Guadeloupe', 'Martinique', 'Guyane', 'La Réunion'])]
#    return france
#
#def prepare_bubble_data(df_subset):
#    bubbles = df_subset.groupby(['lat', 'lon']).size().reset_index(name='population')
#    # Filtering coordinates
#    bubbles = bubbles[(bubbles['lon'] > -5.5) & (bubbles['lon'] < 10) & (bubbles['lat'] > 41) & (bubbles['lat'] < 52)]
#    gdf = gpd.GeoDataFrame(bubbles, geometry=gpd.points_from_xy(bubbles.lon, bubbles.lat))
#    return gdf.sort_values('population', ascending=False)
#
#france_geo = get_metropolitan_france()
#
#configs = [
#    ("Global", df),
#    ("Political", df[df['tag'].isin(['parliament', 'senat', 'president', 'minister'])]),
#    ("Collège de France", df[df['tag'] == 'college_de_france']),
#    ("Executives", df[df['tag'] == 'executive']),]
#
#fig, axes = plt.subplots(1, 4, figsize=(20, 6), facecolor='white')
#
#for i, (name, data_subset) in enumerate(configs):
#    ax = axes[i]
#    for spine in ax.spines.values(): spine.set_visible(False)
#    france_geo.plot(ax=ax, color='#eeeeee', edgecolor='white', linewidth=0.7)
#    gdf_bubbles = prepare_bubble_data(data_subset)
#    total_n = len(data_subset)
#    
#    if not gdf_bubbles.empty:
#        ratios = (gdf_bubbles['population'] / GLOBAL_MAX_POP) ** SCALE
#        sizes = ratios * MAX_BUBBLE_SIZE
#        ax.scatter(gdf_bubbles.geometry.x, gdf_bubbles.geometry.y, s=sizes, color=GROUP_COLORS[name], alpha=0.5, edgecolors='white', linewidths=0.5, zorder=3)
#    
#    ax.set_title(f"{name} (n = {total_n})", x=0.06, loc='left', pad=10, fontsize=12, color='#222222', fontweight='bold')
#    ax.set_xlim(-5.5, 10)
#    ax.set_ylim(41, 51.5)
#    ax.axis('off')
#
#fig.suptitle(f"Bubble Map of Personnalities in Mainland France", fontsize=14, fontname='Helvetica')
#plt.tight_layout(rect=[0, 0.03, 1, 0.97])
#plt.savefig(os.path.join(OUTPUT_DIR, "bubble_map.png"), dpi=300, bbox_inches='tight')


# CHOROPLETH MAPS
#GEO_URLS = {
#    'region': "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson",
#    'department': "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson",
#    'city': "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson",
#    'arrondissements': "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson"}
#
#def export_choropleths(df_data, id_col, level_name, geo_url):
#    print(f"Generating choropleth map: {level_name}...")
#
#    # Cache
#    local_filename = os.path.join(OUTPUT_DIR, f"cache_{level_name.lower()}.geojson")
#
#    if os.path.exists(local_filename):
#        print(f"  Using cached file: {local_filename}")
#        gdf_geo = gpd.read_file(local_filename)
#    else:
#        print(f"  Downloading from: {geo_url}")
#        try:
#            gdf_geo = gpd.read_file(geo_url)
#            gdf_geo.to_file(local_filename, driver='GeoJSON')
#        except Exception as e:
#            print(f"  Error downloading: {e}")
#            return
#    
#    # Adaptative size
#    h = 5 if level_name == 'Arrondissements' else 7
#    fig, axes = plt.subplots(1, 4, figsize=(24, h), facecolor='white')
#
#    gdf_geo = gpd.read_file(geo_url)
#    
#    if level_name == 'Region':
#        geo_key = 'nom'
#    elif level_name == 'Department':
#        geo_key = 'code'
#        gdf_geo['code'] = gdf_geo['code'].astype(str).str.zfill(2)
#        df_data[id_col] = df_data[id_col].astype(str).str.zfill(2)
#    elif level_name == 'City':
#        geo_key = 'nom'
#        if 'code' in gdf_geo.columns:
#            gdf_geo = gdf_geo[~gdf_geo['code'].str.startswith('97', na=False)]
#    elif level_name == 'Arrondissements':
#        if 'c_ar' in gdf_geo.columns:
#            gdf_geo['match_key'] = gdf_geo['c_ar'].apply(lambda x: f"Paris {str(x)[-2:]}")
#        elif 'l_ar' in gdf_geo.columns:
#            gdf_geo['match_key'] = gdf_geo['l_ar'].str.extract(r'(\d+)').astype(str).str.zfill(2).apply(lambda x: f"Paris {x}")
#        geo_key = 'match_key'
#
#    gdf_merged = gdf_geo.merge(df_data, left_on=geo_key, right_on=id_col, how='left')
#    
#    groups = [
#        ('global', 'Global', '#A52A2A'),
#        ('politics', 'Political', '#E63946'),
#        ('college_de_france', 'Collège de France', '#6D597A'),
#        ('executive', 'Executives', '#F4A261')]
#    
#    for i, (col, title, base_color) in enumerate(groups):
#        ax = axes[i]
#        gdf_merged[col] = gdf_merged[col].fillna(0)
#
#        render_col = f"{col}_log"
#        # Log scale, otherwise Paris is too intense
#        gdf_merged[render_col] = np.log1p(gdf_merged[col])
#        cmap = mcolors.LinearSegmentedColormap.from_list("custom", ["#eeeeee", base_color])
#        gdf_merged.plot(column=render_col, cmap=cmap, linewidth=0.1 if level_name == 'City' else 0.6, edgecolor='white',ax=ax)
#        
#        # Arrondissements zoom
#        if level_name == 'Arrondissements':
#                ax.set_xlim(2.22, 2.47)
#                ax.set_ylim(48.81, 48.91)
#        
#        ax.axis('off')
#        total_n = int(df_data[col].sum())
#        ax.set_title(f"{title} (n = {total_n})", loc='left', x=0.06, fontsize=12, fontweight='bold', color='#222222')
#
#    fig.suptitle(f"Choropleth Maps by {level_name}",fontsize=14, fontname='Helvetica', y=0.96)
#    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
#    
#    filename = os.path.join(OUTPUT_DIR, f"choropleth_{level_name.lower()}.png")
#    plt.savefig(filename, dpi=600, bbox_inches='tight')
#    plt.close()
#
#export_choropleths(df_region, 'region', 'Region', GEO_URLS['region'])
#export_choropleths(df_dept, 'dept_num', 'Department', GEO_URLS['department'])
#export_choropleths(df_city_merged, 'pob', 'City', GEO_URLS['city'])
#export_choropleths(df_arr, 'pob', 'Arrondissements', GEO_URLS['arrondissements'])


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

## CORRELATION HEATMAP
#def heatmap_correlation(df, level_name, groups, eco_vars):
#    cols = [c for c in groups + eco_vars if c in df.columns]
#    corr = df[cols].apply(pd.to_numeric, errors='coerce').corr(method='pearson').round(3)
#    
#    fig, ax = plt.subplots(figsize=(7, 5))
#    sns.heatmap(
#        corr,
#        ax=ax,
#        cmap='RdBu',
#        vmin=-1, vmax=1, center=0,
#        annot=True, fmt='.2f', annot_kws={'size': 6},
#        linewidths=0.5, linecolor='white',
#        cbar_kws={'ticks': [-1, 0, 1]},
#    )
#    ax.set_title(f'{level_name} Correlation Matrix', pad=12, fontname='Helvetica')
#    ax.set_xticklabels(ax.get_xticklabels(), fontsize=9, fontname='Helvetica')
#    ax.set_yticklabels(ax.get_yticklabels(), fontsize=9, fontname='Helvetica')
#    ax.tick_params(axis='both', length=0)
#
#    plt.tight_layout()
#    path = f"/Users/eyquem/Desktop/LeadersMap/analysis/out/correlation_{level_name.lower().replace(' ', '_')}.png"
#    fig.savefig(path, dpi=300, bbox_inches='tight')
#    plt.close()
#    print(f"  Saved: {path}")
#
#heatmap_correlation(df_region,      'Region',              GROUPS, ECO_REGION)
#heatmap_correlation(df_dept,        'Department',          GROUPS, ECO_DEPT)
#heatmap_correlation(df_city,        'City',                GROUPS, ECO_CITY)
#heatmap_correlation(df_city_merged, 'City - Paris merged', GROUPS, ECO_CITY)
#heatmap_correlation(df_arr,         'Arrondissements',     GROUPS, ECO_ARR)
#
#
## REGRESSIONS
#def plot_regression_outliers(df, x_col, y_col, level_name, id_col):
#    cols_to_keep = [x_col, y_col, id_col]
#    plot_df = df[cols_to_keep].copy()
#    
#    plot_df['x_val'] = pd.to_numeric(plot_df[x_col], errors='coerce')
#    plot_df['y_val'] = pd.to_numeric(plot_df[y_col], errors='coerce')
#    plot_df['x_log'] = np.log1p(plot_df['x_val'])
#    plot_df['y_log'] = np.log1p(plot_df['y_val'])
#    plot_df = plot_df.dropna(subset=['x_log', 'y_log'])
#
#    slope, intercept, r_value, p_value, std_err = stats.linregress(plot_df['x_log'], plot_df['y_log'])
#    plot_df['resid'] = plot_df['y_log'] - (slope * plot_df['x_log'] + intercept)
#    
#    plt.figure(figsize=(12, 8), facecolor='white')
#    limit = max(abs(plot_df['resid'].min()), abs(plot_df['resid'].max())) * 0.7
#    scatter = plt.scatter(plot_df['x_log'], plot_df['y_log'], c=plot_df['resid'], cmap='RdBu', alpha=0.8, edgecolors='none', s=50, vmin=-limit, vmax=limit)
#    
#    # Regression line
#    x_range = np.array([plot_df['x_log'].min(), plot_df['x_log'].max()])
#    plt.plot(x_range, slope * x_range + intercept, color='#333333', linestyle='--', linewidth=0.8, alpha=0.8, label=f'R2 = {r_value**2:.2f}, p-value = {p_value:.3f}')
#
#    # 4. Labels des 5 plus gros Over/Under performers
#    outliers = plot_df.sort_values('resid', ascending=False)
#    top_labels = outliers.head(5)
#    bottom_labels = outliers.tail(5)
#    
#    for _, row in pd.concat([top_labels, bottom_labels]).iterrows():
#        plt.text(row['x_log'], row['y_log'] + 0.06, str(row[id_col]), 
#                 fontsize=8, fontweight='bold', ha='center', va='bottom')
#        
#    ax = plt.gca()
#    ax.spines['top'].set_visible(False)
#    ax.spines['right'].set_visible(False)
#
#    plt.xlabel(f'log({x_col})', fontsize=10)
#    plt.ylabel(f'log({y_col})', fontsize=10)
#    plt.title(f'{level_name} : {y_col} vs {x_col}', fontsize=12, fontname='Helvetica')
#    plt.grid(False)
#
#    safe_y = y_col.replace(' ', '_')
#    safe_x = x_col.replace(' ', '_')
#    filename = os.path.join(OUTPUT_DIR, f"scatter_{level_name.lower()}_{safe_y}_vs_{safe_x}.png")
#    plt.savefig(filename, dpi=300, bbox_inches='tight')
#    plt.close()
#
#plot_regression_outliers(df_city, 'expo_demog', 'global', 'City', 'pob')
#plot_regression_outliers(df_city_merged, 'expo_demog', 'politics', 'City_Paris_Merged', 'pob')
#plot_regression_outliers(df_dept, 'expo_demog', 'global', 'Department', 'dept')
#plot_regression_outliers(df_dept, 'median', 'global', 'Department', 'dept')


VAR_ARR = ['expo_demog', 'median', 'prepa_count']
VAR_CITIES_ELSE = ['expo_demog', 'cadres', 'edu', 'prepa']
VAR_CITY = ['expo_demog', 'tertiaire', 'lycees_gt', 'prepa_count']
VAR_DEPT = ['expo_demog', 'prepa_rate', 'cadres_and_pro', 'poverty_rate']
VAR_REGION = ['expo_demog', 'prepa_rate']


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
                label = f"log({g}) ~ {' + '.join([f'log({v})' for v in available_eco])}" if log_transform else f"{g} ~ {' + '.join(available_eco)}"
                print(f"\n  \033[1m{level_name} - Multivariate: {label}  (n={mask.sum()})\033[0m")
                print(model.summary().tables[0])
                print(model.summary().tables[1])

                # Save
                summary_path = os.path.join(REG_OUTPUT_DIR, f"summary_{level_name}_{g}.txt")
                with open(summary_path, 'w') as f:
                    f.write(model.summary().as_text())
                
                # Residuals, expected VS observed
                log_fitted = model.predict(X)
                n_observed = np.expm1(y[mask])
                n_expected = np.expm1(log_fitted)

                res_df = pd.DataFrame({
                    'id': df.loc[mask, id_col],
                    'obs': n_observed,
                    'exp': n_expected,
                    'resid_log': model.resid})

                label = f"log({g}) ~ multivariate" if log_transform else f"{g} ~ multivariate"
                print(f"\n  \033[1m{level_name} - {label} (n={mask.sum()})\033[0m")

                print(f"\n  \033[1mOverperformers ({g}):\033[0m")
                over = res_df.sort_values('resid_log', ascending=False).head(5)
                for _, row in over.iterrows():
                    diff_abs = row['obs'] - row['exp']
                    diff_pct = (diff_abs / row['exp'] * 100) if row['exp'] > 0 else 0
                    print(f"    {str(row['id']):<25}  Expected: {row['exp']:>2.1f}     Observed: {int(row['obs']):>2}     Diff: {diff_abs:>+2.1f} ({diff_pct:>+2.1f}%)")

                print(f"  \033[1mUnderperformers ({g}):\033[0m")
                under = res_df.sort_values('resid_log', ascending=True).head(5)
                for _, row in under.iterrows():
                    diff_abs = row['obs'] - row['exp']
                    diff_pct = (diff_abs / row['exp'] * 100) if row['exp'] > 0 else 0
                    print(f"    {str(row['id']):<25}  Expected: {row['exp']:>5.1f}     Observed: {int(row['obs']):>3}     Diff: {diff_abs:>+5.1f} ({diff_pct:>+6.1f}%)")

run_regressions(df_region, 'region', 'Region', GROUPS, VAR_REGION) # bivariate because onnly 17 entities
run_regressions(df_dept, 'dept', 'Department', GROUPS, VAR_DEPT)
run_regressions(df_cities_else, 'pob', 'City', GROUPS, VAR_CITIES_ELSE)
run_regressions(df_cities_q1, 'pob', 'City', GROUPS, VAR_CITY)
run_regressions(df_cities_merged_q1, 'pob', 'City - Paris merged', GROUPS, VAR_CITY)
run_regressions(df_arr, 'pob', 'Arr.', GROUPS, VAR_ARR)
