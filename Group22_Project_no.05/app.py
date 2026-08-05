import streamlit as st
import pandas as pd
import folium
import networkx as nx
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="CDR Intelligence Dashboard", layout="wide")

st.title("📡 CDR, IPDR & Tower Dump Intelligence Dashboard")
st.caption("Cyber Shakti Internship 2.0 | Group 22: Jasdeep Kaur, Paras Khare, Aditya Sangwan, Prasanna Pavan Ghom")
st.divider()

# --- MOCK DATASETS ---
# 1. Call Detail Records (CDR)
cdr_data = {
    'Caller': ['Suspect_A', 'Suspect_A', 'Suspect_B', 'Suspect_C', 'Suspect_A', 'Suspect_B', 'Suspect_C'],
    'Receiver': ['Suspect_B', 'Suspect_C', 'Suspect_C', 'Suspect_A', 'Suspect_B', 'Suspect_A', 'Suspect_B'],
    'Timestamp': ['2026-08-01 22:15', '2026-08-01 22:30', '2026-08-01 23:05', '2026-08-02 01:10', '2026-08-02 02:00', '2026-08-02 02:15', '2026-08-02 03:00'],
    'Duration_Sec': [120, 45, 300, 15, 180, 200, 90],
    'Tower_ID': ['T101', 'T101', 'T102', 'T103', 'T102', 'T101', 'T103']
}

# 2. Cell Tower Dump Data
tower_data = {
    'Tower_ID': ['T101', 'T102', 'T103'],
    'Location': ['Downtown Central', 'North Highway', 'West Station'],
    'Latitude': [18.5204, 18.5314, 18.5100],
    'Longitude': [73.8567, 73.8446, 73.8200]
}

# 3. Internet Protocol Detail Records (IPDR)
ipdr_data = {
    'Suspect': ['Suspect_A', 'Suspect_B', 'Suspect_A', 'Suspect_C'],
    'Timestamp': ['2026-08-01 22:45', '2026-08-01 23:15', '2026-08-02 01:30', '2026-08-02 02:45'],
    'Service_App': ['WhatsApp VoIP', 'Telegram', 'ProtonMail', 'Signal'],
    'Data_Usage_MB': [15.2, 5.5, 2.1, 8.4],
    'Source_IP': ['192.168.1.15', '10.0.0.45', '192.168.1.15', '172.16.0.12']
}

df_cdr = pd.DataFrame(cdr_data)
df_towers = pd.DataFrame(tower_data)
df_ipdr = pd.DataFrame(ipdr_data)

# --- SIDEBAR INTERACTIVE FILTERS ---
st.sidebar.header("🔍 Intelligence Filters")

all_suspects = sorted(list(set(df_cdr['Caller'].unique()).union(set(df_cdr['Receiver'].unique()))))
selected_suspect = st.sidebar.selectbox("Filter Person of Interest (POI):", ["All Suspects"] + all_suspects)

late_night_only = st.sidebar.checkbox("Flag Late-Night Calls Only (11 PM - 4 AM)")

# --- FILTERING LOGIC ---
filtered_cdr = df_cdr.copy()
filtered_ipdr = df_ipdr.copy()

if selected_suspect != "All Suspects":
    filtered_cdr = filtered_cdr[(filtered_cdr['Caller'] == selected_suspect) | (filtered_cdr['Receiver'] == selected_suspect)]
    filtered_ipdr = filtered_ipdr[filtered_ipdr['Suspect'] == selected_suspect]

if late_night_only:
    filtered_cdr = filtered_cdr[filtered_cdr['Timestamp'].str.contains('23:|01:|02:|03:')]
    filtered_ipdr = filtered_ipdr[filtered_ipdr['Timestamp'].str.contains('23:|01:|02:|03:')]

# --- LIVE METRICS DASHBOARD ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total CDR Records", len(filtered_cdr))
active_persons = set(filtered_cdr['Caller']).union(set(filtered_cdr['Receiver'])) if not filtered_cdr.empty else []
m2.metric("Active Suspects Identified", len(active_persons))
m3.metric("Unique Towers Pinged", filtered_cdr['Tower_ID'].nunique() if not filtered_cdr.empty else 0)
anomalies = len(filtered_cdr[filtered_cdr['Timestamp'].str.contains('23:|01:|02:|03:')])
m4.metric("Suspicious Late-Night Calls", anomalies)

st.divider()

# --- TABBED VIEW FOR INTERACTIVE DASHBOARD ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Geospatial Movement Map", 
    "🕸️ Link Analysis Network", 
    "📋 Filtered CDR Log", 
    "🌐 IPDR Data Logs"
])

# TAB 1: INTERACTIVE MAP
with tab1:
    st.subheader("Suspect Movement Map")
    merged_data = pd.merge(filtered_cdr, df_towers, on='Tower_ID')

    if not merged_data.empty:
        intel_map = folium.Map(location=[18.5204, 73.8567], zoom_start=12)

        for idx, row in merged_data.iterrows():
            is_late = any(t in row['Timestamp'] for t in ['23:', '01:', '02:', '03:'])
            popup_text = f"<b>Caller:</b> {row['Caller']}<br><b>Receiver:</b> {row['Receiver']}<br><b>Time:</b> {row['Timestamp']}<br><b>Tower:</b> {row['Location']}"

            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=popup_text,
                tooltip=f"{row['Caller']} @ {row['Location']}",
                icon=folium.Icon(color='red' if is_late else 'blue', icon='phone')
            ).add_to(intel_map)

        intel_map.save("map.html")
        with open("map.html", "r", encoding="utf-8") as f:
            components.html(f.read(), height=450)
        st.info("💡 **Interactive Tip:** Click on any marker to view communication timestamps and suspect locations.")
    else:
        st.warning("No records found matching the current filters.")

# TAB 2: NETWORK GRAPH
with tab2:
    st.subheader("Communication Network Link Graph")
    if not filtered_cdr.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        G = nx.from_pandas_edgelist(filtered_cdr, source='Caller', target='Receiver', create_using=nx.DiGraph())
        pos = nx.spring_layout(G, seed=42)
        
        nx.draw_networkx_nodes(G, pos, node_color='#1E88E5', node_size=2500, ax=ax)
        nx.draw_networkx_labels(G, pos, font_color='white', font_weight='bold', ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='#757575', arrowsize=20, width=2, ax=ax)
        
        ax.axis('off')
        st.pyplot(fig)
    else:
        st.warning("No records available to display communication graph.")

# TAB 3: DATA TABLE (CDR)
with tab3:
    st.subheader("Raw Filtered Telecommunication Log (CDR)")
    st.dataframe(filtered_cdr, use_container_width=True)

# TAB 4: DATA TABLE (IPDR)
with tab4:
    st.subheader("Internet Protocol Detail Records (IPDR)")
    st.caption("Tracks internet-based communications (VoIP, Messaging, Cloud Services) bypassing standard cellular networks.")
    st.dataframe(filtered_ipdr, use_container_width=True)
