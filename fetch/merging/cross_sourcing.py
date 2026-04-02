from rapidfuzz import process, fuzz
from pathlib import Path
import pandas as pd
import unicodedata

base_path = Path("~/EliteCradle").expanduser()
df_source = pd.read_excel(base_path / "fetch/merging/src/base-pop-historiques-1876-2023.xlsx", header=5)
path_export = base_path / "fetch/merging/interim/"

# REG and DEP give us the Region and Department number of each city
df = df_source.iloc[:, [1, 2]].copy()
df.columns = ['REG', 'DEP']

# We calculate the 10-year average for each city
df['2000-2009'] = df_source.iloc[:, 18:22].mean(axis=1)
df['1990-1999'] = df_source.iloc[:, 22:24].mean(axis=1) 
df['1980-1989'] = df_source.iloc[:, 24]                
df['1970-1979'] = df_source.iloc[:, 25]                
df['1960-1969'] = df_source.iloc[:, 26:28].mean(axis=1)
df['1950-1959'] = df_source.iloc[:, 28]                
df['1930-1939'] = df_source.iloc[:, 29:31].mean(axis=1)
df['1940-1949'] = df[['1950-1959', '1930-1939']].mean(axis=1) # Average of the precedent and following decade since we don't have any data points in this interval
df['1920-1929'] = df_source.iloc[:, 31:33].mean(axis=1) 
df['1910-1919'] = df_source.iloc[:, 33]                
df['1900-1909'] = df_source.iloc[:, 34:36].mean(axis=1) 
df['-1900'] = df_source.iloc[:, 36:41].mean(axis=1)
ordered_cols = ['2000-2009', '1990-1999', '1980-1989', '1970-1979', '1960-1969', '1950-1959', '1940-1949', '1930-1939', '1920-1929', '1910-1919', '1900-1909', '-1900']

# Region regrouping
df_region = df.drop(columns=['DEP']).groupby('REG').sum().reset_index()

# Swithing from INSEE code to official names
mapping_regions = {
    1: "Guadeloupe", 2: "Martinique", 3: "Guyane", 4: "La Réunion",
    11: "Île-de-France", 24: "Centre-Val de Loire", 27: "Bourgogne-Franche-Comté",
    28: "Normandie", 32: "Hauts-de-France", 44: "Grand Est",
    52: "Pays de la Loire", 53: "Bretagne", 75: "Nouvelle-Aquitaine",
    76: "Occitanie", 84: "Auvergne-Rhône-Alpes", 93: "Provence-Alpes-Côte d'Azur",
    94: "Corse", 971: "Guadeloupe", 972: "Martinique", 973:"Guyane", 974:"La Réunion"
}

# And from department numbers to names
mapping_depts = {
    '01': "Ain", '02': "Aisne", '03': "Allier", '04': "Alpes-de-Haute-Provence", '05': "Hautes-Alpes",
    '06': "Alpes-Maritimes", '07': "Ardèche", '08': "Ardennes", '09': "Ariège", '10': "Aube",
    '11': "Aude", '12': "Aveyron", '13': "Bouches-du-Rhône", '14': "Calvados", '15': "Cantal",
    '16': "Charente", '17': "Charente-Maritime", '18': "Cher", '19': "Corrèze", '2A': "Corse-du-Sud",
    '2B': "Haute-Corse", '21': "Côte-d'Or", '22': "Côtes-d'Armor", '23': "Creuse", '24': "Dordogne",
    '25': "Doubs", '26': "Drôme", '27': "Eure", '28': "Eure-et-Loir", '29': "Finistère",
    '30': "Gard", '31': "Haute-Garonne", '32': "Gers", '33': "Gironde", '34': "Hérault",
    '35': "Ille-et-Vilaine", '36': "Indre", '37': "Indre-et-Loire", '38': "Isère", '39': "Jura",
    '40': "Landes", '41': "Loir-et-Cher", '42': "Loire", '43': "Haute-Loire", '44': "Loire-Atlantique",
    '45': "Loiret", '46': "Lot", '47': "Lot-et-Garonne", '48': "Lozère", '49': "Maine-et-Loire",
    '50': "Manche", '51': "Marne", '52': "Haute-Marne", '53': "Mayenne", '54': "Meurthe-et-Moselle",
    '55': "Meuse", '56': "Morbihan", '57': "Moselle", '58': "Nièvre", '59': "Nord",
    '60': "Oise", '61': "Orne", '62': "Pas-de-Calais", '63': "Puy-de-Dôme", '64': "Pyrénées-Atlantiques",
    '65': "Hautes-Pyrénées", '66': "Pyrénées-Orientales", '67': "Bas-Rhin", '68': "Haut-Rhin", '69': "Rhône",
    '70': "Haute-Saône", '71': "Saône-et-Loire", '72': "Sarthe", '73': "Savoie", '74': "Haute-Savoie",
    '75': "Paris", '76': "Seine-Maritime", '77': "Seine-et-Marne", '78': "Yvelines", '79': "Deux-Sèvres",
    '80': "Somme", '81': "Tarn", '82': "Tarn-et-Garonne", '83': "Var", '84': "Vaucluse",
    '85': "Vendée", '86': "Vienne", '87': "Haute-Vienne", '88': "Vosges", '89': "Yonne",
    '90': "Territoire de Belfort", '91': "Essonne", '92': "Hauts-de-Seine", '93': "Seine-Saint-Denis",
    '94': "Val-de-Marne", '95': "Val-d'Oise", '971': "Guadeloupe", '972': "Martinique", 
    '973': "Guyane", '974': "La Réunion"
}

