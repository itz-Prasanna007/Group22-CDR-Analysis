import streamlit as st
import pandas as pd
import folium
import networkx as nx
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# --- PAGE SETUP ---
st.set_page_config(page_title="CDR Analysis PoC", layout="wide")
st.title("📡 Cyber Shakti: CDR & Tower Dump Intelligence Analysis")
st.markdown("**Group 22:** Jasdeep Kaur, Paras Khare, Aditya Sangwan, Prasanna Pavan Ghom")
st.divider()

# --- 1. MOCK DATASETS ---
cdr_data = {
    'Caller': ['Suspect_A', 'Suspect_A', 'Suspect_B', 'Suspect_C', 'Suspect_A', 'Suspect_B'],
    'Receiver': ['Suspect_B', 'Suspect_C', 'Suspect_C', 'Suspect_A', 'Suspect_B', 'Suspect_A'],
    'Timestamp': ['2026-08-01 22:15', '2026-08-01 22:30', '2026-08-01 23:05', '2026-08-02 01:10', '2026-08-02 02:00', '2026-08-02 02:15'],
    'Duration_Sec': [120, 45, 300, 15, 180, 200],
    'Tower_ID': ['T101', 'T101', 'T102', 'T103', 'T102', 'T101']
}
tower_data = {
    'Tower_ID': ['T101', 'T102', 'T103'],
    'Location': ['Downtown Central', 'North Highway', 'West Station'],
    'Latitude': [18.5204, 18.5314, 18.5100],
    'Longitude': [73.8567, 73.8446, 73.8200]
}
df_cdr = pd.DataFrame(cdr_data)
df_towers = pd.DataFrame(tower_data)

# --- UI: SHOW RAW DATA ---
st.header("1. Data Ingestion")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Raw CDR Data")
    st.dataframe(df_cdr, use_container_width=True)
with col2:
    st.subheader("Cell Tower Locations")
    st.dataframe(df_towers, use_container_width=True)

# --- UI: INTEL ANALYSIS ---
st.header("2. Communication Frequency")
frequent_calls = df_cdr.groupby(['Caller', 'Receiver']).size().reset_index(name='Call_Count')
st.dataframe(frequent_calls, use_container_width=True)

# --- UI: GEOSPATIAL MAP ---
st.header("3. Suspect Geospatial Movement Map")
merged_data = pd.merge(df_cdr, df_towers, on='Tower_ID')
intel_map = folium.Map(location=[18.5204, 73.8567], zoom_start=13)

for idx, row in merged_data.iterrows():
    popup_text = f"Caller: {row['Caller']}<br>Receiver: {row['Receiver']}<br>Time: {row['Timestamp']}<br>Tower: {row['Location']}"
    is_late_night = '23:' in row['Timestamp'] or '01:' in row['Timestamp'] or '02:' in row['Timestamp']
    
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=popup_text,
        tooltip=f"Activity at {row['Tower_ID']}",
        icon=folium.Icon(color='red' if is_late_night else 'blue', icon='info-sign')
    ).add_to(intel_map)

# Save map and render in Streamlit
intel_map.save("map.html")
with open("map.html", "r", encoding="utf-8") as f:
    html_map = f.read()
components.html(html_map, height=450)
st.caption("🔴 Red markers indicate late-night suspicious activity.")

# --- UI: NETWORK GRAPH ---
st.header("4. Link Analysis Network")
fig, ax = plt.subplots(figsize=(8, 4))
G = nx.from_pandas_edgelist(df_cdr, source='Caller', target='Receiver', create_using=nx.DiGraph())
nx.draw_networkx(G, with_labels=True, node_color='#4CAF50', node_size=2500, font_weight='bold', font_color='white', arrowsize=20, ax=ax)
st.pyplot(fig)
