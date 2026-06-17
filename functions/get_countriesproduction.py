from www.services import *
import os
import tempfile


def get_countries_production(df):
    df = metaTagExtraction(df, 'AU_CO')
    df = df.get()

    df['AU_CO'] = df['AU_CO'].apply(
        lambda x: x if isinstance(x, list) else ([] if pd.isna(x) else [x]))

    def clean_country_names(countries):
        cleaned = []
        for country in countries:
            if isinstance(country, str):
                cleaned.append(country.upper().strip())
        return cleaned

    df['AU_CO'] = df['AU_CO'].apply(clean_country_names)

    country_counts = df['AU_CO'].explode().value_counts().reset_index()
    country_counts.columns = ['Tab', 'Freq']

    # Download world map with cache and fallback
    _cache = os.path.join(tempfile.gettempdir(), 'ne_110m_countries.geojson')
    world  = None

    if os.path.exists(_cache):
        try:
            world = gpd.read_file(_cache)
        except Exception:
            world = None

    if world is None:
        _mirrors = [
            'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson',
            'https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip',
        ]
        import urllib.request
        for _url in _mirrors:
            try:
                world = gpd.read_file(_url)
                try:
                    world.to_file(_cache, driver='GeoJSON')
                except Exception:
                    pass
                break
            except Exception:
                continue

    if world is None:
        fig = go.Figure()
        fig.update_layout(
            title='World map unavailable (network error). Countries data loaded.',
            height=300)
        return fig, country_counts

    world['Nations'] = world['SOVEREIGNT'].str.upper().str.strip()
    world = world.dissolve(by='Nations').reset_index()
    country_prod = world.merge(country_counts, how='left',
                               left_on='Nations', right_on='Tab')
    country_prod = country_prod.drop_duplicates(subset=['Nations'])
    country_prod['Freq'] = country_prod['Freq'].fillna(0)

    fig = px.choropleth(
        country_prod,
        geojson=country_prod.geometry,
        locations=country_prod.index,
        color='Freq',
        hover_name='Nations',
        color_continuous_scale='Blues',
        labels={'Freq': 'N. of Documents'},
    )
    fig.update_geos(showframe=False, showcoastlines=True,
                    projection_type='equirectangular')
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title='N. of Documents'),
        hoverlabel=dict(bgcolor='white', font_size=13,
                        font_family='Segoe UI, Arial', bordercolor='#5567BB'),
    )
    
    

    table = country_prod[['Nations', 'Freq']].dropna().sort_values(
        'Freq', ascending=False).reset_index(drop=True)
    table.columns = ['Country', 'Frequency']

    return fig, table
