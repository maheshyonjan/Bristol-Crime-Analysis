import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import json
import branca.colormap as cm

# --- CSS STYLING (UI ENHANCEMENTS) ---
def add_custom_css():
    st.markdown("""
        <style>
        /* Modern, semi-transparent tooltips (Hover) - Opacity 0.7 */
        .leaflet-tooltip {
            background-color: rgba(255, 255, 255, 0.7) !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #333;
            border-radius: 8px;
            font-family: 'Helvetica', sans-serif;
            font-size: 13px;
            font-weight: 500;
        }
        /* Remove default tooltip arrow for clean floating look */
        .leaflet-tooltip-left:before, .leaflet-tooltip-right:before {
            border: none !important;
        }
        
        /* Modern, semi-transparent Popups (Click) - Opacity 0.6 (UPDATED) */
        .leaflet-popup-content-wrapper {
            background-color: rgba(255, 255, 255, 0.6) !important;
            backdrop-filter: blur(5px); /* Adds a nice blur effect behind */
        }
        .leaflet-popup-tip {
            border-top-color: rgba(255, 255, 255, 0.6) !important;
        }
        </style>
        """, unsafe_allow_html=True)

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Bristol Crime Analysis", layout="wide")
add_custom_css()

# --- 1. DATA LOADER ---
@st.cache_data
def load_data():
    # Load processed datasets (Incidents, Socioeconomic, and Venues)
    try:
        incidents = pd.read_csv('app_data_incidents.csv')
        master = pd.read_csv('app_data_master.csv')
        pubs = pd.read_csv('bristol_pubs_restaurants.csv') # Night-Time Economy Data
        
        # Restore datetime objects
        incidents['Month'] = pd.to_datetime(incidents['Month'])
        return incidents, master, pubs
    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
        st.stop()

def load_geojson():
    try:
        with open('raw_data/Lower_Layer_Super_Output_Areas_2021_(Precise).geojson') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("GeoJSON file not found. Check the 'data' folder.")
        st.stop()

# Initialize
incidents_df, master_df, pubs_df = load_data()
geojson_data = load_geojson()

# --- 2. SIDEBAR FILTERS ---
st.sidebar.header("Filters")
st.sidebar.info("Configure filters to update the dashboard.")

# --- FILTER 1: TIME PERIOD ---
st.sidebar.subheader("Time Period")

min_date = incidents_df['Month'].min().date()
max_date = incidents_df['Month'].max().date()

start_date, end_date = st.sidebar.slider(
    "Select Date Range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="MMM YYYY"
)

time_mask = (incidents_df['Month'].dt.date >= start_date) & (incidents_df['Month'].dt.date <= end_date)
base_filtered_incidents = incidents_df.loc[time_mask]


# --- FILTER 2: CRIME TYPE ---
st.sidebar.subheader("Crime Categories")

all_crimes = base_filtered_incidents['Crime type'].unique().tolist()

# Priority crimes to show by default
target_defaults = [
    "Vehicle crime",
    "Criminal damage and arson",
    "Burglary",
    "Anti-social behaviour",
    "Other crime",
    "Violence and sexual offences"
]

# Safety Check: Ensure we only default-select crimes that actually exist in the current data
valid_defaults = [c for c in target_defaults if c in all_crimes]

selected_crimes = st.sidebar.multiselect(
    "Select Crime Types:", 
    all_crimes, 
    default=valid_defaults 
)

filtered_incidents = base_filtered_incidents[base_filtered_incidents['Crime type'].isin(selected_crimes)]

# --- FILTER 3: MAP METRIC (UPDATED) ---
st.sidebar.subheader("Map Layer")
map_metric = st.sidebar.radio(
    "Colour Map By (Socioeconomic Factor):",
    # Added 'None (Boundaries Only)' option here
    options=['Crime_Rate', 'IMDScore', 'Income', 'Employment', 'None (Boundaries Only)'],
    format_func=lambda x: "Crimes per 1,000" if x == 'Crime_Rate' 
                          else ("Boundaries Only (Transparent)" if x == 'None (Boundaries Only)' 
                          else x + " Deprivation")
)

# --- FILTER 4: EXPORT ---
st.sidebar.markdown("---")
st.sidebar.subheader("Export Data")
st.sidebar.download_button(
    label="📥 Download Filtered Dataset",
    data=filtered_incidents.to_csv(index=False).encode('utf-8'),
    file_name='bristol_crime_filtered.csv',
    mime='text/csv',
    help="Download the dataset currently displayed."
)

# --- 3. DYNAMIC DATA AGGREGATION ---
# Recalculate neighbourhood statistics based on active filters.

# 1. Aggregate Incident Counts (LSOA21CD is the key)
current_crime_counts = filtered_incidents['LSOA21CD'].value_counts().reset_index()
current_crime_counts.columns = ['LSOA21CD', 'Period_Total_Crimes']

# 2. Drop stale columns to prevent merge collisions
cols_to_drop = ['Period_Total_Crimes', 'Total_Crimes', 'Crime_Rate']
master_df = master_df.drop(columns=[c for c in cols_to_drop if c in master_df.columns])

