#%%

import pandas as pd

# Настройка для правильного отображения дробной части чисел
pd.set_option("display.precision", 15)

scopus = pd.read_csv('../data/scopus-sources-2020.csv', dtype={
    "Print ISSN": str,
    "E-ISSN": str
}).fillna({
    "Print ISSN": '-',
    "E-ISSN": '-'
})[['Scopus Source ID', 'Title', 'SNIP', 'Print ISSN', 'E-ISSN']].drop_duplicates(subset=['Scopus Source ID']).reset_index(drop=True)
scopus['Print ISSN'] = scopus['Print ISSN'].apply(lambda x: x if x == '-' or len(x) >= 8 else '0' * (8 - len(x)) + x)
scopus['E-ISSN'] = scopus['E-ISSN'].apply(lambda x: x if x == '-' or len(x) >= 8 else '0' * (8 - len(x)) + x)

cwts = pd.read_csv('../data/cwts-journal-indicators.csv', dtype={
    "Print ISSN": str,
    "Electronic ISSN": str,
})[['Source title', 'Print ISSN', 'Electronic ISSN', 'SNIP', 'SNIP (lower bound)', 'Source type', 'Year']]
cwts = cwts[(cwts['Source type'] == 'Journal') & (cwts['Year'] == 2020)].drop(columns=['Source type', 'Year']).reset_index(drop=True)

#%%

# Создание 2-х абстрактных структуры данных ускорения работы
issn_data = pd.DataFrame(columns=['snip', 'lower_bound'])
eissn_data = pd.DataFrame(columns=['snip', 'lower_bound'])

for i, cwts_row in cwts.iterrows():
    issn_value = cwts_row['Print ISSN'].replace('-', '')
    eissn_value = cwts_row['Electronic ISSN'].replace('-', '')

    if issn_value != '' and issn_value not in issn_data.index:
        issn_data.loc[issn_value] = {
            "snip": cwts_row['SNIP'],
            "lower_bound": cwts_row['SNIP (lower bound)']
        }

    if eissn_value != '' and eissn_value not in eissn_data.index:
        eissn_data.loc[eissn_value] = {
            "snip": cwts_row['SNIP'],
            "lower_bound": cwts_row['SNIP (lower bound)']
        }

#%%

scopus['cwts_snip'] = 0
scopus['cwts_lower_bound'] = 0

for i, scopus_row in scopus.iterrows():
    issn_value = scopus_row['Print ISSN']
    issn_list = issn_value.split(' ') if issn_value != '-' else []
    eissn_value = scopus_row['E-ISSN']
    eissn_list = eissn_value.split(' ') if eissn_value != '-' else []
    found_in_issn = False

    for issn in issn_list:
        if issn in issn_data.index:
            scopus.loc[i, 'cwts_snip'] = issn_data.loc[issn, 'snip']
            scopus.loc[i, 'cwts_lower_bound'] = issn_data.loc[issn, 'lower_bound']
            found_in_issn = True
            break

    if ~found_in_issn:
        for eissn in eissn_list:
            if eissn in eissn_data.index:
                scopus.loc[i, 'cwts_snip'] = eissn_data.loc[eissn, 'snip']
                scopus.loc[i, 'cwts_lower_bound'] = eissn_data.loc[eissn, 'lower_bound']
                break

#%%

thresholds = pd.read_csv('../data/snip-thresholds.csv')[['year', 'threshvalue25', 'threshvalue50']]
year = 2020
q1_threshold = thresholds[thresholds['year'] == year]['threshvalue25'].values[0]
q2_threshold = thresholds[thresholds['year'] == year]['threshvalue50'].values[0]

def get_quartile(row):
    snip = row['cwts_snip']
    lower_bound = row['cwts_lower_bound']

    if lower_bound >= q1_threshold:
        return 'Q1'
    elif snip >= q1_threshold:
        return 'Q1*'
    elif lower_bound >= q2_threshold:
        return 'Q2'
    elif snip >= q2_threshold:
        return 'Q2*'

    return 'Other'


scopus['quartile'] = scopus.apply(get_quartile, axis=1)
groups = scopus.groupby(['quartile']).count().reset_index()[['quartile', 'Scopus Source ID']].rename(columns={
    "Scopus Source ID": "count"
})
scopus.to_csv('../data/result_scopus_sources_with_quartiles_by_priority_2030.csv')
