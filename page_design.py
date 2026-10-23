"""Page-specific decorative backgrounds with native scroll motion."""
import streamlit as st

PAGE_ART = {
    'Overview': 'overview',
    'All Rankable Schools': 'school-directory',
    'Served Schools': 'served-schools',
    'Food Resources': 'food-resources',
    'Priority Map': 'priority-map',
    'Distance review': 'distance-review',
    'Budget & Allocation Lab': 'budget-allocation',
    'Scenario Lab': 'scenario-lab',
    'School Explorer': 'school-explorer',
    'Methodology & Sources': 'methodology',
    'Analytical Framework': 'analytical-framework',
}


def artwork_url(name):
    return f"app/static/page-{name}.png"


def render_page_background(page):
    name = PAGE_ART[page]
    selector = f'[data-testid="stAppViewContainer"]:has(.page-art-{name})'
    st.markdown(
        f'<span class="page-art-{name}" aria-hidden="true" style="display:none"></span>'
        '<style>'
        f'{selector} [data-testid="stMain"]' + '{'
        'background-color:#fff;'
        f'background-image:linear-gradient(rgba(255,255,255,.80),rgba(255,255,255,.80)),url("{artwork_url(name)}");'
        'background-size:100% auto;background-position:center top;background-attachment:local;background-repeat:repeat-y;'
        '}'
        f'{selector} [data-testid="stMain"] [data-testid="stDataFrame"],{selector} [data-testid="stMain"] [data-testid="stPlotlyChart"],'
        f'{selector} [data-testid="stMain"] [data-testid="stDeckGlJsonChart"],{selector} [data-testid="stMain"] [data-testid="stDataEditor"]'
        '{background:#fff;border-radius:8px;}'
        f'{selector} [data-testid="stMain"] [data-testid="stDataFrame"],'
        f'{selector} [data-testid="stMain"] [data-testid="stDataEditor"],'
        f'{selector} [data-testid="stMain"] [data-testid="stTable"],'
        f'{selector} [data-testid="stMain"] .food-sites-wrap'
        '{background:#fff;border:1px solid #dce4df;border-radius:12px;'
        'box-shadow:0 3px 0 #e0e6e1,0 12px 26px rgba(28,53,40,.10),0 3px 7px rgba(28,53,40,.045),inset 0 1px 0 #fff;'
        'margin-bottom:16px;}'
        f'{selector} [data-testid="stMain"] [data-testid="stDataFrame"],'
        f'{selector} [data-testid="stMain"] [data-testid="stDataEditor"]'
        '{padding:2px;box-sizing:border-box;}'

        f'{selector} [data-testid="stMain"] [data-testid="stMarkdownContainer"],{selector} [data-testid="stMain"] [data-testid="stCaptionContainer"],{selector} [data-testid="stMain"] [data-testid="stWidgetLabel"]'
        '{background:rgba(255,255,255,.88);border-radius:4px;}'
        f'{selector} [data-testid="stMain"] [data-testid="stMetric"]'
        '{background:#fff;box-shadow:0 3px 14px rgba(32,63,45,.035);}'
        '@keyframes civic-background-drift{from{background-position:center 0}to{background-position:center -180px}}'
        '@supports(animation-timeline:scroll()){' + selector + ' [data-testid="stMain"]'
        '{background-attachment:fixed;animation:civic-background-drift linear both;animation-timeline:scroll(self block);}}'
        '@media(max-width:760px){' + selector + ' [data-testid="stMain"]'
        '{background-size:100% auto;background-attachment:local;animation:none;}}'
        '@media(prefers-reduced-motion:reduce){' + selector + ' [data-testid="stMain"]'
        '{background-attachment:scroll;animation:none;}}'
        '</style>', unsafe_allow_html=True,
    )
