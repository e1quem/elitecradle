import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import warnings
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns

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

# But : quelles sont les villes qui produisent le plus d'élites en france ? Les facteurs économiques (pauvreté, salaire médian) et démographiques (population) expliquent-ils la formation d'élites ?

# Les groupes de personnalités : on itère sur ces 4
# 1. Total
# 2. Politics
# 3. College_de_france
# 4. Executives

GROUPS = ['global', 'politics', 'college_de_france', 'executive']

# Variables for each level
ECO_ARR = ['expo_demog', 'median']
ECO_CITY = ['expo_demog', 'median']
ECO_CITY_MERGED = ['expo_demog', 'median']
ECO_DEPT = ['expo_demog', 'median', 'poverty_rate']
ECO_REGION = ['expo_demog', 'median_euro', 'poverty_rate']


# I. Analyse descriptive et classsements
# Distributions (histogrammes, box plots)
# Corrélation, (matrice pour chaque niveau géographique)
# Statistiques descriptives (min, max, median, std, valeure la plus fréquente)


def print_ranking(df, id_col, level_name, groups, top_n=10, show_bottom = False):
    print(f"\n  \033[1mRANKING — {level_name.upper()}\033[0m")
    for g in groups:
        if g not in df.columns:
            continue
        sorted_df = df[[id_col, g]].dropna().sort_values(g, ascending=False)
        total = sorted_df[g].sum()
        print(f"\n  \033[1m{g}\033[0m : {int(total)}")
        #print(f"\033[2m  {'Rank':<5} {id_col:<35} {'N':>6}  {'%':>8}\033[0m")
        for i, (_, row) in enumerate(sorted_df.head(top_n).iterrows(), 1):
            pct = row[g] / total * 100 if total > 0 else 0
            print(f"  {i:<5} {str(row[id_col]):<35} {int(row[g]):>6}  {pct:>7.1f}%")
        if show_bottom:
            print(f"  ...")
            bottom_df = sorted_df.tail(top_n)
            total_rows = len(sorted_df)
            for i, (_, row) in enumerate(bottom_df.iterrows(), 1):
                rank = total_rows - top_n + i
                pct = row[g] / total * 100 if total > 0 else 0
                print(f"  {rank:<5} {str(row[id_col]):<35} {int(row[g]):>6}  {pct:>7.1f}%")


print_ranking(df_region, id_col='region', level_name='Region',      groups=GROUPS, top_n=10, show_bottom = False)
print_ranking(df_dept,   id_col='dept',   level_name='Department', groups=GROUPS, top_n=10, show_bottom = True)
print_ranking(df_city,   id_col='pob',    level_name='City',       groups=GROUPS, top_n=10, show_bottom = False)
print_ranking(df_city_merged,   id_col='pob',    level_name='City - Paris merged', groups=GROUPS, top_n=10, show_bottom = False)
print_ranking(df_arr,   id_col='pob',    level_name='Arrondissements', groups=GROUPS, top_n=10, show_bottom = False)


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


# Après avoir nettoyé la base, il faudra exporter ces cinq heatmaps en propre
def print_correlation(df, level_name, groups, eco_vars):
    print(f"\n\033[1m  CORRELATION — {level_name.upper()}\033[0m")
    cols = [c for c in groups + eco_vars if c in df.columns]
    corr = df[cols].corr(method='pearson').round(3)
    print(corr.to_string())

print_correlation(df_region, 'Region',      GROUPS, ECO_REGION)
print_correlation(df_dept,   'Department', GROUPS, ECO_DEPT)
print_correlation(df_city,   'City',       GROUPS, ECO_CITY)
print_correlation(df_city_merged, 'City - Paris merged', GROUPS, ECO_CITY)
print_correlation(df_arr, 'Arrondissements', GROUPS, ECO_CITY)

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
    ax.set_title(f'{level_name} Correlation Matrix', pad=12)

    ax.set_xticklabels(ax.get_xticklabels(), fontsize=10)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=10)
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



