"""Decorative Overview artwork, kept separate from data and controls."""
import base64
from pathlib import Path
import streamlit as st


@st.cache_data
def overview_artwork():
    return base64.b64encode((Path(__file__).resolve().parent / 'assets/overview-school-produce.png').read_bytes()).decode('ascii')


def render_overview_header():
    st.markdown('''
<style>
.overview-banner{position:relative;isolation:isolate;overflow:hidden;border:1px solid #e2e6db;border-radius:20px;background:#faf8f2;margin:0 0 24px;box-shadow:0 8px 28px rgba(40,66,47,.045)}
.overview-banner .overview-copy{position:relative;z-index:2;width:57%;box-sizing:border-box;padding:32px;background:#faf8f2}
.overview-banner .overview-kicker{font-size:.72rem;letter-spacing:.11em;text-transform:uppercase;color:#2d6047;font-weight:650;line-height:1.6;margin:0 0 12px}
.overview-banner h1{color:#183d2d;font-size:clamp(1.8rem,2.7vw,2.65rem);line-height:1.12;letter-spacing:-.035em;margin:0 0 16px;padding:0;font-weight:700}
.overview-banner p{color:#41564a;font-size:1rem;line-height:1.65;margin:0;max-width:600px}
.overview-banner .overview-art{position:absolute;z-index:1;right:0;top:0;width:49%;height:100%;object-fit:cover;object-position:70% 65%;mask-image:linear-gradient(to right,transparent,black 20%);-webkit-mask-image:linear-gradient(to right,transparent,black 20%);pointer-events:none;user-select:none}
@media(max-width:760px){.overview-banner .overview-copy{width:100%;padding:24px}.overview-banner h1{font-size:1.85rem}.overview-banner .overview-art{position:relative;display:block;width:100%;height:180px;object-position:75% 62%;mask-image:none;-webkit-mask-image:none}.overview-banner{border-radius:16px}.overview-banner .overview-kicker{font-size:.66rem}}
</style>
''', unsafe_allow_html=True)
    st.markdown(
        '<section class="overview-banner" aria-label="Philadelphia school food access overview">'
        '<div class="overview-copy">'
        '<div class="overview-kicker">Applied Economics · Food Access · Resource Allocation</div>'
        '<h1>Philadelphia School Food Access Priority Tool</h1>'
        '<p>A transparent decision-support model for identifying schools where fresh-food outreach may have the greatest need. The tool combines economic disadvantage, geographic fresh-food access, nearby food resources, and potential student reach.</p>'
        '</div>'
        f'<img class="overview-art" src="data:image/png;base64,{overview_artwork()}" alt="" aria-hidden="true" decoding="async">'
        '</section>', unsafe_allow_html=True,
    )
