"""Overview introduction; page artwork is managed by page_design."""
import streamlit as st


def render_overview_header():
    st.markdown(
        '<div class="hero">'
        '<div class="kicker">Applied Economics · Food Access · Resource Allocation</div>'
        '<h1>Philadelphia School Food Access Priority Tool</h1>'
        '<p>A transparent decision-support model for identifying schools where fresh-food outreach may have the greatest need. The tool combines economic disadvantage, geographic fresh-food access, nearby food resources, and potential student reach.</p>'
        '</div>', unsafe_allow_html=True,
    )