df_region['region'] = df_region['REG'].map(mapping_regions)
cols_reg = ['REG', 'region'] + ordered_cols
df_region = df_region[cols_reg]
df_region = df_region.fillna(0)

# We fill empty values by the most recent data multiplied by 0.95 : 5% approximate population growth
for i in range(1, len(ordered_cols)):
    current_col = ordered_cols[i]
    prev_col = ordered_cols[i-1]
    mask = df_region[current_col] == 0
    df_region.loc[mask, current_col] = df_region.loc[mask, prev_col] * 0.95

df_region = df_region.round(0).astype(int, errors='ignore')
df_region.to_csv(f"{path_export}pop_region.csv", index=False, sep=";")

# Department regrouping
df['DEP'] = df['DEP'].astype(str).str.zfill(2)
df_dept = df.groupby('DEP').sum(numeric_only=True).reset_index()

df_dept['dept'] = df_dept['DEP'].map(mapping_depts)
cols_dept = ['DEP', 'dept'] + ordered_cols
df_dept = df_dept[cols_dept]
df_dept = df_dept.fillna(0)

# Same empty filling
for i in range(1, len(ordered_cols)):
    current_col = ordered_cols[i]
    prev_col = ordered_cols[i-1]
    mask = df_dept[current_col] == 0
    df_dept.loc[mask, current_col] = df_dept.loc[mask, prev_col] * 0.95

df_dept = df_dept.round(0).astype(int, errors='ignore')
df_dept.to_csv(f"{path_export}pop_dept.csv", index=False, sep=";")
print("Successful population export")


# Economic indicators
df_ecoc = pd.read_csv(base_path / "fetch/merging/interim/eco_city.csv", sep=None, engine='python')
df_ecod = pd.read_csv(base_path / "fetch/merging/interim/eco_dept.csv", sep=None, engine='python')
df_ecor = pd.read_csv(base_path / "fetch/merging/interim/eco_region.csv", sep=None, engine='python')
df_datac = pd.read_csv(base_path / "fetch/merging/interim/data_city.csv", sep=None, engine='python')

# Demographic indicators
df_popc = pd.read_csv(base_path / "fetch/merging/interim/pop_city.csv", sep=None, engine='python')
df_popd = pd.read_csv(base_path / "fetch/merging/interim/pop_dept.csv", sep=None, engine='python')
df_popr = pd.read_csv(base_path / "fetch/merging/interim/pop_region.csv", sep=None, engine='python')

# Educational indicators
df_edu = pd.read_csv(base_path / "fetch/merging/interim/edu_city.csv", sep=None, engine='python')
df_prepa = pd.read_csv(base_path / "fetch/merging/interim/cpge.csv", sep=None, engine='python')

# Personnalities
df_ppl = pd.read_csv(base_path / "fetch/merging/out/merged_clean.csv", sep=None, engine='python')

