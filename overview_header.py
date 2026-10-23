"""Faint full-page Overview background with readable foreground content."""
import base64
from pathlib import Path
import streamlit as st


@st.cache_data
def overview_artwork():
    return base64.b64encode((Path(__file__).resolve().parent / 'assets/overview-page-background.png').read_bytes()).decode('ascii')


def render_overview_header():
    selector = '[data-testid="stAppViewContainer"]:has(.overview-page-marker)'
    st.markdown(
        '<style>'
        f'{selector} [data-testid="stMain"]' + '{'
        'background-color:#fff;'
        f'background-image:linear-gradient(rgba(255,255,255,.60),rgba(255,255,255,.60)),url("data:image/png;base64,{overview_artwork()}");'
        'background-size:100% 100vh;background-position:center top;background-attachment:fixed;background-repeat:no-repeat;'
        '}'
        f'{selector} [data-testid="stDataFrame"],{selector} [data-testid="stPlotlyChart"]' + '{background:#fff;border-radius:8px;}'
        f'{selector} .overview-page-marker' + '{padding:8px 0 14px;background:rgba(255,255,255,.88);}'
        '@media(max-width:760px){'
        f'{selector} [data-testid="stMain"]' + '{background-attachment:scroll;background-size:100% 100vh;}'
        '}'
        '</style>', unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero overview-page-marker">'
        '<div class="kicker">Applied Economics · Food Access · Resource Allocation</div>'
        '<h1>Philadelphia School Food Access Priority Tool</h1>'
        '<p>A transparent decision-support model for identifying schools where fresh-food outreach may have the greatest need. The tool combines economic disadvantage, geographic fresh-food access, nearby food resources, and potential student reach.</p>'
        '</div>', unsafe_allow_html=True,
    )