# 3. Merge new counts
master_df = pd.merge(master_df, current_crime_counts, on='LSOA21CD', how='left')

# 4. Recalculate Rates
master_df['Period_Total_Crimes'] = master_df['Period_Total_Crimes'].fillna(0)
master_df['Total_Crimes'] = master_df['Period_Total_Crimes']
master_df['Crime_Rate'] = (master_df['Total_Crimes'] / master_df['POP2022Total']) * 1000
master_df['Crime_Rate'] = master_df['Crime_Rate'].fillna(0)


# --- 4. MAIN DASHBOARD UI ---
st.title("Spatial Analysis of Crime in Bristol")

# --- STATIC DATA OVERVIEW (GLOBAL STATS) ---
with st.expander("Dataset Overview (Global Statistics)", expanded=True):
    if not filtered_incidents.empty:
        total_records = len(incidents_df)
        unique_categories = incidents_df['Crime type'].nunique()
        date_range = f"{incidents_df['Month'].min().strftime('%b %Y')} - {incidents_df['Month'].max().strftime('%b %Y')}"
        
        top_crime = incidents_df['Crime type'].value_counts().idxmax()
        top_crime_count = incidents_df['Crime type'].value_counts().max()
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Incidents", f"{total_records:,}")
        kpi2.metric("Date Range", date_range)
        kpi3.metric("Crime Categories", unique_categories)
        kpi4.metric(f"Top Crime: {top_crime}", f"{top_crime_count:,}")
        
        st.markdown("---")
        
        st.markdown("**Top 5 Reported Crimes (All Time):**")
        top_5_df = incidents_df['Crime type'].value_counts().head(5).reset_index()
        top_5_df.columns = ['Crime Category', 'Total Count']
        st.dataframe(top_5_df, hide_index=True, use_container_width=True)
    else:
        st.warning("No data available for the current filters.")

st.markdown("### Visualisation and Statistical Exploration of Crime Patterns vs. Socioeconomic Factors")


tab1, tab2, tab3 = st.tabs(["Spatial Analysis", "Statistical Correlation", "Data Explorer"])

# --- TAB 1: GEOSPATIAL MAP (UPDATED LOGIC) ---
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Geospatial Map: {map_metric}")
        
        # 1. Inject Data into GeoJSON for Tooltips
        stats_dict = master_df.set_index('LSOA21CD').to_dict('index')
        for feature in geojson_data['features']:
            lsoa_id = feature['properties'].get('LSOA21CD')
            if lsoa_id in stats_dict:
                feature['properties'].update(stats_dict[lsoa_id])

        # 2. Initialize Map
        m = folium.Map(location=[51.4545, -2.5879], zoom_start=12, tiles=None)
        folium.TileLayer('cartodbpositron', name='Simple Background').add_to(m)
        folium.TileLayer('OpenStreetMap', name='Detailed Streets').add_to(m)

        # 3. Handle "Boundaries Only" vs "Coloured Map" Logic
        if map_metric == 'None (Boundaries Only)':
            # --- TRANSPARENT LAYER LOGIC ---
            folium.GeoJson(
                geojson_data,
                name="LSOA Boundaries",
                style_function=lambda feature: {
                    'fillColor': 'transparent', 
                    'color': 'black',           
                    'weight': 0.8,              
                    'fillOpacity': 0,
                },
                highlight_function=lambda x: {'weight': 2, 'color': 'blue', 'fillOpacity': 0.1},
                tooltip=folium.GeoJsonTooltip(
                    fields=['LSOA21LN', 'LSOA21NM'], 
                    aliases=['Local Name:', 'Code Name:'], 
                    sticky=True
                )
            ).add_to(m)
            
        else:
            # --- STANDARD CHOROPLETH LOGIC ---
            min_val = master_df[map_metric].min()
            max_val = master_df[map_metric].max()
            if min_val == max_val: max_val += 1
                
            colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
            colormap.caption = f"Legend: {map_metric}"

            if map_metric == 'Crime_Rate':
                t_fields = ['LSOA21LN', 'LSOA21NM', map_metric, 'Total_Crimes']
                t_aliases = ['Local Name:', 'Code Name:', 'Crime Rate/1000:', 'Total Incidents:']
            else:
                t_fields = ['LSOA21LN', 'LSOA21NM', map_metric]
                t_aliases = ['Local Name:', 'Code Name:', f'{map_metric} Score:']

            folium.GeoJson(
                geojson_data,
                name=f"Neighbourhood Areas ({map_metric})",
                style_function=lambda feature: {
                    'fillColor': colormap(feature['properties'][map_metric]) if feature['properties'].get(map_metric) is not None else 'gray',
                    'color': 'black', 'weight': 0.5, 'fillOpacity': 0.7,
                },
                highlight_function=lambda x: {'weight': 2, 'color': 'black', 'fillOpacity': 1.0},
                tooltip=folium.GeoJsonTooltip(fields=t_fields, aliases=t_aliases, localize=True, sticky=True)
            ).add_to(m)
            
            colormap.add_to(m)

        # 4. Crime Hotspot Layer (Heatmap)
        heat_data = filtered_incidents[['Latitude', 'Longitude']].dropna().values.tolist()
        if heat_data:
            HeatMap(
                heat_data, 
                name="Crime Hotspots", 
                radius=10, blur=15, min_opacity=0.4,
                gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}
            ).add_to(m)
            
        # 5. NIGHT-TIME ECONOMY LAYER
        pub_layer = folium.FeatureGroup(name="Night-Time Economy", show=False)
        
        for _, row in pubs_df.iterrows():
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=3,
                color='black',
                weight=0,
                fill=True,
                fill_color='black', 
                fill_opacity=0.8,
                popup=folium.Popup(f"<b>{row['BUSINESS_NAME']}</b><br>{row['BUSINESS_TYPE']}", max_width=200)
            ).add_to(pub_layer)
        pub_layer.add_to(m)

        # 6. Render Map
        folium.LayerControl(collapsed=False).add_to(m) 
        
        # --- FIX: REMOVED FIXED WIDTH SO IT FITS THE COLUMN ---
        st_folium(m, height=700, width=None) # width=None allows it to be responsive
        
    with col2:
        st.write("### Map Interpretation")
        st.info(f"""
        **Layer Controls (Top Right):**
        * **Simple Background:** Best for viewing deprivation colours.
        * **Crime Hotspots:** The heatmap of filtered incidents.
        * **Night-Time Economy:** Toggles Pubs & Clubs (Black Dots).
        
        **Analysis Tip:**
        1. Select **'Boundaries Only'** in the sidebar.
        2. Turn on **Crime Hotspots** in the map layer control.
        3. Turn on **Night-Time Economy**.
        4. Observe how the black dots (Clubs) align perfectly with the hotspots!
        """)

