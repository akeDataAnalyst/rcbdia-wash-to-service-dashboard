#!/usr/bin/env python
# coding: utf-8

# In[4]:


# app.py  ← Donor-Ready Version (World Bank / UNICEF / USAID standard)
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="RCBDIA WASH-to-Service Dashboard", layout="wide")

# === DATA & SCORING (unchanged – 100% working) ===
@st.cache_data
def load_data():
    woreda = pd.read_csv("data/dim_woreda.csv")
    kebele = pd.read_csv("data/dim_kebele.csv")
    wuaf = pd.read_csv("data/dim_wuaf.csv")
    wp = pd.read_csv("data/dim_water_point.csv")
    kpi = pd.read_csv("data/fact_wuaf_kpi.csv")

    df = (kpi
          .merge(wuaf, on='wuaf_id', how='left')
          .merge(kebele, on='kebele_id', how='left')
          .merge(woreda, on='woreda_id', how='left')
          )

    def calc_score(r):
        s = (r['functionality_rate'] * 4 +
             r['tariff_collection_rate'] * 3 +
             min(r['meetings_held'], 2) * 0.5 +
             r['maintenance_done'] +
             (5 - min(r['user_complaints'], 5)) * 0.2 +
             r['water_quality_test'] +
             r['financial_audit'] +
             min(r['training_attended'], 3)/3 +
             r['wa_salary_paid'] +
             r['spare_parts_stock'] +
             min(r['emergency_fund']/2000, 1) +
             r['user_satisfaction_score'] * 0.2 +
             (r['wp_functional']/r['total_wp']) +
             (0.5 if r['has_business_plan'] else 0) +
             (0.5 if r['has_tariff'] else 0))
        return round(min(s, 15.0), 2)

    df['total_score'] = df.apply(calc_score, axis=1)
    df['performance_band'] = pd.cut(df['total_score'],
                                   bins=[0, 8.5, 11, 13.5, 15],
                                   labels=['Needs Support', 'Fair', 'Good', 'Excellent'],
                                   include_lowest=True)
    return df

df = load_data()

# === FILTER ===
st.sidebar.header("Filters")
selected_woreda = st.sidebar.selectbox("Woreda", ['All'] + sorted(df['woreda_name'].dropna().unique()))
if selected_woreda != 'All':
    df = df[df['woreda_name'] == selected_woreda]

# === HEADER ===
st.title("RCBDIA WASH-to-Service Dashboard")
st.markdown("**Wolaita Zone | 74 WUAFs | 148 Water Points | 179,280 beneficiaries**")

# === GLOSSARY & STANDARDS (Donor version – short & sharp) ===
with st.expander("Acronyms & Performance Standards", expanded=False):
    st.markdown("""
    **Acronyms**  
    • WASH – Water, Sanitation and Hygiene  
    • WUAF – Water Users Association Federation  
    • WP – Water Point  

    **RCBDIA & National Targets**  
    | Indicator                | Target      | Source                          |
    |--------------------------|-------------|---------------------------------|
    | Functionality Rate       | ≥ 95%       | OWNP-II / SDG 6                 |
    | Tariff Collection Rate   | ≥ 80%       | National Utility Guideline      |
    | User Satisfaction        | ≥ 4.2/5     | RCBDIA Community Scorecard      |
    | Emergency Fund           | ≥ 2,000 ETB | RCBDIA Sustainability Framework|
    | 15-Point Score           | ≥ 13.5      | Excellent = Utility-Ready       |
    """)

# === KPI CARDS ===
c1, c2, c3, c4 = st.columns(4)
c1.metric("Functionality Rate", f"{df['functionality_rate'].mean():.1%}", "Target ≥95%")
c2.metric("Tariff Collection", f"{df['tariff_collection_rate'].mean():.1%}", "Target ≥80%")
c3.metric("User Satisfaction", f"{df['user_satisfaction_score'].mean():.2f}/5", "Target ≥4.2")
c4.metric("15-Point Score", f"{df['total_score'].mean():.2f}/15", "Excellent ≥13.5")

# === SCORECARD ===
st.subheader("WUAF 15-Point Scorecard")
fig = px.scatter(df,
                 x='month', y='kebele_name',
                 size='total_score', color='performance_band',
                 hover_data=['wuaf_id', 'woreda_name', 'total_score'],
                 color_discrete_map={'Excellent':'#006400', 'Good':'#238823',
                                    'Fair':'#FFD700', 'Needs Support':'#DC143C'})
st.plotly_chart(fig, use_container_width=True)

# === RED FLAGS ===
st.subheader("Red Flags – Immediate Support Required")
alerts = df[(df['functionality_rate'] < 0.90) |
            (df['tariff_collection_rate'] < 0.70) |
            (df['emergency_fund'] < 1500)]

if not alerts.empty:
    st.error(f"{len(alerts)} WUAF(s) below critical threshold")
    st.dataframe(alerts[['wuaf_id','kebele_name','woreda_name','month',
                         'functionality_rate','tariff_collection_rate','emergency_fund']],
                 use_container_width=True)
else:
    st.success("All WUAFs performing above critical thresholds")

# === FOOTER ===
st.markdown("---")
st.caption("Developed by Aklilu Abera Dana | RCBDIA WASH Analytics | Wolaita Zone 2025")


# In[ ]:




