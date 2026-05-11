# Re-running visualization with compatible Altair selection syntax
import pandas as pd
import numpy as np
import altair as alt

# Data setup
quarters = [f'Q{q} {y}' for y in range(2023, 2028) for q in range(1, 5)][:18]
hist_end_idx = 12
data = {
    'Quarter': quarters,
    'onsemi_P50': [1.96, 2.09, 2.18, 2.02, 1.86, 1.74, 1.76, 1.75, 1.68, 1.62, 1.58, 1.55, 1.51, 1.51, 1.50, 1.50, 1.65, 1.70],
    'TXN': [4.38, 4.53, 4.53, 4.08, 3.66, 3.82, 3.90, 3.85, 3.75, 3.65, 3.55, 3.50, 3.50, 3.60, 3.70, 3.82, 3.90, 4.00],
    'NXPI': [3.12, 3.30, 3.43, 3.42, 3.13, 3.13, 3.25, 3.30, 3.20, 3.15, 3.10, 3.10, 3.10, 3.20, 3.30, 3.38, 3.45, 3.55],
    'STM': [4.25, 4.33, 4.43, 4.28, 3.47, 3.23, 3.25, 3.35, 3.30, 3.25, 3.25, 3.30, 3.30, 3.40, 3.45, 3.55, 3.65, 3.75]
}
df = pd.DataFrame(data)
df['Period_Idx'] = range(len(df))
df['Type'] = ['Historical']*hist_end_idx + ['Forecast']*(len(df)-hist_end_idx)
df['onsemi_P10'] = list(df['onsemi_P50'][:12]) + [1.39, 1.33, 1.29, 1.26, 1.35, 1.40]
df['onsemi_P90'] = list(df['onsemi_P50'][:12]) + [1.64, 1.69, 1.73, 1.77, 1.95, 2.05]

for col in ['onsemi_P50', 'TXN', 'NXPI', 'STM']:
    df[f'{col}_QoQ'] = df[col].pct_change() * 100

risk_data = pd.DataFrame({
    'Company': ['onsemi', 'TXN', 'NXPI', 'STM'],
    'Risk Factor': ['SiC Yield Volatility', 'Inventory Overhang', 'Auto Demand Slowdown', 'Geopolitical Exposure'],
    'Impact': [4, 3, 3, 5],
    'Likelihood': [3, 4, 3, 3],
    'Market_Cap_B': [35, 150, 60, 40],
    'Audit_Logic': [
        'SiC growth targets at risk if yield < 80%.',
        'High fab utilization aging inventory risks.',
        'Tier-1 auto correlation with rates.',
        'Energy cost spikes in EU hubs.'
    ]
})
risk_data['Score'] = risk_data['Impact'] * risk_data['Likelihood']

# Interactive selection (using selection_multi/single for compatibility)
selection = alt.selection_point(fields=['Company'], bind='legend')

base = alt.Chart(df).encode(x=alt.X('Quarter:N', sort=alt.SortField('Period_Idx')))
line_onsemi = base.mark_line(point=True).encode(
    y=alt.Y('onsemi_P50:Q', title='Revenue ($B)'),
    color=alt.value('#1f77b4'),
    strokeDash=alt.condition(alt.datum.Type == 'Forecast', alt.value([5, 5]), alt.value([0, 0]))
)
band = alt.Chart(df[df['Type'] == 'Forecast']).mark_area(opacity=0.2).encode(
    x=alt.X('Quarter:N', sort=alt.SortField('Period_Idx')),
    y='onsemi_P10:Q', y2='onsemi_P90:Q', color=alt.value('#1f77b4')
)
peer_melt = df.melt(id_vars=['Quarter', 'Type', 'Period_Idx'], value_vars=['TXN', 'NXPI', 'STM'], var_name='Company', value_name='Revenue')
peer_lines = alt.Chart(peer_melt).mark_line(point=True).encode(
    x=alt.X('Quarter:N', sort=alt.SortField('Period_Idx')),
    y='Revenue:Q',
    color='Company:N',
    strokeDash=alt.condition(alt.datum.Type == 'Forecast', alt.value([5, 5]), alt.value([0, 0])),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
).add_params(selection)

pane1 = (band + line_onsemi + peer_lines).properties(width=350, height=250, title="Revenue Forecast ($B)")

qoq_melt = df[1:].melt(id_vars=['Quarter', 'Type', 'Period_Idx'], value_vars=['onsemi_P50_QoQ', 'TXN_QoQ', 'NXPI_QoQ', 'STM_QoQ'], var_name='Company', value_name='QoQ')
qoq_melt['Company'] = qoq_melt['Company'].str.replace('_P50_QoQ', '')
pane2 = alt.Chart(qoq_melt).mark_line(point=True).encode(
    x=alt.X('Quarter:N', sort=alt.SortField('Period_Idx')),
    y=alt.Y('QoQ:Q', title='QoQ % Change'),
    color='Company:N',
    strokeDash=alt.condition(alt.datum.Type == 'Forecast', alt.value([5, 5]), alt.value([0, 0])),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
).properties(width=350, height=250, title="QoQ Momentum (%)")

pane3 = alt.Chart(risk_data).mark_circle().encode(
    x='Likelihood:Q', y='Impact:Q', size='Market_Cap_B:Q',
    color=alt.Color('Score:Q', scale=alt.Scale(scheme='redyellowgreen', reverse=True)),
    tooltip=['Company', 'Risk Factor', 'Score', 'Audit_Logic']
).properties(width=750, height=300, title="Strategic Risk Matrix")

dashboard = (pane1 | pane2) & pane3
dashboard.save('senior_analyst_dashboard.json')
print("Dashboard and audit files generated.")