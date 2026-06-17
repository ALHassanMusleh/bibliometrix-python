from www.services import *


def get_trend_topics(df, ngram, field_tt, time_window, file_upload_terms_tt,
                     file_upload_synonyms_tt, word_minimum_frequency, number_of_words_year):
    field  = field_tt
    remove_terms = None
    synonyms     = None

    if file_upload_terms_tt:
        remove_terms = file_upload_terms_tt
    if file_upload_synonyms_tt:
        synonyms = file_upload_synonyms_tt

    # time_window from UI is an int — convert to None so field_by_year auto-detects range
    timespan = None
    if isinstance(time_window, (list, tuple)) and len(time_window) == 2:
        timespan = time_window

    trend_topics = field_by_year(df, field, timespan, word_minimum_frequency,
                                 number_of_words_year, remove_terms, synonyms)

    fig = px.scatter(trend_topics, x='year_med', y='item', size='freq',
                     hover_data=['year_q1', 'year_q3'], height=800)
    fig.update_layout(
        xaxis_title='Year', yaxis_title='Term', showlegend=False,
        plot_bgcolor='white',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='lightgrey'),
        hoverlabel=dict(bgcolor='white', font_size=13,
                        font_family='Segoe UI, Arial', bordercolor='#5567BB'),
    )
    fig.update_traces(
        hovertemplate=(
            '<b>Term:</b> %{y}<br>'
            '<b>Median Year:</b> %{x}<br>'
            '<b>Frequency:</b> %{marker.size}<br>'
            '<b>Q1 Year:</b> %{customdata[0]}<br>'
            '<b>Q3 Year:</b> %{customdata[1]}<br>'
            '<extra></extra>'
        ),
        customdata=trend_topics[['year_q1', 'year_q3']].values
    )

    for i in range(len(trend_topics)):
        fig.add_shape(
            type='line',
            x0=trend_topics['year_q1'].iloc[i], y0=trend_topics['item'].iloc[i],
            x1=trend_topics['year_q3'].iloc[i], y1=trend_topics['item'].iloc[i],
            line=dict(color='lightblue', width=5), layer='below'
        )

    fig.update_traces(marker=dict(color='dodgerblue', opacity=1),
                      selector=dict(mode='markers'))
    
    
    return fig, trend_topics


def field_by_year(df, field, timespan, min_freq, n_items,
                  remove_terms=None, synonyms=None):
    import numpy as np

    A = cocMatrix(df, Field=field, binary=False,
                  remove_terms=remove_terms, synonyms=synonyms)
    n   = A.sum(axis=0).to_numpy()
    dfm = df.get()

    trend_med = pd.DataFrame(A.values).apply(
        lambda x: pd.Series(np.round(
            np.quantile(np.repeat(dfm['PY'], x), [0.25, 0.5, 0.75])
        )), axis=0
    ).T
    trend_med.columns = ['year_q1', 'year_med', 'year_q3']
    trend_med['freq'] = n
    trend_med['item'] = A.columns

    if timespan is None or not (isinstance(timespan, (list, tuple)) and len(timespan) == 2):
        timespan = [trend_med['year_med'].min(), trend_med['year_med'].max()]

    trend_med = trend_med[
        (trend_med['year_med'] >= timespan[0]) &
        (trend_med['year_med'] <= timespan[1])
    ]
    trend_med = trend_med[trend_med['freq'] >= min_freq]

    # Use sort + head instead of groupby to keep year_med column
    trend_med = (trend_med
                 .sort_values(['year_med', 'freq'], ascending=[True, False])
                 .groupby('year_med', group_keys=False, sort=False)
                 .head(n_items)
                 .reset_index(drop=True))

    return trend_med
