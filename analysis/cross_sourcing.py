from rapidfuzz import process, fuzz
import unicodedata
import pandas as pd

# Economic indicators
df_ecoc = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/interim/eco_city.csv", sep=None, engine='python')
df_ecod = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/interim/eco_dept.csv", sep=None, engine='python')
df_ecor = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/interim/eco_region.csv", sep=None, engine='python')

# Demographic indicators
df_popc = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/interim/pop_city.csv", sep=None, engine='python')
df_popd = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/interim/pop_dept.csv", sep=None, engine='python')
df_popr = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/interim/pop_region.csv", sep=None, engine='python')

# Personnalities
df_ppl = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/analysis/interim/merged_clean.csv", sep=None, engine='python')

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
    return str(code).strip()[:-3]

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
for df in [df_ppl, df_popc]:
    df['dept'] = df['dept'].apply(to_dept_type)

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

# Start from the demographic base and merge personalities and economic data
df_final_city = df_popc.copy()
df_final_city = pd.merge(df_final_city, df_ppl_count, on=['pob', 'dept'], how='left')
df_final_city = pd.merge(df_final_city, df_ecoc[['pob', 'dept', 'median']], on=['pob', 'dept'], how='left')
tag_columns = [c for c in df_ppl_count.columns if c not in ['pob', 'dept', 'global']]
df_final_city[tag_columns + ['global']] = df_final_city[tag_columns + ['global']].fillna(0).astype(int)

politics_tags = ['depute', 'senate', 'minister', 'president']
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

# Retain only cities that produced at least one personality
df_final_city = df_final_city[df_final_city['global'] > 0].copy()
df_final_city['global'] = df_final_city['global'].fillna(0).astype(int)
ordered_cols = ['pob', 'dept', 'global', 'politics'] + tag_columns + ['median', 'expo_demog']
df_final_city = df_final_city[ordered_cols]

df_final_city.to_csv("/Users/eyquem/Desktop/LeadersMap/analysis/processed/analysis_city.csv", index=False, sep=";")





### Faire par arrondissement de paris : trouver population et richesse




# Creating the Department dataframe with economic and demographic data
# Counting personalities per department
df_ppl_count = df_ppl.groupby(['department', 'tag']).value_counts().reset_index(name='count')
df_ppl_count = df_ppl_count.pivot_table(index='department', columns='tag', values='count', fill_value=0).reset_index()
df_ppl_count.columns.name = None
df_ppl_count['global'] = df_ppl_count.select_dtypes(include=['number']).sum(axis=1)
df_ppl_count = df_ppl_count.rename(columns={'department': 'dept'})


# Obtaining departmental population per decade
df_final_department = df_popd.copy()

# Merging personnalities count and economic data
df_final_department = pd.merge(df_final_department, df_ppl_count, on='dept', how='left')
df_eco_subset = df_ecod[['dept', 'median', 'poverty_rate']]
df_final_department = pd.merge(df_final_department, df_eco_subset, on='dept', how='left')

tag_columns = [c for c in df_ppl_count.columns if c not in ['dept', 'global']]
df_final_department[tag_columns + ['global']] = df_final_department[tag_columns + ['global']].fillna(0).astype(int)

politics_tags = ['depute', 'senate', 'minister', 'president']
politics_cols = [col for col in politics_tags if col in df_final_department.columns]
df_final_department['politics'] = df_final_department[politics_cols].sum(axis=1)

# Which department produces the most leaders compared to their demographic weight when these Leaders were born ?
# Calculating demographic exposition of the department
df_final_department['expo_demog'] = 0

# Avoiding TypeError
cols_to_fix = [c for c in weights.index if c in df_final_department.columns]
df_final_department[cols_to_fix] = df_final_department[cols_to_fix].apply(pd.to_numeric, errors='coerce').fillna(0)

for decade, weight in weights.items():
    if decade in df_final_department.columns:
        df_final_department['expo_demog'] += df_final_department[decade] * weight

# Cleaning
df_final_department['global'] = df_final_department['global'].fillna(0).astype(int)
ordered_cols = ['dept', 'global', 'politics'] + tag_columns + ['median', 'poverty_rate', 'expo_demog']
df_final_department = df_final_department[ordered_cols]

df_final_department.to_csv("/Users/eyquem/Desktop/LeadersMap/analysis/processed/analysis_department.csv", index=False, sep=";")


# Creating the Region dataframe with economic and demographic data
# Counting personalities per region
df_ppl_count = df_ppl.groupby(['region', 'tag']).size().reset_index(name='count')
df_ppl_count = df_ppl_count.pivot_table(index='region', columns='tag', values='count', fill_value=0).reset_index()
df_ppl_count.columns.name = None
df_ppl_count['global'] = df_ppl_count.select_dtypes(include=['number']).sum(axis=1)

# Obtaining regional population per decade
df_final_region = df_popr.copy()

# Merging personnalities count and economic data
df_final_region = pd.merge(df_final_region, df_ppl_count, on='region', how='left')
df_eco_subset = df_ecor[['region', 'median_euro', 'poverty_rate']]
df_eco_subset['median_euro'] = (df_eco_subset['median_euro'].astype(str).str.replace('\u202f', '', regex=False).str.replace(',', '.', regex=False).pipe(pd.to_numeric, errors='coerce'))
df_final_region = pd.merge(df_final_region, df_eco_subset, on='region', how='left')
tag_columns = [c for c in df_ppl_count.columns if c not in ['region', 'global']]
df_final_region[tag_columns + ['global']] = df_final_region[tag_columns + ['global']].fillna(0).astype(int)

politics_tags = ['depute', 'senate', 'minister', 'president']
politics_cols = [col for col in politics_tags if col in df_final_region.columns]
df_final_region['politics'] = df_final_region[politics_cols].sum(axis=1)

# Calculating demographic exposition of the region
df_final_region['expo_demog'] = 0

# Avoiding TypeError
cols_to_fix = [c for c in weights.index if c in df_final_region.columns]
df_final_region[cols_to_fix] = df_final_region[cols_to_fix].apply(pd.to_numeric, errors='coerce').fillna(0)

for decade, weight in weights.items():
    if decade in df_final_region.columns:
        df_final_region['expo_demog'] += df_final_region[decade] * weight

# Cleaning
df_final_region['global'] = df_final_region['global'].fillna(0).astype(int)
ordered_cols = ['region', 'global', 'politics'] + tag_columns + ['median_euro', 'poverty_rate', 'expo_demog']
df_final_region = df_final_region[ordered_cols]

df_final_region.to_csv("/Users/eyquem/Desktop/LeadersMap/analysis/processed/analysis_region.csv", index=False, sep=";")