import pycountry


def harmonize_country_names():
    return {
        'Czech Republic': 'Czechia',
        'Russia': 'Russian Federation',
        'Macedonia': 'North Macedonia',
        'United Kingdom': 'United Kingdom',
        'UK': 'United Kingdom',
        'Kosovo': 'Kosovo',
        'turkey': 'Turkey',
        'Türkiye': 'Turkey'
    }


def iso2_to_iso3(code):
    try:
        return pycountry.countries.get(alpha_2=code).alpha_3
    except Exception:
        return None