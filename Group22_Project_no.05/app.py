import streamlit as st
import pandas as pd
import folium
import networkx as nx
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Cyber Intelligence Tool", layout="wide")

st.title("📡 Telecom Correlation & Timeline Reconstruction Engine")
st.markdown("**Objective:** Correlate telecom records to reconstruct communication timelines and visualize investigative leads.")
st.caption("Developed by Group 22: Jasdeep Kaur, Paras Khare, Aditya Sangwan, Prasanna Pavan Ghom")
st.divider()

# --- SAMPLE DATA GENERATOR (For Fallback) ---
def load_sample_data():
    cdr = pd.DataFrame({
        'Caller': ['Suspect_A', 'Suspect_A', 'Suspect_B', 'Suspect_C'],
        'Receiver': ['Suspect_B', 'Suspect_C', 'Suspect_C', 'Suspect_A'],
        'Timestamp': ['2026-08-01 22:15:00', '2026-08-01 22:30:00', '2026-08-01 23:05:00', '2026-08-02 01:10:00'],
        'Tower_ID': ['T101', 'T101', 'T102', 'T103']
    })
    ipdr = pd.DataFrame({
        'Suspect': ['Suspect_A', 'Suspect_B'],
        'Service': ['WhatsApp VoIP', 'Telegram'],
        'Timestamp': ['2026-08-01 22:45:00', '2026-08-02 01:30:00'],
        'Tower_ID': ['T101', 'T102']
    })
    towers = pd.DataFrame({
        'Tower_ID': ['T101', 'T102', 'T103'],
        'Location': ['Downtown Central', 'North Highway', 'West Station'],
        'Latitude': [18.5204, 18.5314, 18.5100],
        'Longitude': [73.8567, 73.8446, 73.8200]
    })
    return cdr, ipdr, towers

# --- SIDEBAR: DATA UPLOAD OR DEMO MODE ---
st.sidebar.header("📂 1. Data Ingestion")
st.sidebar.markdown("Upload raw files to reconstruct timelines.")

upload_cdr = st.sidebar.file_uploader("Upload CDR (CSV)", type="csv")
upload_ipdr = st.sidebar.file_uploader("Upload IPDR (CSV)", type="csv")
upload_towers = st.sidebar.file_uploader("Upload Tower Dump (CSV)", type="csv")

use_demo = st.sidebar.button("Run Demo / Sample Data")

# --- DATA PROCESSING LOGIC ---
df_cdr, df_ipdr, df_towers = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

if use_demo:
    df_cdr, df_ipdr, df_towers = load_sample_data()
    st.success("Loaded Sample Data successfully. Tool is in Demo Mode.")
elif upload_cdr and upload_ipdr and upload_towers:
    df_cdr = pd.read_csv(upload_cdr)
    df_ipdr = pd.read_csv(upload_ipdr)
    df_towers = pd.read_csv(upload_towers)
    st.success("Raw files ingested successfully. Engine ready.")
else:
    st.info("👈 Please upload your CDR, IPDR, and Tower Dump CSV files in the sidebar, or click 'Run Demo' to test the tool.")
    st.stop() # Stops execution until data is provided (makes it act like a real app)

# --- ENGINE: TIMELINE RECONSTRUCTION ---
# Standardizing and merging CDR and IPDR into a single timeline
cdr_timeline = df_cdr[['Timestamp', 'Caller', 'Receiver', 'Tower_ID']].copy()
cdr_timeline['Event_Type'] = 'Cellular Call'
cdr_timeline.rename(columns={'Caller': 'Primary_Entity', 'Receiver': 'Secondary_Entity'}, inplace=True)

ipdr_timeline = df_ipdr[['Timestamp', 'Suspect', 'Service', 'Tower_ID']].copy()
ipdr_timeline['Event_Type'] = 'Internet/Data'
ipdr_timeline.rename(columns={'Suspect': 'Primary_Entity', 'Service': 'Secondary_Entity'}, inplace=True)

# Correlate and sort chronologically
master_timeline = pd.concat([cdr_timeline, ipdr_timeline])
master_timeline['Timestamp'] = pd.to_datetime(master_timeline['Timestamp'])
master_timeline = master_timeline.sort_values(by='Timestamp').reset_index(drop=True)

# Merge with Tower Data for geospatial coordinates
correlated_data = pd.merge(master_timeline, df_towers, on='Tower_ID', how='left')

# --- UI TABS: VISUALIZING LEADS ---
st.header("2. Investigative Leads & Correlation")
tab1, tab2, tab3 = st.tabs(["⏱️ Chronological Timeline", "🗺️ Geospatial Movement", "🕸️ Link Analysis"])

with tab1:
    st.subheader("Reconstructed Master Timeline")
    st.caption("Integrated view of all cellular and data events sorted by exact timestamp.")
    st.dataframe(correlated_data, use_container_width=True)

with tab2:
    st.subheader("Geospatial Tower Correlation")
    if not correlated_data.empty:
        # Center map on the first tower hit
        start_lat = correlated_data['Latitude'].iloc[0]
        start_lon = correlated_data['Longitude'].iloc[0]
        intel_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)

        # Map iterations based on the chronological timeline
        for idx, row in correlated_data.iterrows():
            popup_html = f"<b>Entity:</b> {row['Primary_Entity']}<br><b>Event:</b> {row['Event_Type']}<br><b>Time:</b> {row['Timestamp']}<br><b>Location:</b> {row['Location']}"
            
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=popup_html,
                tooltip=f"Timeline Event #{idx + 1}",
                icon=folium.Icon(color='red' if row['Event_Type'] == 'Internet/Data' else 'blue')
            ).add_to(intel_map)

        intel_map.save("timeline_map.html")
        with open("timeline_map.html", "r", encoding="utf-8") as f:
            components.html(f.read(), height=500)
        st.caption("📍 Blue = Cellular Calls | 🔴 Red = Internet/App Usage (IPDR)")

with tab3:
    st.subheader("Network Link Graph")
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Extract only cellular calls for the network graph
    G = nx.from_pandas_edgelist(df_cdr, source='Caller', target='Receiver', create_using=nx.DiGraph())
    pos = nx.spring_layout(G, seed=42)
    
    nx.draw_networkx_nodes(G, pos, node_color='#4CAF50', node_size=2000, ax=ax)
    nx.draw_networkx_labels(G, pos, font_color='white', font_weight='bold', ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='#BDBDBD', arrowsize=20, width=2, ax=ax)
    
    ax.axis('off')
    st.pyplot(fig)
