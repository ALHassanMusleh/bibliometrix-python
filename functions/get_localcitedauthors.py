from www.services import *


def get_local_cited_authors(df, num_of_cited_authors, fast_search=False):
    if fast_search:
        loccit = df.get()['TC'].quantile(0.75)
    else:
        loccit = 1

    df = metaTagExtraction(df, 'SR')
    M  = df.get()
    M['TC'] = M['TC'].fillna(0)

    H = histNetwork(df, min_citations=loccit, sep=';', network=False)

    # Guard: histNetwork returns None when DB is not compatible
    if H is None:
        fig = go.Figure()
        fig.update_layout(
            title='Local citation analysis not available for this database/dataset',
            height=200)
        empty = pd.DataFrame(columns=['Authors', 'N. of Local Citations'])
        return fig, empty

    LCS = H['histData']
    M   = H['M']

    AU = M['AU'].explode()
    n  = AU.groupby(level=0).size()

    df_authors   = pd.DataFrame({'AU': AU, 'LCS': M['LCS'].repeat(n).values})
    author_counts = df_authors.groupby('AU')['LCS'].sum().reset_index()
    author_counts.columns = ['Authors', 'N. of Local Citations']
    author_counts = author_counts.sort_values(by='N. of Local Citations', ascending=False)

    if num_of_cited_authors > len(author_counts):
        num_of_cited_authors = len(author_counts)

    table_located_authors = author_counts.copy()
    author_counts = author_counts.head(num_of_cited_authors).reset_index(drop=True)

    frequency = 'N. of Local Citations'
    max_x = float(author_counts[frequency].max()) if len(author_counts) > 0 else 1

    fig = go.Figure()

    for i, row in author_counts.iterrows():
        fig.add_shape(type='line', x0=0, x1=row[frequency], y0=i, y1=i,
                      line=dict(color='#e0e0e0', width=5), layer='below')

    fig.add_trace(go.Scatter(
        x=author_counts[frequency],
        y=list(range(len(author_counts))),
        mode='markers+text',
        marker=dict(
            size=18 + 6 * (author_counts[frequency] / max_x if max_x > 0 else 1),
            color=author_counts[frequency],
            colorscale=[[0, '#B3D1F2'], [1, '#5567BB']],
            line=dict(width=1, color='#E0E0E0'),
            opacity=0.95, showscale=False,
        ),
        text=author_counts[frequency],
        textposition='top center',
        textfont=dict(color='#5567BB', size=13),
        hovertemplate=(
            '<b>Author:</b> %{customdata}<br>'
            f'<b>{frequency}:</b> %{{x}}<extra></extra>'
        ),
        customdata=author_counts['Authors'],
    ))

    for i in range(len(author_counts)):
        fig.add_shape(type='line', x0=0, x1=max_x, y0=i, y1=i,
                      line=dict(color='#E0E0E0', width=2), layer='below')

    tick_step = max(1, int(max_x // 5))
    x_ticks   = list(range(0, int(max_x) + tick_step, tick_step))

    fig.update_yaxes(tickvals=list(range(len(author_counts))),
                     ticktext=author_counts['Authors'],
                     autorange='reversed', showgrid=False,
                     title='Authors', tickfont=dict(size=13))
    fig.update_xaxes(showgrid=True, gridcolor='#F0F0F0', zeroline=False,
                     tickvals=x_ticks, title=frequency,
                     tickfont=dict(size=13), range=[0, max_x * 1.1])
    fig.update_layout(
        plot_bgcolor='white',
        font=dict(color='#222222', size=14, family='Segoe UI, Arial'),
        margin=dict(l=0, r=0, t=0, b=0),
        height=50 + 90 * len(author_counts),
        showlegend=False,
        hoverlabel=dict(bgcolor='white', font_size=13,
                        font_family='Segoe UI, Arial', bordercolor='#5567BB'),
        coloraxis_showscale=False,
    )
    
    
    return fig, table_located_authors