#from matplotlib.backends.backend_pdf import PdfPages
#
## Définition explicite des modèles significatifs
#SIGNIFICANT_MODELS = [
#    # (df,           id_col,   level,                group,              eco_vars_significant)
#    (df_city,        'pob',    'City',               'global',           ['median']),
#    (df_city,        'pob',    'City',               'college_de_france',['median']),
#    (df_city,        'pob',    'City',               'executive',        ['median']),
#    (df_city_merged, 'pob',    'City - Paris merged','global',           ['median']),
#    (df_city_merged, 'pob',    'City - Paris merged','college_de_france',['median']),
#    (df_city_merged, 'pob',    'City - Paris merged','executive',        ['median']),
#    (df_arr,         'pob',    'Arrondissements',    'global',         ['median']),
#    (df_arr,         'pob',    'Arrondissements',    'college_de_france',['median']),
#    (df_arr,         'pob',    'Arrondissements',    'politics',        ['median']),
#]
#
#def plot_scatter_residuals(ax, df, id_col, level, group, eco_vars, top_n=10):
#    y_raw = pd.to_numeric(df[group], errors='coerce')
#    y = np.log1p(y_raw)
#    x_raw = pd.to_numeric(df['median'], errors='coerce')
#    x = np.log1p(x_raw)
#
#    # Fit multivariate on significant vars
#    eco_df = df[eco_vars].apply(pd.to_numeric, errors='coerce')
#    eco_df_log = np.log1p(eco_df)
#    mask = y.notna() & x.notna() & eco_df_log.notna().all(axis=1)
#    y_m, x_m = y[mask], x[mask]
#    ids = df.loc[mask, id_col].values
#
#    X = sm.add_constant(eco_df_log[mask])
#    model = sm.OLS(y_m, X).fit()
#    residuals = model.resid
#
#    # Colormap résidus
#    norm = plt.Normalize(vmin=-max(abs(residuals)), vmax=max(abs(residuals)))
#    cmap = plt.cm.RdBu
#    colors = cmap(norm(residuals))
#
#    # Scatter
#    sc = ax.scatter(x_m, y_m, c=residuals, cmap='RdBu',
#                    norm=norm, s=18, alpha=0.7, linewidths=0.2, edgecolors='white')
#
#    # Regression line (univariée expo_demog pour la ligne)
#    m_uni = sm.OLS(y_m, sm.add_constant(x_m)).fit()
#    x_line = np.linspace(x_m.min(), x_m.max(), 100)
#    y_line = m_uni.params[0] + m_uni.params[1] * x_line
#    ax.plot(x_line, y_line, 'k--', linewidth=0.8, alpha=0.6)
#
#    # Labels top/bottom outliers
#    resid_df = pd.DataFrame({'entity': ids, 'residual': residuals, 'x': x_m.values, 'y': y_m.values})
#    top = resid_df.nlargest(top_n, 'residual')
#    bot = resid_df.nsmallest(top_n, 'residual')
#    for _, row in pd.concat([top, bot]).iterrows():
#        ax.annotate(row['entity'], (row['x'], row['y']),
#                    fontsize=5.5, alpha=0.85,
#                    xytext=(3, 3), textcoords='offset points')
#
#    # Labels
#    sig_vars = ' + '.join([f'log({v})' for v in eco_vars])
#    ax.set_xlabel(f'log(median)', fontsize=8)
#    ax.set_ylabel(f'log({group})', fontsize=8)
#    ax.set_title(f'{level} — {group}\n~ {sig_vars}  |  R²={model.rsquared:.3f}  n={mask.sum()}',
#                 fontsize=9, pad=8)
#    ax.tick_params(labelsize=7)
#
#    plt.colorbar(sc, ax=ax, label='résidu', shrink=0.8)
#
#
## Export PDF
#output_pdf = "/Users/eyquem/Desktop/LeadersMap/analysis/outputs/scatter_significant.pdf"
#
#with PdfPages(output_pdf) as pdf:
#    for (df_l, id_col, level, group, eco_vars) in SIGNIFICANT_MODELS:
#        fig, ax = plt.subplots(figsize=(9, 6))
#        plot_scatter_residuals(ax, df_l, id_col, level, group, eco_vars, top_n=10)
#        plt.tight_layout()
#        pdf.savefig(fig, dpi=150)
#        plt.close()
#        print(f"  Added: {level} — {group}")
#
#print(f"\nSaved: {output_pdf}")


