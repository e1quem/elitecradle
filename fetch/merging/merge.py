from pathlib import Path
import pandas as pd
import unicodedata
import re

base_path = Path("~/elitecradle").expanduser()

def normalize_text(text):
    if pd.isna(text):
        return text
    # No caps, deleting spaces
    text = str(text).lower().strip()
    # Deleting diactics
    text = "".join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    # Capitalize the first letter
    return text.capitalize()

df_dp = pd.read_csv(base_path / "fetch/parliament/out/an_clean.csv", sep=None, engine='python')
df_mn = pd.read_csv(base_path / "fetch/ministers/out/mn_clean.csv", sep=None, engine='python')
df_pr = pd.read_csv(base_path / "fetch/presidents/out/presidents_clean.csv", sep=None, engine='python')
df_sn = pd.read_csv(base_path / "fetch/senators/out/sn_clean.csv", sep=None, engine='python')
df_cf = pd.read_csv(base_path / "fetch/scholars/out/cf_clean.csv", sep=None, engine='python')
df_cfBIS = pd.read_csv(base_path / "fetch/scholars/out/scholars_clean.csv", sep=None, engine='python')
df_executives = pd.read_csv(base_path / "fetch/executives/out/exec_clean.csv", sep=None, engine='python')
df_executivesBIS = pd.read_csv(base_path / "fetch/executives/out/CEOs_clean.csv", sep=None, engine='python')
df_executivesTER = pd.read_csv(base_path / "fetch/executives/out/business_person_clean.csv", sep=None, engine='python')

df = pd.concat([df_dp, df_mn, df_pr, df_sn, df_cf, df_cfBIS, df_executives, df_executivesBIS, df_executivesTER], ignore_index=True)

# Normalizing dob
df['dob'] = pd.to_numeric(df['dob'], errors='coerce').astype('Int64')

# We group lines sharing the same name and dob
# Tag hierarchy
hierarchy = ['president', 'minister', 'college_de_france', 'scholar', 'executive', 'executiveBIS', 'executiveTER', 'senat', 'parliament']
df['tag'] = pd.Categorical(df['tag'], categories=hierarchy, ordered=True)
df = df.sort_values('tag')
df = df.groupby(['name', 'dob'], as_index=False).first()

# We fusion columns
df['department'] = df.pop('dep_name').fillna(df.pop('dept_ob'))
df['dept_num'] = df.pop('dep_num').fillna(df.pop('dept_num'))

# Normalizing pob
df['pob'] = df['pob'].apply(normalize_text)

# Deleting parliamentes ids and data.gouv API confidence indicator
df = df.drop(columns=['id', 'confidence'], errors='ignore')

# Column order
order = ['name', 'dob', 'tag', 'pob', 'department', 'dept_num', 'region', 'lat', 'lon']
existing_cols = [c for c in order if c in df.columns]
df = df[existing_cols]

output_path = base_path / "fetch/merging/interim/merged_raw.csv"
df.to_csv(output_path, index=False, encoding='utf-8')