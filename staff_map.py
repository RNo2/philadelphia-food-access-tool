"""Top-25 geographic planning, with explicit distance and location assumptions."""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

SHARE_ADDRESS = '2901 W. Hunting Park Avenue, Philadelphia, PA 19129'
# Approximate planning location only; editable until a staff-confirmed pin is available.
SHARE_LAT = 40.008
SHARE_LON = -75.18


def miles_between(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = [np.radians(v) for v in (lat1, lon1, lat2, lon2)]
    h = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    return 3958.7613 * 2 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def select_top_schools(ranked, types, levels):
    # Keep deterministic scenario ordering, including tie breakers from the app.
    return ranked[ranked['Type'].isin(types or ranked['Type'].dropna().unique()) & ranked['Level'].isin(levels or ranked['Level'].dropna().unique())].head(25).copy()


def distance_tables(schools, hub_lat, hub_lon):
    mapped = schools[schools['Latitude'].between(-90, 90) & schools['Longitude'].between(-180, 180)].copy().reset_index(drop=True)
    mapped['Miles from Share (approx.)'] = miles_between(hub_lat, hub_lon, mapped['Latitude'].to_numpy(), mapped['Longitude'].to_numpy())
    pairs = []
    matrix = np.zeros((len(mapped), len(mapped)))
    for i in range(len(mapped)):
        for j in range(i+1, len(mapped)):
            a, b = mapped.iloc[i], mapped.iloc[j]
            distance = float(miles_between(a['Latitude'], a['Longitude'], b['Latitude'], b['Longitude']))
            matrix[i, j] = matrix[j, i] = distance
            pairs.append({'School A': a['School'], 'School B': b['School'], 'School ID A': a['School ID'], 'School ID B': b['School ID'], 'Miles apart': distance,
                          'source': [float(a['Longitude']), float(a['Latitude'])], 'target': [float(b['Longitude']), float(b['Latitude'])]})
    pairs = pd.DataFrame(pairs, columns=['School A', 'School B', 'School ID A', 'School ID B', 'Miles apart', 'source', 'target'])
    return mapped, pairs.sort_values('Miles apart'), matrix



def spacing_recommendation(schools, minimum_miles):
    """Priority-first feasible shortlist; not a maximum-cardinality optimization."""
    if not np.isfinite(minimum_miles) or minimum_miles < 0:
        raise ValueError('Minimum spacing must be finite and nonnegative.')
    ordered = schools.sort_values(['Scenario score', 'Economic %', 'Enrollment', 'School ID'], ascending=[False, False, False, True]).copy()
    kept = []
    decisions = []
    for _, school in ordered.iterrows():
        valid = pd.notna(school['Latitude']) and pd.notna(school['Longitude']) and -90 <= school['Latitude'] <= 90 and -180 <= school['Longitude'] <= 180
        conflicts = []
        if valid:
            for previous in kept:
                distance = float(miles_between(school['Latitude'], school['Longitude'], previous['Latitude'], previous['Longitude']))
                if distance <= minimum_miles:
                    conflicts.append((previous, distance))
        if not valid:
            decision, reason = 'Needs coordinate review', 'Missing or invalid coordinates; spacing cannot be verified.'
        elif conflicts:
            decision = 'Leave out'
            reason = '; '.join(f"{previous['School']} ({distance:.2f} mi)" for previous, distance in conflicts)
        else:
            decision, reason = 'Recommend', 'No conflict with a higher-priority recommended school.'
            kept.append(school)
        decisions.append({'School ID': school['School ID'], 'Decision': decision, 'Reason / conflicting recommended schools': reason})
    return ordered.merge(pd.DataFrame(decisions, columns=['School ID', 'Decision', 'Reason / conflicting recommended schools']), on='School ID', how='left', validate='one_to_one')


def render_spacing_results(decisions, pairs, minimum_miles, weights):
    st.subheader('Spacing recommendations')
    st.caption(f'Applies to the currently filtered top 25 only. Schools at or within {minimum_miles:g} straight-line miles cannot both be recommended. This tool does not refill the list from outside the displayed group.')
    st.write('We consider schools in rubric-priority order: scenario score, economic disadvantage, enrollment, then School ID. Keep the highest-priority school, then keep each next school only if it clears every already recommended school. This favors priority; it does not guarantee the largest possible number of schools or maximum total score.')
    cols = ['School', 'School ID', 'Scenario score', 'Type', 'Level', 'Decision', 'Reason / conflicting recommended schools']
    st.dataframe(decisions[cols], hide_index=True, use_container_width=True)
    recommended = decisions[decisions['Decision'].eq('Recommend')]
    st.success(f'{len(recommended)} schools recommended; {int(decisions["Decision"].eq("Leave out").sum())} left out because of spacing.')
    if decisions['Decision'].eq('Needs coordinate review').any():
        st.warning('Schools without valid coordinates are withheld from the spacing shortlist pending review.')
    export = decisions[cols].assign(**{'Minimum separation (mi)': minimum_miles, 'Selection rule': 'Priority-first spacing', **{f'Weight: {name}': value for name, value in weights.items()}})
    st.download_button('Download spacing decisions', export.to_csv(index=False).encode('utf-8'), 'school_spacing_decisions.csv', 'text/csv')
    st.download_button('Download recommended schools', export[export['Decision'].eq('Recommend')].to_csv(index=False).encode('utf-8'), 'spacing_recommended_schools.csv', 'text/csv')
    st.markdown('#### Nearby-school rubric comparisons')
    comparison = pairs[pairs['Miles apart'] <= minimum_miles][['School ID A', 'School ID B', 'Miles apart']].copy()
    components = [('Economic contribution', 'Economic points', 'Economic need', 30), ('Fresh-access contribution', 'Fresh points', 'Fresh food access', 25), ('Resource-gap contribution', 'Resource points', 'Resource gap', 25), ('Reach contribution', 'Reach points', 'Potential reach', 5)]
    evidence = decisions[['School ID', 'School', 'Scenario score', 'Economic %', 'Enrollment', 'Effective fresh miles', 'Effective resources', 'Decision', 'Reason / conflicting recommended schools']].copy()
    evidence['Economic %'] *= 100
    for label, column, weight, maximum in components:
        evidence[label] = decisions[column] / maximum * weights[weight]
    for side in ['A', 'B']:
        comparison = comparison.merge(evidence.rename(columns={column: f'{side}: {column}' for column in evidence.columns}), left_on=f'School ID {side}', right_on=f'{side}: School ID', how='left')
    if comparison.empty:
        st.info('No school pairs violate this spacing rule in the displayed group.')
    else:
        st.caption('Both schools appear with their current weighted rubric contributions. A pair can have both schools left out if each conflicts with a different recommended school; use the decision reasons to trace the complete shortlist. Economic % is displayed on a 0–100 scale.')
    st.dataframe(comparison, hide_index=True, use_container_width=True, column_config={'Miles apart': st.column_config.NumberColumn(format='%.2f')})
    st.download_button('Download pair-by-pair rubric comparisons', comparison.to_csv(index=False).encode('utf-8'), 'spacing_rubric_comparisons.csv', 'text/csv')

def render_staff_map(ranked, all_schools, weights):
    st.title('Distance review')
    service = pd.read_csv(Path(__file__).resolve().parent / 'data/served_schools.csv', dtype={'School ID': str})
    served_ids = service.loc[service['Service status'].eq('Currently served'), 'School ID']
    ranked = ranked.copy()
    ranked['Service status'] = np.where(ranked['School ID'].isin(served_ids), 'Currently served', 'Not listed as currently served')
    service_filter = st.multiselect('Served Schools', ['Currently served', 'Not listed as currently served'], key='staff_service')
    if service_filter:
        ranked = ranked[ranked['Service status'].isin(service_filter)]
    st.write('Compare the top 25 expansion priorities, their distances from Share, and schools clustered in the same area. Sidebar scenario weights update the selection.')
    st.info('Distances are straight-line miles, not driving routes or travel times. Close schools are review flags, not proof of duplicate service or a reason to exclude a school automatically.')
    with st.expander('Share dispatch location · approximate pin — confirm before route planning'):
        address = st.text_input('Share dispatch address / label', key='staff_hub_address')
        st.caption('When location fields are blank, the map uses Share Food Program Philadelphia headquarters at 2901 W. Hunting Park Avenue (approximate pin). Live geocoding is unavailable here, so the initial pin is an approximate planning location. Editing the address label does not move the pin; enter confirmed coordinates below. Changes last for this session.')
        x, y = st.columns(2)
        hub_lat = x.number_input('Share latitude', min_value=-90.0, max_value=90.0, value=None, format='%.6f', key='staff_hub_lat')
        hub_lon = y.number_input('Share longitude', min_value=-180.0, max_value=180.0, value=None, format='%.6f', key='staff_hub_lon')
    address = address or SHARE_ADDRESS
    hub_lat = hub_lat if hub_lat is not None else SHARE_LAT
    hub_lon = hub_lon if hub_lon is not None else SHARE_LON
    a, b = st.columns(2)
    types = a.multiselect('School type', sorted(ranked['Type'].dropna().unique()), key='staff_types')
    levels = b.multiselect('School level', sorted(ranked['Level'].dropna().unique()), key='staff_levels')
    st.caption('Combined grade levels are shown as recorded (for example Elementary-Middle). Filters apply before ranking selection: the map fills up to 20 schools from the chosen types and levels. Empty filters show all service groups. Fewer appear only when fewer than 25 eligible schools match. Scenario rank remains the citywide comparison rank.')
    schools = select_top_schools(ranked, types, levels)
    mapped, pairs, matrix = distance_tables(schools, hub_lat, hub_lon)
    threshold_input = st.number_input('Flag school pairs closer than (miles)', min_value=0.1, max_value=3.0, value=None, step=0.1, key='staff_threshold')
    threshold = threshold_input if threshold_input is not None else 0
    minimum_spacing = st.number_input('Minimum school separation (miles)', min_value=0.0, max_value=50.0, value=None, step=0.1, key='staff_spacing')
    decisions = spacing_recommendation(schools, minimum_spacing) if minimum_spacing is not None else None
    st.caption('Optional spacing rule: enter miles to recommend a shortlist where no two schools are at or within that distance. Blank leaves recommendations off. Rubric weights in the sidebar update the choices.')
    st.caption('Enter a distance threshold to highlight close school pairs; blank means no proximity flags.')
    close = pairs[pairs['Miles apart'] < threshold].copy()
    a, b, c = st.columns(3)
    a.metric('Schools selected', len(schools))
    b.metric('School pairs flagged', len(close))
    c.metric('Schools missing valid coordinates', len(schools)-len(mapped))
    if len(schools) != len(mapped):
        st.warning('Some selected schools have no valid coordinates. They remain in the selected-school list but cannot appear in the map or distance comparisons.')
    a, b = st.columns(2)
    names = a.checkbox('Show school names', False, key='staff_names')
    spokes = b.checkbox('Show Share-to-school connections', False, key='staff_spokes')
    style = st.selectbox('Map background', ['Street', 'Light', 'Dark'], index=None, key='staff_style')
    hub = pd.DataFrame([{'Longitude': hub_lon, 'Latitude': hub_lat, 'label': '◆ SHARE (approx.)', 'tip': 'Share Food Program'}])
    layers = [pdk.Layer('ScatterplotLayer', hub, id='share-hub', get_position='[Longitude, Latitude]', get_radius=200, radius_min_pixels=14, get_fill_color=[190,35,50], pickable=True),
              pdk.Layer('TextLayer', hub, id='share-label', get_position='[Longitude, Latitude]', get_text='label', get_color=[190,35,50], get_size=16, get_pixel_offset=[0,-28])]
    view_points = [[hub_lon, hub_lat]]
    if not mapped.empty:
        mapped['number'] = mapped['Order'].astype(str)
        mapped['name_label'] = mapped['Order'].astype(str) + ' · ' + mapped['School']
        mapped['tip'] = mapped['School']
        mapped['marker_color'] = [[30,105,165,230] for _ in range(len(mapped))]
        if decisions is not None:
            decision_lookup = decisions.set_index('School ID')['Decision']
            mapped['marker_color'] = mapped['School ID'].map(lambda sid: [35,145,85,230] if decision_lookup.loc[sid] == 'Recommend' else [150,150,150,150])
        if spokes:
            lines = pd.DataFrame([{'source':[hub_lon,hub_lat], 'target':[r['Longitude'],r['Latitude']]} for _,r in mapped.iterrows()])
            layers.append(pdk.Layer('LineLayer', lines, id='share-connections', get_source_position='source', get_target_position='target', get_color=[70,125,180,100], get_width=1))
        if not close.empty:
            close['tip'] = close['School A'] + ' ↔ ' + close['School B']
            layers.append(pdk.Layer('LineLayer', close, id='close-school-pairs', get_source_position='source', get_target_position='target', get_color=[235,135,30,210], get_width=4, pickable=True))
        layers.append(pdk.Layer('ScatterplotLayer', mapped, id='top25-schools', get_position='[Longitude, Latitude]', get_radius=150, radius_min_pixels=10, get_fill_color='marker_color', pickable=True, auto_highlight=True))
        layers.append(pdk.Layer('TextLayer', mapped, id='school-labels', get_position='[Longitude, Latitude]', get_text='name_label' if names else 'number', get_size=12, get_pixel_offset=[0,-20], get_color=[225,238,250] if style == 'Dark' else [25,75,125]))
        view_points += mapped[['Longitude','Latitude']].values.tolist()
    view = pdk.data_utils.compute_view(view_points, view_proportion=0.8) if len(view_points)>1 else pdk.ViewState(latitude=hub_lat, longitude=hub_lon, zoom=12)
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view, map_provider='carto', map_style={'Street':'road','Light':'light','Dark':'dark'}[style or 'Street'], tooltip={'text':'{tip}', 'style':{'backgroundColor':'#17334d','color':'white'}}), use_container_width=True)
    marker_legend = 'Green = spacing recommendation · Gray = left out' if decisions is not None else 'Blue = selected schools'
    st.caption(f'Red = Share approximate location · {marker_legend} · Orange lines = close pairs. The Served Schools filter applies before selecting the top 25; blank includes both groups. Scenario ranks and order retain their citywide values. Connections are not roads or service boundaries.')
    st.subheader('Selected schools and distance from Share')
    table = schools[['Order','Scenario rank','School','Type','Level','School ID','School address','Scenario score','Service status']].merge(mapped[['School ID','Miles from Share (approx.)']], on='School ID', how='left')
    sort = st.selectbox('Sort school list', ['Scenario order', 'Nearest Share', 'Farthest Share'], index=None, key='staff_sort')
    table = table.sort_values('Order' if sort in (None, 'Scenario order') else 'Miles from Share (approx.)', ascending=sort!='Farthest Share', na_position='last')
    st.dataframe(table, hide_index=True, use_container_width=True, column_config={'Miles from Share (approx.)':st.column_config.NumberColumn(format='%.2f')})
    export = table.assign(**{'Share address':address,'Share latitude':hub_lat,'Share longitude':hub_lon,'Distance method':'Straight-line Haversine; approximate Share pin'})
    st.download_button('Download selected schools and distances', export.to_csv(index=False).encode('utf-8'), 'top25_staff_distances.csv', 'text/csv')
    st.subheader('Schools near one another')
    pair_table = close[['School A','School B','Miles apart']]
    if pair_table.empty:
        st.info('No selected school pairs fall below this distance threshold.')
    st.dataframe(pair_table, hide_index=True, use_container_width=True, column_config={'Miles apart':st.column_config.NumberColumn(format='%.2f')})
    st.download_button('Download all pairwise school distances', pairs[['School A','School B','School ID A','School ID B','Miles apart']].to_csv(index=False).encode('utf-8'), 'school_pair_distances.csv', 'text/csv')
    if len(mapped)>1:
        st.subheader('Compare any two selected schools')
        ids = mapped['School ID'].tolist()
        lookup = mapped.set_index('School ID')
        a, b = st.columns(2)
        first = a.selectbox('School A', ids, index=None, format_func=lambda sid: lookup.loc[sid,'School'], key='staff_compare_a')
        second = b.selectbox('School B', ids, index=None, format_func=lambda sid: lookup.loc[sid,'School'], key='staff_compare_b')
        if first is not None and second is not None:
            x, y = lookup.loc[first], lookup.loc[second]
            st.metric('Distance between selected schools', f"{float(miles_between(x['Latitude'],x['Longitude'],y['Latitude'],y['Longitude'])):.2f} mi")
        with st.expander('Full school-to-school distance grid'):
            labels = mapped['Order'].astype(str) + ' · ' + mapped['School']
            fig = px.imshow(matrix, x=labels, y=labels, color_continuous_scale='Blues_r', labels={'color':'Miles'}, aspect='auto')
            fig.update_traces(hovertemplate='%{y}<br>%{x}<br>%{z:.2f} mi<extra></extra>')
            st.plotly_chart(fig, use_container_width=True)

    if decisions is not None:
        st.caption('Spacing colors: green = recommended; gray = left out. Hover labels remain school names only.')
        render_spacing_results(decisions, pairs, minimum_spacing, weights)
