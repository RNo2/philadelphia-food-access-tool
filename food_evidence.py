"""Workbook food-site evidence; distances are recomputed for each school."""
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def load_food_sites():
    return pd.read_csv(Path(__file__).resolve().parent / 'data/food_sites.csv', dtype={'Site ID': str})


def nearby_food_sites(sites, latitude, longitude):
    columns = ['Miles', 'Site name', 'Address', 'Type', 'Status', 'ZIP restrictions', 'Website', 'Retrieved', 'Source URL']
    if pd.isna(latitude) or pd.isna(longitude) or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return pd.DataFrame(columns=columns)
    active = sites[(sites['Candidate'].eq('Yes')) & sites['Status'].eq('Active') & ~sites['Temporary closure'].fillna('').astype(str).str.lower().eq('yes') & ~sites['Seasonal closure'].fillna('').astype(str).str.lower().eq('yes')].copy()
    lat = pd.to_numeric(active['Latitude'], errors='coerce')
    lon = pd.to_numeric(active['Longitude'], errors='coerce')
    active = active[lat.between(-90, 90) & lon.between(-180, 180)].copy()
    lat = np.radians(pd.to_numeric(active['Latitude']))
    lon = np.radians(pd.to_numeric(active['Longitude']))
    school_lat, school_lon = np.radians([float(latitude), float(longitude)])
    hav = np.sin((lat-school_lat)/2)**2 + np.cos(lat)*np.cos(school_lat)*np.sin((lon-school_lon)/2)**2
    active['Miles'] = 3958.7613 * 2 * np.arcsin(np.sqrt(hav.clip(0, 1)))
    return active[active['Miles'] <= 1].sort_values(['Miles', 'Site name'])[columns].reset_index(drop=True)


def render_food_sites(row, key):
    st.subheader('Nearby listed food sites')
    st.caption('From SBD_Expansion_Model_10.20.2026.xlsx; source retrieved October 9, 2026. Active City Food Site candidates within one straight-line mile, excluding recorded closures. Listed websites are provider references, not confirmation of current hours or eligibility. Multiple listings can share an address; the model resource count uses distinct addresses.')
    if pd.isna(row['Latitude']) or pd.isna(row['Longitude']):
        st.info('School coordinates are missing; nearby sites cannot be calculated.')
        return
    nearby = nearby_food_sites(load_food_sites(), row['Latitude'], row['Longitude'])
    if nearby.empty:
        st.info('No active candidate food sites within one mile in this snapshot. This does not establish that no food assistance is available.')
    else:
        st.dataframe(nearby.rename(columns={'Site name': 'Food site'}), hide_index=True, use_container_width=True, column_config={
            'Miles': st.column_config.NumberColumn(format='%.2f'),
            'Website': st.column_config.LinkColumn('Website reference'),
            'Source URL': st.column_config.LinkColumn('City source dataset'),
        })
        st.download_button('Download nearby food sites', nearby.to_csv(index=False).encode('utf-8'), 'nearby_food_sites.csv', 'text/csv', key=key)