## VI. Diagnostic et qualité de modèles (R-2, p value, BIC)
#
## V. Map
#import json
#import pandas as pd
#import numpy as np
#
#def generate_d3_map(df_path, output_path, df, spacing=0.4, iterations=50):
#    df = pd.read_csv(df_path, sep=None, engine='python')
#    df = df.dropna(subset=['lat', 'lon', 'tag', 'dob'])
#    df['dob'] = pd.to_numeric(df['dob'], errors='coerce').dropna()
#    df = df.dropna(subset=['dob'])
#    df['dob'] = df['dob'].astype(int)
#
#    def spiral_jitter(df, spacing=0.04):
#        df = df.copy()
#        df['lat_j'] = df['lat'].astype(float)
#        df['lon_j'] = df['lon'].astype(float)
#        golden = np.pi * (3 - np.sqrt(5))
#        for (lat, lon), idx in df.groupby(['lat', 'lon']).groups.items():
#            idx = list(idx)
#            for i, row_idx in enumerate(idx):
#                if i == 0:
#                    continue
#                r = spacing * np.sqrt(i)
#                theta = i * golden
#                df.at[row_idx, 'lat_j'] = lat + r * np.cos(theta)
#                df.at[row_idx, 'lon_j'] = lon + r * np.sin(theta)
#        return df
#
#    def force_jitter_global(df, spacing=0.04, iterations=50):
#        df = df.copy()
#        coords = df[['lat_j', 'lon_j']].values.copy()
#        min_dist = spacing * 0.9  # distance minimale souhaitée
#
#        for _ in range(iterations):
#            for i in range(len(coords)):
#                dx = coords[i, 1] - coords[:, 1]  # lon
#                dy = coords[i, 0] - coords[:, 0]  # lat
#                dist = np.sqrt(dx**2 + dy**2)
#                dist[i] = np.inf  # ignorer soi-même
#
#                too_close = dist < min_dist
#                if not too_close.any():
#                    continue
#
#                # Force de répulsion proportionnelle à l'overlap
#                overlap = (min_dist - dist[too_close]) / min_dist
#                push_x = (dx[too_close] / dist[too_close] * overlap).sum() * 0.3
#                push_y = (dy[too_close] / dist[too_close] * overlap).sum() * 0.3
#
#                coords[i, 1] += push_x * spacing
#                coords[i, 0] += push_y * spacing
#
#        df['lat_j'] = coords[:, 0]
#        df['lon_j'] = coords[:, 1]
#        return df
#
#
#    df = spiral_jitter(df, spacing=spacing)
#
#    # 2. Répulsion globale
#    df = force_jitter_global(df, spacing=spacing, iterations=iterations)
#
#
#    records = df[['name', 'tag', 'dob', 'lat_j', 'lon_j', 'pob']].rename(
#        columns={'lat_j': 'lat', 'lon_j': 'lon'}
#    ).to_dict(orient='records')
#
#    data_json = json.dumps(records, ensure_ascii=False)
#
#    html = f"""<!DOCTYPE html>
#<html lang="fr">
#<head>
#<meta charset="UTF-8">
#<meta name="viewport" content="width=device-width, initial-scale=1.0">
#<title>Géographie des élites françaises</title>
#<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
#<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+3:wght@300;400;500&display=swap" rel="stylesheet">
#<style>
#  :root {{
#    --bg: #f7f4ef;
#    --paper: #faf8f4;
#    --ink: #1c1c1c;
#    --ink-light: #6b6560;
#    --border: #d4cfc8;
#    --dept-stroke: #c8c2b8;
#    --region-stroke: #8a8278;
#    --sea: #e8eef4;
#
#    --depute:            #d4a017;
#    --executive:         #1a5f8a;
#    --college_de_france: #2d7a4f;
#    --president:         #6b3fa0;
#    --senat:             #c4601a;
#    --ministre:          #b52a2a;
#  }}
#
#  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
#
#  body {{
#    font-family: 'Source Sans 3', sans-serif;
#    background: var(--bg);
#    color: var(--ink);
#    min-height: 100vh;
#    display: flex;
#    flex-direction: column;
#  }}
#
#  #masthead {{
#    padding: 28px 48px 20px;
#    border-bottom: 2px solid var(--ink);
#    display: flex;
#    justify-content: space-between;
#    align-items: flex-end;
#  }}
#
#  #masthead-left h1 {{
#    font-family: 'Playfair Display', serif;
#    font-size: 26px;
#    font-weight: 700;
#    line-height: 1.1;
#    letter-spacing: -0.01em;
#  }}
#
#  #masthead-left p {{
#    font-size: 13px;
#    color: var(--ink-light);
#    margin-top: 5px;
#    font-weight: 300;
#    letter-spacing: 0.03em;
#    text-transform: uppercase;
#  }}
#
#  #masthead-right {{
#    font-size: 11px;
#    color: var(--ink-light);
#    text-align: right;
#    line-height: 1.8;
#  }}
#
#  #toolbar {{
#    display: flex;
#    align-items: center;
#    gap: 32px;
#    padding: 14px 48px;
#    border-bottom: 1px solid var(--border);
#    background: var(--paper);
#  }}
#
#  #year-block {{
#    display: flex;
#    flex-direction: column;
#    gap: 2px;
#    min-width: 64px;
#  }}
#
#  #year-label {{
#    font-size: 10px;
#    text-transform: uppercase;
#    letter-spacing: 0.1em;
#    color: var(--ink-light);
#  }}
#
#  #year-val {{
#    font-family: 'Playfair Display', serif;
#    font-size: 30px;
#    font-weight: 600;
#    line-height: 1;
#    color: var(--ink);
#  }}
#
#  #slider-block {{
#    flex: 1;
#    display: flex;
#    flex-direction: column;
#    gap: 6px;
#  }}
#
#  #year-slider {{
#    -webkit-appearance: none;
#    width: 100%;
#    height: 2px;
#    background: var(--border);
#    outline: none;
#    cursor: pointer;
#  }}
#
#  #year-slider::-webkit-slider-thumb {{
#    -webkit-appearance: none;
#    width: 14px;
#    height: 14px;
#    border-radius: 50%;
#    background: var(--ink);
#    cursor: pointer;
#    transition: transform 0.1s;
#  }}
#
#  #year-slider::-webkit-slider-thumb:hover {{ transform: scale(1.3); }}
#
#  #slider-ticks {{
#    display: flex;
#    justify-content: space-between;
#    font-size: 10px;
#    color: var(--ink-light);
#    letter-spacing: 0.05em;
#  }}
#
#  #play-btn {{
#    width: 36px; height: 36px;
#    border: 1.5px solid var(--ink);
#    background: transparent;
#    cursor: pointer;
#    display: flex;
#    align-items: center;
#    justify-content: center;
#    font-size: 13px;
#    color: var(--ink);
#    transition: all 0.15s;
#    flex-shrink: 0;
#  }}
#
#  #play-btn:hover {{ background: var(--ink); color: var(--paper); }}
#
#  #count-block {{
#    text-align: right;
#    min-width: 110px;
#  }}
#
#  #count-val {{
#    font-family: 'Playfair Display', serif;
#    font-size: 22px;
#    font-weight: 600;
#  }}
#
#  #count-label {{
#    font-size: 10px;
#    text-transform: uppercase;
#    letter-spacing: 0.1em;
#    color: var(--ink-light);
#  }}
#
#  #main {{
#    display: flex;
#    flex: 1;
#    overflow: hidden;
#  }}
#
#  #map-area {{
#    flex: 1;
#    position: relative;
#    background: var(--sea);
#  }}
#
#  #map-svg {{
#    width: 100%;
#    height: 100%;
#  }}
#
#  .dept-path {{
#    fill: var(--paper);
#    stroke: var(--dept-stroke);
#    stroke-width: 0.4px;
#  }}
#
#  .region-path {{
#    fill: none;
#    stroke: var(--region-stroke);
#    stroke-width: 1.4px;
#  }}
#
#  .dot {{
#    transition: opacity 0.3s;
#  }}
#
#  .dot:hover {{ opacity: 1 !important; cursor: pointer; }}
#
#  #sidebar {{
#    width: 220px;
#    border-left: 1px solid var(--border);
#    background: var(--paper);
#    padding: 24px 20px;
#    display: flex;
#    flex-direction: column;
#    gap: 20px;
#    overflow-y: auto;
#  }}
#
#  #legend-title {{
#    font-family: 'Playfair Display', serif;
#    font-size: 14px;
#    font-weight: 600;
#    padding-bottom: 10px;
#    border-bottom: 1px solid var(--border);
#  }}
#
#  .legend-item {{
#    display: flex;
#    align-items: center;
#    gap: 10px;
#    cursor: pointer;
#    user-select: none;
#    padding: 5px 0;
#    transition: opacity 0.2s;
#  }}
#
#  .legend-item.disabled {{ opacity: 0.3; }}
#
#  .legend-swatch {{
#    width: 12px; height: 12px;
#    border-radius: 50%;
#    flex-shrink: 0;
#  }}
#
#  .legend-name {{
#    font-size: 13px;
#    font-weight: 400;
#    flex: 1;
#  }}
#
#  .legend-count {{
#    font-size: 11px;
#    color: var(--ink-light);
#    font-variant-numeric: tabular-nums;
#  }}
#
#  #stats-block {{
#    padding-top: 16px;
#    border-top: 1px solid var(--border);
#  }}
#
#  #stats-title {{
#    font-size: 10px;
#    text-transform: uppercase;
#    letter-spacing: 0.1em;
#    color: var(--ink-light);
#    margin-bottom: 10px;
#  }}
#
#  .stat-row {{
#    display: flex;
#    justify-content: space-between;
#    font-size: 12px;
#    padding: 3px 0;
#    border-bottom: 1px dotted var(--border);
#  }}
#
#  /* Tooltip */
#  #tooltip {{
#    position: fixed;
#    background: var(--ink);
#    color: var(--paper);
#    padding: 8px 12px;
#    font-size: 12px;
#    line-height: 1.6;
#    pointer-events: none;
#    opacity: 0;
#    transition: opacity 0.15s;
#    max-width: 200px;
#    z-index: 9999;
#  }}
#
#  #tooltip b {{ font-weight: 600; font-size: 13px; display: block; }}
#
#  /* DOM encarts */
#  .encart {{
#    position: absolute;
#    background: var(--sea);
#  }}
#
#  .encart-label {{
#    position: absolute;
#    font-size: 9px;
#    text-transform: uppercase;
#    letter-spacing: 0.08em;
#    color: var(--ink-light);
#  }}
#
#  #footer {{
#    padding: 10px 48px;
#    border-top: 1px solid var(--border);
#    font-size: 10px;
#    color: var(--ink-light);
#    letter-spacing: 0.04em;
#    display: flex;
#    justify-content: space-between;
#  }}
#</style>
#</head>
#<body>
#
#<div id="masthead">
#  <div id="masthead-left">
#    <h1>Géographie des élites françaises</h1>
#    <p>Lieux de naissance · par catégorie · vue cumulative</p>
#  </div>
#  <div id="masthead-right">
#    LeadersMap · Données agrégées<br>
#    France métropolitaine &amp; DOM
#  </div>
#</div>
#
#<div id="toolbar">
#  <div id="year-block">
#    <div id="year-label">Année</div>
#    <div id="year-val">1875</div>
#  </div>
#  <div id="slider-block">
#    <input type="range" id="year-slider" min="1875" max="2005" value="1875" step="1"/>
#    <div id="slider-ticks">
#      <span>1875</span>
#      <span>1900</span><span>1925</span><span>1950</span><span>1975</span><span>2000</span><span>2005</span>
#    </div>
#  </div>
#  <button id="play-btn" title="Play / Pause">▶</button>
#  <div id="count-block">
#    <div id="count-val">0</div>
#    <div id="count-label">personnalités</div>
#  </div>
#</div>
#
#<div id="main">
#  <div id="map-area">
#    <svg id="map-svg"></svg>
#  </div>
#  <div id="sidebar">
#    <div id="legend-title">Catégories</div>
#    <div id="legend-items"></div>
#    <div id="stats-block">
#      <div id="stats-title">Visibles</div>
#      <div id="stats-rows"></div>
#    </div>
#  </div>
#</div>
#
#<div id="footer">
#  <span>Cliquer sur une catégorie pour l'activer / désactiver</span>
#  <span>Survol pour détail · Animation cumulative depuis 1875</span>
#</div>
#
#<div id="tooltip"></div>
#
#<script>
#const DATA = {data_json};
#
#const TAGS = [
#  {{ id: 'depute',            label: 'Député',            color: '#d4a017' }},
#  {{ id: 'executive',         label: 'Executive',         color: '#1a5f8a' }},
#  {{ id: 'college_de_france', label: 'Collège de France', color: '#2d7a4f' }},
#  {{ id: 'president',         label: 'Président',         color: '#6b3fa0' }},
#  {{ id: 'senat',             label: 'Sénat',             color: '#c4601a' }},
#  {{ id: 'ministre',          label: 'Ministre',          color: '#b52a2a' }},
#];
#
#const colorMap = Object.fromEntries(TAGS.map(t => [t.id, t.color]));
#let activeSet = new Set(TAGS.map(t => t.id));
#
#// ── D3 MAP SETUP ─────────────────────────────────────────────────────────────
#const svg = d3.select('#map-svg');
#const mapArea = document.getElementById('map-area');
#
#// Metropolitan France projection
#const projFR = d3.geoConicConformal()
#  .center([2.5, 46.5])
#  .parallels([44, 49])
#  .scale(1)
#  .translate([0, 0]);
#
#const pathFR = d3.geoPath().projection(projFR);
#
#// DOM projections (small insets)
#const domConfigs = [
#  {{ id: 'guyane',     center: [-53.1, 3.9],   parallels: [2, 6],   scale: 0.7, label: 'Guyane' }},
#  {{ id: 'reunion',    center: [55.5, -21.1],  parallels: [-22, -20], scale: 2.5, label: 'La Réunion' }},
#  {{ id: 'guadeloupe', center: [-61.5, 16.2],  parallels: [15, 17], scale: 3.5, label: 'Guadeloupe' }},
#  {{ id: 'martinique', center: [-61.0, 14.65], parallels: [14, 15], scale: 4.5, label: 'Martinique' }},
#];
#
#let deptData = null, regionData = null;
#let dotsLayer = null;
#let drawnDots = new Map(); // dob -> [elements]
#let currentYear = 1875;
#let playing = false;
#let playInterval = null;
#
#// Fetch both GeoJSONs
#Promise.all([
#  fetch('https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson').then(r => r.json()),
#  fetch('https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-version-simplifiee.geojson').then(r => r.json()),
#]).then(([dept, region]) => {{
#  deptData = dept;
#  regionData = region;
#  initMap();
#}});
#
#function initMap() {{
#  const W = mapArea.clientWidth;
#  const H = mapArea.clientHeight;
#
#  svg.attr('viewBox', `0 0 ${{W}} ${{H}}`).attr('width', W).attr('height', H);
#
#  // Fit metropolitan France
#  const mainW = W - 20;
#  const mainH = H - 20;
#  projFR.fitExtent([[10, 10], [mainW * 0.78, mainH]], {{
#    type: 'FeatureCollection',
#    features: deptData.features.filter(f => {{
#      const code = f.properties.code;
#      return code && !['971','972','973','974','976'].includes(code);
#    }})
#  }});
#
#  const metroGroup = svg.append('g').attr('id', 'metro');
#
#  // Departments (thin)
#  metroGroup.selectAll('.dept-path')
#    .data(deptData.features.filter(f => !['971','972','973','974','976'].includes(f.properties.code)))
#    .enter().append('path')
#    .attr('class', 'dept-path')
#    .attr('d', pathFR);
#
#  // Regions (thick overlay)
#  metroGroup.selectAll('.region-path')
#    .data(regionData.features)
#    .enter().append('path')
#    .attr('class', 'region-path')
#    .attr('d', pathFR);
#
#  // DOM insets
#  const insetW = 90, insetH = 80;
#  const insetX = W - insetW - 12;
#  const insetStartY = 10;
#
#  domConfigs.forEach((dom, i) => {{
#    const iy = insetStartY + i * (insetH + 8);
#    const g = svg.append('g').attr('transform', `translate(${{insetX}}, ${{iy}})`);
#
#    // Border
#    g.append('rect')
#      .attr('width', insetW).attr('height', insetH)
#      .attr('fill', '#e8eef4').attr('stroke', '#c8c2b8').attr('stroke-width', 0.6);
#
#    // Label
#    g.append('text')
#      .attr('x', 4).attr('y', insetH - 4)
#      .attr('font-size', '8px')
#      .attr('font-family', 'Source Sans 3, sans-serif')
#      .attr('fill', '#8a8278')
#      .attr('letter-spacing', '0.08em')
#      .text(dom.label.toUpperCase());
#
#    // GeoJSON for this DOM
#    const domFeatures = deptData.features.filter(f => {{
#      const code = f.properties.code;
#      if (dom.id === 'guyane') return code === '973';
#      if (dom.id === 'reunion') return code === '974';
#      if (dom.id === 'guadeloupe') return code === '971';
#      if (dom.id === 'martinique') return code === '972';
#      return false;
#    }});
#
#    if (domFeatures.length === 0) return;
#
#    const domProj = d3.geoConicConformal()
#      .center(dom.center)
#      .parallels(dom.parallels)
#      .scale(1).translate([0, 0]);
#
#    const domPath = d3.geoPath().projection(domProj);
#    domProj.fitExtent([[4, 4], [insetW - 4, insetH - 14]], {{
#      type: 'FeatureCollection', features: domFeatures
#    }});
#
#    g.selectAll('.dept-path-dom')
#      .data(domFeatures)
#      .enter().append('path')
#      .attr('fill', '#faf8f4')
#      .attr('stroke', '#c8c2b8')
#      .attr('stroke-width', 0.5)
#      .attr('d', domPath);
#
#    // Store projection for dot placement
#    dom.proj = domProj;
#    dom.group = g;
#    dom.offsetX = insetX;
#    dom.offsetY = iy;
#  }});
#
#  // Dots layer on top
#  dotsLayer = svg.append('g').attr('id', 'dots');
#
#  buildLegend();
#  renderUpTo(1875);
#}}
#
#function projectPoint(lon, lat) {{
#  // Check if DOM
#  const domCodes = {{
#    'guyane': [-54.5, -51.5, 2.0, 5.5],
#    'reunion': [55.0, 56.0, -21.5, -20.5],
#    'guadeloupe': [-62.0, -60.9, 15.7, 16.6],
#    'martinique': [-61.3, -60.7, 14.3, 15.0],
#  }};
#  for (const dom of domConfigs) {{
#    if (!dom.proj) continue;
#    const bounds = domCodes[dom.id];
#    if (lon >= bounds[0] && lon <= bounds[1] && lat >= bounds[2] && lat <= bounds[3]) {{
#      const [x, y] = dom.proj([lon, lat]);
#      return [dom.offsetX + x, dom.offsetY + y];
#    }}
#  }}
#  const pt = projFR([lon, lat]);
#  return pt;
#}}
#
#function renderUpTo(year) {{
#  const toAdd = DATA.filter(d => d.dob <= year && !drawnDots.has(d));
#
#  toAdd.forEach(d => {{
#    if (!activeSet.has(d.tag)) {{ drawnDots.set(d, null); return; }}
#    const pt = projectPoint(d.lon, d.lat);
#    if (!pt) {{ drawnDots.set(d, null); return; }}
#    const circle = dotsLayer.append('circle')
#      .attr('class', 'dot')
#      .attr('cx', pt[0]).attr('cy', pt[1])
#      .attr('r', 2)
#      .attr('fill', colorMap[d.tag] || '#999')
#      .attr('fill-opacity', 0.72)
#      .attr('stroke', 'rgba(255,255,255,0.5)')
#      .attr('stroke-width', 0.4)
#      .on('mouseover', (event) => showTooltip(event, d))
#      .on('mousemove', (event) => moveTooltip(event))
#      .on('mouseout', hideTooltip);
#
#    drawnDots.set(d, circle);
#  }});
#
#  document.getElementById('year-val').textContent = year;
#  updateCount();
#  updateStats();
#}}
#
#function redrawAll() {{
#  dotsLayer.selectAll('*').remove();
#  drawnDots.clear();
#  renderUpTo(currentYear);
#}}
#
#// ── LEGEND & FILTERS ─────────────────────────────────────────────────────────
#function buildLegend() {{
#  const container = document.getElementById('legend-items');
#  TAGS.forEach(t => {{
#    const item = document.createElement('div');
#    item.className = 'legend-item';
#    item.dataset.tag = t.id;
#    item.innerHTML = `
#      <div class="legend-swatch" style="background:${{t.color}}"></div>
#      <div class="legend-name">${{t.label}}</div>
#      <div class="legend-count" id="lc-${{t.id}}">0</div>
#    `;
#    item.addEventListener('click', () => toggleTag(t.id, item));
#    container.appendChild(item);
#  }});
#}}
#
#function toggleTag(tagId, item) {{
#  if (activeSet.has(tagId)) {{
#    activeSet.delete(tagId);
#    item.classList.add('disabled');
#    // Hide existing dots
#    drawnDots.forEach((circle, d) => {{
#      if (d.tag === tagId && circle) circle.attr('display', 'none');
#    }});
#  }} else {{
#    activeSet.add(tagId);
#    item.classList.remove('disabled');
#    // Show or draw dots
#    drawnDots.forEach((circle, d) => {{
#      if (d.tag === tagId) {{
#        if (circle) circle.attr('display', null);
#        else if (d.dob <= currentYear) {{
#          const pt = projectPoint(d.lon, d.lat);
#          if (!pt) return;
#          const c = dotsLayer.append('circle')
#            .attr('class', 'dot')
#            .attr('cx', pt[0]).attr('cy', pt[1])
#            .attr('r', 2)
#            .attr('fill', colorMap[d.tag] || '#999')
#            .attr('fill-opacity', 0.72)
#            .attr('stroke', 'rgba(255,255,255,0.5)')
#            .attr('stroke-width', 0.4)
#            .on('mouseover', (event) => showTooltip(event, d))
#            .on('mousemove', (event) => moveTooltip(event))
#            .on('mouseout', hideTooltip);
#          drawnDots.set(d, c);
#        }}
#      }}
#    }});
#  }}
#  updateCount();
#  updateStats();
#}}
#
#function updateCount() {{
#  let n = 0;
#  drawnDots.forEach((circle, d) => {{
#    if (d.dob <= currentYear && activeSet.has(d.tag)) n++;
#  }});
#  document.getElementById('count-val').textContent = n.toLocaleString('fr-FR');
#}}
#
#function updateStats() {{
#  const container = document.getElementById('stats-rows');
#  container.innerHTML = '';
#  TAGS.forEach(t => {{
#    let n = 0;
#    drawnDots.forEach((c, d) => {{
#      if (d.tag === t.id && d.dob <= currentYear) n++;
#    }});
#    document.getElementById('lc-' + t.id).textContent = n.toLocaleString('fr-FR');
#    if (activeSet.has(t.id)) {{
#      const row = document.createElement('div');
#      row.className = 'stat-row';
#      row.innerHTML = `<span style="color:${{t.color}};font-weight:500">${{t.label}}</span><span>${{n.toLocaleString('fr-FR')}}</span>`;
#      container.appendChild(row);
#    }}
#  }});
#}}
#
#// ── TOOLTIP ──────────────────────────────────────────────────────────────────
#const tooltip = document.getElementById('tooltip');
#
#function showTooltip(event, d) {{
#  const tagLabel = TAGS.find(t => t.id === d.tag)?.label || d.tag;
#  tooltip.innerHTML = `<b>${{d.name}}</b>${{tagLabel}} · ${{d.dob}}<br>${{d.pob}}`;
#  tooltip.style.opacity = 1;
#  moveTooltip(event);
#}}
#
#function moveTooltip(event) {{
#  tooltip.style.left = (event.clientX + 14) + 'px';
#  tooltip.style.top  = (event.clientY - 10) + 'px';
#}}
#
#function hideTooltip() {{
#  tooltip.style.opacity = 0;
#}}
#
#// ── SLIDER & PLAY ────────────────────────────────────────────────────────────
#const slider = document.getElementById('year-slider');
#
#slider.addEventListener('input', function() {{
#  const y = +this.value;
#  if (y < currentYear) {{
#    dotsLayer.selectAll('*').remove();
#    drawnDots.clear();
#    currentYear = 1875;
#  }}
#  currentYear = y;
#  renderUpTo(y);
#}});
#
#document.getElementById('play-btn').addEventListener('click', function() {{
#  if (playing) {{
#    clearInterval(playInterval);
#    playing = false;
#    this.textContent = '▶';
#  }} else {{
#    playing = true;
#    this.textContent = '⏸';
#    if (currentYear >= 2005) {{
#      dotsLayer.selectAll('*').remove();
#      drawnDots.clear();
#      currentYear = 1875;
#      slider.value = 1875;
#    }}
#    playInterval = setInterval(() => {{
#      if (currentYear >= 2005) {{
#        clearInterval(playInterval);
#        playing = false;
#        document.getElementById('play-btn').textContent = '▶';
#        return;
#      }}
#      currentYear++;
#      slider.value = currentYear;
#      renderUpTo(currentYear);
#    }}, 60);
#  }}
#}});
#
#// Resize
#window.addEventListener('resize', () => {{
#  if (deptData) {{ svg.selectAll('*').remove(); drawnDots.clear(); initMap(); }}
#}});
#</script>
#</body>
#</html>"""
#
#    with open(output_path, 'w', encoding='utf-8') as f:
#        f.write(html)
#    print(f"Saved: {output_path}")
#
#generate_d3_map(
#    df_path="/Users/eyquem/Desktop/LeadersMap/analysis/interim/merged_clean.csv",
#    output_path="/Users/eyquem/Desktop/LeadersMap/analysis/processed/map_elites_d3.html",
#    df=df,  # Si tu veux passer df, passe-le en troisième argument
#    spacing=0.04,
#    iterations=50
#)

#Résultats