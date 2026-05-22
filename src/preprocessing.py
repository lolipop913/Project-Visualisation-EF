import pandas as pd
import pycountry
from .harmonization import harmonize_country_names, iso2_to_iso3


def load_ef_epi(path):
    df = pd.read_csv(path)

    df = df.rename(columns={
        'Country': 'country',
        'Year': 'year',
        'Score': 'score'
    })

    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['score'] = pd.to_numeric(df['score'], errors='coerce')

    mapping = {
        k.lower(): v
        for k, v in harmonize_country_names().items()
    }

    df['country_clean'] = (
        df['country']
        .astype(str)
        .str.strip()
        .apply(lambda x: mapping.get(x.lower(), x))
    )

    def safe_lookup(country):
        try:
            return pycountry.countries.lookup(country).alpha_2
        except LookupError:
            print(f"Country not found: {country}")
            return None

    df['iso2'] = df['country_clean'].apply(
        lambda x: safe_lookup(x) if pd.notna(x) else None
    )

    df['iso3'] = df['iso2'].apply(iso2_to_iso3)

    return df.dropna(subset=['iso3', 'year', 'score'])


def clean_eurostat(df):
    df = df.rename(columns={c: 'geo' for c in df.columns if 'geo' in c.lower()})
    year_cols = [c for c in df.columns if c.isdigit()]
    id_cols = [c for c in df.columns if c not in year_cols]
    df = df.melt(id_vars=id_cols, var_name='year', value_name='value')
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    if 'sex' in df.columns and 'T' in df['sex'].unique():
        df = df[df['sex'] == 'T']
    if 'unit' in df.columns:
        df = df[df['unit'] == 'PC']
    df = df[~df['language'].isin(['TOTAL', 'UNK', 'OTH'])]
    df = df[df['language'] == 'ENG']
    df = df[df['geo'].str.len() == 2]
    df['iso3'] = df['geo'].apply(iso2_to_iso3)
    df = df[df['iso3'].notna()]
    df = df.rename(columns={'value': 'learning'})
    df = df[['geo', 'iso3', 'year', 'learning']].dropna(subset=['year', 'learning'])
    return df.groupby(['geo', 'iso3', 'year'], as_index=False)['learning'].mean()


def compute_percentiles(df, value_column, groupby_columns=None, result_column=None):
    result_column = result_column or f'{value_column}_percentile'
    groupby_columns = groupby_columns or ['year']
    df[result_column] = df.groupby(groupby_columns)[value_column].rank(pct=True)
    return df


def merge_datasets(eurostat_df, ef_df):
    ef_df = compute_percentiles(ef_df, 'score', ['year'], 'ef_percentile')
    eurostat_df = compute_percentiles(eurostat_df, 'learning', ['year'], 'learning_percentile')
    merged = eurostat_df.merge(
        ef_df[['iso3', 'year', 'ef_percentile']],
        on=['iso3', 'year'],
        how='left'
    )
    merged['gap_pct'] = merged['ef_percentile'] - merged['learning_percentile']
    return merged