# --- TAB 2: STATISTICAL ANALYSIS ---
with tab2:
    st.subheader("Crime Distribution Trends")
    
    # Chart 1: Categorical Distribution
    if not filtered_incidents.empty:
        fig_bar = px.bar(filtered_incidents['Crime type'].value_counts().reset_index(), 
                         x='Crime type', y='count', color='Crime type',
                         title=f"Total Recorded Incidents by Category ({start_date} to {end_date})")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Chart 2: Temporal Trends
        st.subheader("Temporal Analysis: Monthly Crime Trends")
        monthly_trends = filtered_incidents.groupby(['Month', 'Crime type']).size().reset_index(name='Incident_Count')
        crime_order = filtered_incidents['Crime type'].value_counts().index.tolist()
        
        fig_line = px.line(
            monthly_trends, x='Month', y='Incident_Count', color='Crime type', 
            title="Crime Trends Over Time", markers=True,
            category_orders={"Crime type": crime_order},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_line.update_xaxes(dtick="M1", tickformat="%b %Y")
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.divider()
        
        # Chart 3 & 4: Correlation Analysis
        st.subheader("Socioeconomic Correlation Analysis")
        col_a, col_b = st.columns(2)
        
        with col_a:
            fig_scatter = px.scatter(
                master_df, x='Income', y='Crime_Rate', 
                marginal_x="box", marginal_y="box",
                hover_name='LSOA21LN', hover_data=['LSOA21NM'], 
                trendline="ols",
                title="Correlation: Income Deprivation vs. Crime Rate",
                labels={'Income': 'Income Score (Higher = Poorer)', 'Crime_Rate': 'Crimes per 1,000'}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col_b:
            corr = master_df[['Crime_Rate', 'IMDScore', 'Income', 'Employment', 'EducationScore']].corr()
            fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', 
                                 title="Statistical Correlation Matrix")
            st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Please adjust filters to see statistical analysis.")

# --- TAB 3: DATA EXPLORER ---
with tab3:
    st.subheader("Comparative Analysis: Poverty vs. Crime Hotspots")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Top 10 Most Deprived")
        top_deprived = master_df.sort_values(by='IMDScore', ascending=False).head(10)
        st.dataframe(top_deprived[['LSOA21LN', 'IMDScore', 'Crime_Rate']], hide_index=True, use_container_width=True)

    with col2:
        st.markdown("### Top 10 Highest Crime Rates")
        top_crime = master_df.sort_values(by='Crime_Rate', ascending=False).head(10)
        st.dataframe(top_crime[['LSOA21LN', 'Crime_Rate', 'IMDScore']], hide_index=True, use_container_width=True)

    # Overlap Logic
    deprived_names = set(top_deprived['LSOA21LN'])
    crime_names = set(top_crime['LSOA21LN'])
    common_areas = deprived_names.intersection(crime_names)
    
    st.divider()
    st.subheader("Overlap Analysis")
    if len(common_areas) > 0:
        st.warning(f"**Key Finding:** {len(common_areas)} out of 10 neighbourhoods appear in both lists: **{', '.join(list(common_areas))}**")
    else:
        st.success("**Key Finding:** Zero overlap between Top 10 Poorest and Top 10 High-Crime areas.")