# Turning dob into decades intervals
def categorize_decade(year):
    if pd.isna(year):
        return None
    year = int(year)
    if year < 1900:
        return "-1900"
    
    start_year = (year // 10) * 10
    end_year = start_year + 9
    return f"{start_year}-{end_year}"

# Normalizing INSEE department code
def extract_dept_from_insee(code):
    if pd.isna(code):
        return None
    s = str(code).split('.')[0].strip()
    if s.startswith('97'):
        return s[:3]
    if len(s) >= 5:
        return s[:-3]
    return s.zfill(2)

def to_dept_type(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return val
    
def normalize_str(s):
    s = str(s).lower().strip()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('-', ' ').replace("'", ' ')
    return s

# Department code normalization
df_ecoc['dept'] = df_ecoc['dept_num'].apply(extract_dept_from_insee).apply(to_dept_type)
df_ppl  = df_ppl.rename(columns={'dept_num': 'dept'})
df_popc = df_popc.rename(columns={'DEP': 'dept'})
for df in [df_ppl, df_popc]: df['dept'] = df['dept'].apply(to_dept_type)

# Calculating birth decade and weight
df_ppl['birth_decade'] = df_ppl['dob'].apply(categorize_decade)
weights = df_ppl['birth_decade'].value_counts(normalize=True)

# Fuzzy city-name matching
ref_by_dept = {
    dept: {normalize_str(pob): pob for pob in group['pob'].unique()}
    for dept, group in df_popc.groupby('dept')
}

def fuzzy_match_pob(pob, dept, threshold=85):
    candidates = ref_by_dept.get(dept)
    if not candidates:
        return None
    result = process.extractOne(
        normalize_str(pob),
        candidates.keys(),
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold
    )
    if result:
        matched_key, score, _ = result
        return candidates[matched_key]
    return None

df_ppl['pob_clean'] = df_ppl.apply(lambda row: fuzzy_match_pob(row['pob'], row['dept']), axis=1)
unmatched = df_ppl[df_ppl['pob_clean'].isna()][['pob', 'dept']].drop_duplicates()
if not unmatched.empty:
    print(f"{len(unmatched)} unmatched localities:")
    print(unmatched.to_string())

df_ppl['pob'] = df_ppl['pob_clean'].fillna(df_ppl['pob'])


# Creating the City dataframe with economic and demographic data
df_ppl_count = df_ppl.groupby(['pob', 'dept', 'tag']).size().reset_index(name='count')

# 1 Column per tag, with total
df_ppl_count = df_ppl_count.pivot_table(
    index=['pob', 'dept'], 
    columns='tag', 
    values='count', 
    fill_value=0
).reset_index()
df_ppl_count['global'] = df_ppl_count.select_dtypes(include=['number']).sum(axis=1)

# Edu
df_edu['dept'] = df_edu['dept'].str.split(' - ').str[0].apply(to_dept_type)

df_edu_counts = df_edu.groupby(['pob', 'dept', 'type']).size().unstack(fill_value=0).reset_index()
df_edu_counts = df_edu_counts.rename(columns={'PRO': 'lycees_pro', 'GT': 'lycees_gt'})
df_edu_counts['lycees'] = df_edu_counts['lycees_pro'] + df_edu_counts['lycees_gt']
df_edu_counts['edu'] = 1 

unmatched_edu = df_edu_counts[~df_edu_counts.set_index(['pob', 'dept']).index.isin(df_popc.set_index(['pob', 'dept']).index)]
if not unmatched_edu.empty:
    print(f"{len(unmatched_edu)} educational localities not found in demographic base:")
    print(unmatched_edu[['pob', 'dept']].to_string())

# CPGE
df_prepa = df_prepa.rename(columns={'commune': 'pob'})
df_prepa['dept'] = df_prepa['dept_id'].str.replace('D', '').str.lstrip('0').apply(to_dept_type)
df_prepa_counts = df_prepa.groupby(['pob', 'dept']).size().reset_index(name='prepa_count')
df_prepa_counts['prepa'] = 1  # Binary indicator

unmatched_prepa = df_prepa_counts[~df_prepa_counts.set_index(['pob', 'dept']).index.isin(df_popc.set_index(['pob', 'dept']).index)]
if not unmatched_prepa.empty:
    print(f"{len(unmatched_prepa)} CPGE localities not found in demographic base:")
    print(unmatched_prepa[['pob', 'dept']].to_string())

# Start from the demographic base and merge personalities and economic data
df_final_city = df_popc.copy()

def extract_dept_from_commune(code):
    if pd.isna(code): return None
    s = str(code).split('.')[0].strip().zfill(5) 
    return s[:3] if s.startswith('97') else s[:2]

df_datac['dept'] = df_datac['dept_num'].apply(extract_dept_from_commune).apply(to_dept_type)

df_final_city = pd.merge(df_final_city, df_datac[['pob', 'dept', 'cadres', 'activity_rate', 'tertiaire']], on=['pob', 'dept'], how='left')
df_final_city = pd.merge(df_final_city, df_ppl_count, on=['pob', 'dept'], how='left')
df_final_city = pd.merge(df_final_city, df_ecoc[['pob', 'dept', 'median']], on=['pob', 'dept'], how='left')
df_final_city = pd.merge(df_final_city, df_edu_counts, on=['pob', 'dept'], how='left')
df_final_city = pd.merge(df_final_city, df_prepa_counts, on=['pob', 'dept'], how='left')

tag_columns = [c for c in df_ppl_count.columns if c not in ['pob', 'dept', 'global']]
edu_cols = ['lycees_pro', 'lycees_gt', 'lycees', 'edu']
prepa_cols = ['prepa', 'prepa_count']
df_final_city[tag_columns + ['global'] + edu_cols + prepa_cols] = df_final_city[tag_columns + ['global'] + edu_cols + prepa_cols].fillna(0).astype(int)

politics_tags = ['parliament', 'senat', 'minister', 'president']
politics_cols = [col for col in politics_tags if col in df_final_city.columns]
df_final_city['politics'] = df_final_city[politics_cols].sum(axis=1)

# Compute demographic exposure: weighted sum of population across birth decades
# Each decade's population is weighted by its share in the personalities dataset
df_final_city['expo_demog'] = 0
cols_to_fix = [c for c in weights.index if c in df_final_city.columns]
df_final_city[cols_to_fix] = df_final_city[cols_to_fix].apply(pd.to_numeric, errors='coerce').fillna(0)
for decade, weight in weights.items():
    if decade in df_final_city.columns:
        df_final_city['expo_demog'] += df_final_city[decade] * weight

# Prepa rate is the amount of preparatory classes per 1000 people in the demographic exposure index
df_final_city['prepa_rate'] = df_final_city['prepa_count'] / df_final_city['expo_demog'] * 1000

# We retain all cities, even those without elites
df_final_city['global'] = df_final_city['global'].fillna(0).astype(int)
ordered_cols = ['pob', 'dept', 'global', 'politics'] + tag_columns + ['median', 'cadres', 'activity_rate', 'tertiaire', 'expo_demog', 'lycees_pro', 'lycees_gt', 'lycees', 'edu', 'prepa', 'prepa_count', 'prepa_rate']
df_final_city = df_final_city[ordered_cols]

df_final_city.to_csv(base_path / "analysis/processed/analysis_city.csv", index=False, sep=";")


# Creating the Department dataframe with economic and demographic data
# Counting personalities per department
df_ppl_count = df_ppl.groupby(['department', 'tag']).size().reset_index(name='count')
df_ppl_count = df_ppl_count.pivot_table(index='department', columns='tag', values='count', fill_value=0).reset_index()
df_ppl_count.columns.name = None
df_ppl_count['global'] = df_ppl_count.select_dtypes(include=['number']).sum(axis=1)
df_ppl_count = df_ppl_count.rename(columns={'department': 'dept'})
df_prepa_dept = df_prepa.groupby('dept').size().reset_index(name='prepa_count')
df_prepa_dept = df_prepa_dept.rename(columns={'dept': 'DEP'})

# Obtaining departmental population per decade
df_final_department = df_popd.copy()

# Merging personnalities count and economic data
df_final_department = pd.merge(df_final_department, df_ppl_count, on='dept', how='left')
df_final_department['DEP'] = df_final_department['DEP'].apply(to_dept_type)
df_final_department = pd.merge(df_final_department, df_prepa_dept, on='DEP', how='left')
df_eco_subset = df_ecod[['dept', 'dept_num', 'median', 'poverty_rate', 'colleges', 'lycees_pro', 'lycees_gt', 'second_degre', 'cadres_and_pro', 'activity_rate', 'tertiaire']]
df_final_department = pd.merge(df_final_department, df_eco_subset, on='dept', how='left')

tag_columns = [c for c in df_ppl_count.columns if c not in ['dept', 'global']]
df_final_department[tag_columns + ['global']] = df_final_department[tag_columns + ['global']].fillna(0).astype(int)
df_final_department['prepa_count'] = df_final_department['prepa_count'].fillna(0).astype(int)

politics_cols = [col for col in politics_tags if col in df_final_department.columns]
df_final_department['politics'] = df_final_department[politics_cols].sum(axis=1)

# Which department produces the most leaders compared to their demographic weight when these Leaders were born ?
# Calculating demographic exposition of the department
df_final_department['expo_demog'] = 0
cols_to_fix = [c for c in weights.index if c in df_final_department.columns]
df_final_department[cols_to_fix] = df_final_department[cols_to_fix].apply(pd.to_numeric, errors='coerce').fillna(0)

for decade, weight in weights.items():
    if decade in df_final_department.columns:
        df_final_department['expo_demog'] += df_final_department[decade] * weight

# Prepa rate is the amount of preparatory classes per 1000 people in the demographic exposure index
df_final_department['prepa_rate'] = df_final_department['prepa_count'] / df_final_department['expo_demog'] * 1000

# Cleaning
df_final_department['global'] = df_final_department['global'].fillna(0).astype(int)
ordered_cols = ['dept', 'dept_num', 'global', 'politics'] + tag_columns + ['median', 'poverty_rate', 'expo_demog', 'colleges', 'lycees_pro', 'lycees_gt', 'second_degre', 'cadres_and_pro', 'activity_rate', 'tertiaire', 'prepa_count', 'prepa_rate']
df_final_department = df_final_department[ordered_cols]
df_final_department.to_csv(base_path / "analysis/processed/analysis_department.csv", index=False, sep=";")


# Creating the Region dataframe with economic and demographic data
# Counting personalities per region
df_ppl_count = df_ppl.groupby(['region', 'tag']).size().reset_index(name='count')
df_ppl_count = df_ppl_count.pivot_table(index='region', columns='tag', values='count', fill_value=0).reset_index()
df_ppl_count.columns.name = None
df_ppl_count['global'] = df_ppl_count.select_dtypes(include=['number']).sum(axis=1)
df_prepa_reg = df_prepa.groupby('region').size().reset_index(name='prepa_count')

# Obtaining regional population per decade
df_final_region = df_popr.copy()

# Merging personnalities count and economic data
df_final_region = pd.merge(df_final_region, df_ppl_count, on='region', how='left')
df_final_region = pd.merge(df_final_region, df_prepa_reg, on='region', how='left')
df_eco_subset = df_ecor[['region', 'median_euro', 'poverty_rate', 'colleges', 'lycees_pro', 'lycees_gt', 'second_degre', 'cadres_and_pro', 'activity_rate', 'tertiaire']]

df_eco_subset['median_euro'] = (df_eco_subset['median_euro'].astype(str).str.replace('\u202f', '', regex=False).str.replace(',', '.', regex=False).pipe(pd.to_numeric, errors='coerce'))
df_final_region = pd.merge(df_final_region, df_eco_subset, on='region', how='left')
tag_columns = [c for c in df_ppl_count.columns if c not in ['region', 'global']]
df_final_region[tag_columns + ['global']] = df_final_region[tag_columns + ['global']].fillna(0).astype(int)
df_final_region['prepa_count'] = df_final_region['prepa_count'].fillna(0).astype(int)

politics_cols = [col for col in politics_tags if col in df_final_region.columns]
df_final_region['politics'] = df_final_region[politics_cols].sum(axis=1)

# Calculating demographic exposition of the region
df_final_region['expo_demog'] = 0
cols_to_fix = [c for c in weights.index if c in df_final_region.columns]
df_final_region[cols_to_fix] = df_final_region[cols_to_fix].apply(pd.to_numeric, errors='coerce').fillna(0)

for decade, weight in weights.items():
    if decade in df_final_region.columns:
        df_final_region['expo_demog'] += df_final_region[decade] * weight

# Prepa rate is the amount of preparatory classes per 1000 people in the demographic exposure index
df_final_region['prepa_rate'] = df_final_region['prepa_count'] / df_final_region['expo_demog'] * 1000

# Cleaning
df_final_region['global'] = df_final_region['global'].fillna(0).astype(int)
ordered_cols = ['region', 'global', 'politics'] + tag_columns + ['median_euro', 'poverty_rate', 'expo_demog', 'colleges', 'lycees_pro', 'lycees_gt', 'second_degre', 'cadres_and_pro', 'activity_rate', 'tertiaire', 'prepa_count', 'prepa_rate']
df_final_region = df_final_region[ordered_cols]
df_final_region.to_csv(base_path / "analysis/processed/analysis_region.csv", index=False, sep=";")