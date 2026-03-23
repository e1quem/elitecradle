import pandas as pd

df_source = pd.read_excel("/Users/eyquem/Desktop/LeadersMap/analysis/sources/base-pop-historiques-1876-2023.xlsx", header=5)
path_export = "/Users/eyquem/Desktop/LeadersMap/analysis/interim/"

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

# Region regrouping
df_region = df.drop(columns=['DEP']).groupby('REG').sum().reset_index()

# Swithing from INSEE code to official names
mapping_regions = {
    1: "Guadeloupe", 2: "Martinique", 3: "Guyane", 4: "La Réunion",
    11: "Île-de-France", 24: "Centre-Val de Loire", 27: "Bourgogne-Franche-Comté",
    28: "Normandie", 32: "Hauts-de-France", 44: "Grand Est",
    52: "Pays de la Loire", 53: "Bretagne", 75: "Nouvelle-Aquitaine",
    76: "Occitanie", 84: "Auvergne-Rhône-Alpes", 93: "Provence-Alpes-Côte d'Azur",
    94: "Corse"
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
    '973': "Guyane", '974': "La Réunion", '976': "Mayotte"
}

df_region['region'] = df_region['REG'].map(mapping_regions)
cols_reg = ['REG', 'region'] + [c for c in df_region.columns if c not in ['REG', 'region']]
df_region = df_region[cols_reg]
df_region = df_region.round(0).fillna(0).astype(int, errors='ignore')
df_region.to_csv(f"{path_export}pop_region.csv", index=False, sep=";")

# Department regrouping
df['DEP'] = df['DEP'].astype(str).str.zfill(2)
df_dept = df.groupby('DEP').sum().reset_index()
df_dept['dept'] = df_dept['DEP'].map(mapping_depts)
df_dept = df_dept.round(0).fillna(0).astype(int, errors='ignore')
cols_dept = ['DEP', 'dept'] + [c for c in df_dept.columns if c not in ['DEP', 'dept', 'REG']]
df_dept[cols_dept].to_csv(f"{path_export}pop_dept.csv", index=False, sep=";")

print("Successful export !")
