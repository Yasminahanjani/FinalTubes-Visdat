import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from sklearn.preprocessing import LabelEncoder
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, GeoJSONDataSource, LinearColorMapper, ColorBar, FactorRange, NumeralTickFormatter
from bokeh.palettes import Plasma256, Pastel1
from bokeh.transform import dodge, factor_cmap
from shapely.geometry import shape
import gdown

# Judul dan Deskripsi Halaman Web
st.set_page_config(page_title="DALY & Death Analysis", layout="wide")
st.title("\U0001F4CA Menggali Fakta Kesehatan: DALYs dan Kematian di 25 Negara Ekonomi Terbesar di Dunia (2000–2019)")
st.markdown("Halaman website ini bertujuan untuk memberikan visualisasi analisis data DALY (Disability-Adjusted Life Years) dan kematian dari 25 negara ekonomi terbesar di dunia antara tahun 2000 hingga 2019.")
st.markdown("Disusun oleh Kelompok 3 : ")
st.markdown("1. **Yasmina Arethaya Hanjani (1301223008)**")
st.markdown("2. **Yesi Sukmawati (1301223031)**")
st.markdown("3. **Kaila Fiorenza Gampo (1301223084)**")

# Panggil data dan preprocesssing
@st.cache_data
def load_data():
    if not os.path.exists("data.csv"):
        url = "https://drive.google.com/uc?id=11HjGz-LPT84Zk_W_fzk-JHr_AyBHZr1I"
        gdown.download(url, "data.csv", quiet=False)
    
    df = pd.read_csv("data.csv")
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)

    # Encoding kolom gender dan kode negara
    df['SEX_CODE'] = df['SEX_CODE'].map({'FMLE': 0, 'MLE': 1})
    le = LabelEncoder()
    df['COUNTRY_CODE_ENCODED'] = le.fit_transform(df['COUNTRY_CODE'])
    df['AGEGROUP_CODE_ENCODED'] = le.fit_transform(df['AGEGROUP_CODE'])
    
    # Normalisasi nama negara
    df['COUNTRY'] = df['COUNTRY'].replace({
        'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
        'Iran (Islamic Republic of)': 'Iran',
        'Republic of Korea': 'South Korea',
    })
    df['GENDER'] = df['SEX_CODE'].map({1: 'Male', 0: 'Female'})
    return df

df = load_data()
years = sorted(df['YEAR'].unique())

## Opsi Sidebar ##
st.sidebar.header("Filter Data")
# Sliding pilih tahun range 2000-2019 (per 5 tahun)
st.sidebar.markdown("Pilih tahun melihat data berdasarkan tahun.")
year_options = [2000, 2005, 2010, 2015, 2019]
selected_year = st.sidebar.select_slider(
    "Tahun",
    options=year_options,
    value=year_options[-1]
)
# Dropdown pilih negara 
st.sidebar.markdown("Pilih negara untuk melihat data berdasarkan negara.")
negara_opsi = ["All"] + sorted(df['COUNTRY'].unique())
selected_country = st.sidebar.selectbox("Negara", negara_opsi)
is_global = selected_country == "All"

# Filter data berdasarkan tahun dan negara yang dipilih
filtered_df = df[(df['YEAR'] == selected_year) & (df['COUNTRY'] == selected_country)]

# Menampilkan informasi dataset (top 5) jika memilih "ALL"
if is_global:
    st.subheader("🔍 5 Data teratas di Dataset")
    st.dataframe(df.head(5))

# PLOT 1: Populasi berdasarkan Gender menggunakan barplot
if not is_global: # Ditampilkan hanya jika memfilter negara tertentu
    st.subheader(f"👨‍👩‍👧 Populasi di {selected_country} ({selected_year})")
    pop_by_gender = filtered_df.groupby("GENDER")["POPULATION"].sum().reset_index()
    gender = pop_by_gender['GENDER'].tolist()
    counts = pop_by_gender['POPULATION'].tolist()

    source = ColumnDataSource(data=dict(gender=gender, counts=counts))

    p1 = figure(x_range=gender, height=350, toolbar_location=None, title="Populasi berdasarkan Gender")
    p1.vbar(x='gender', top='counts', width=0.9, source=source, legend_field="gender",
            line_color='white', fill_color=factor_cmap('gender', palette=Pastel1[9], factors=gender))
    p1.xgrid.grid_line_color = None
    p1.y_range.start = 0
    p1.yaxis.formatter = NumeralTickFormatter(format="0,0") # Format penulisan angka
    p1.legend.orientation = "vertical"
    p1.legend.location = "top_center"

    hover_p1 = HoverTool(tooltips=[("Gender", "@gender"), ("Populasi", "@counts{0,0}")])
    p1.add_tools(hover_p1)

    st.bokeh_chart(p1, use_container_width=True)

# PLOT 2: Top 20 Penyebab Kematian Tertinggi menggunakan horizontal bar plot
st.subheader("☠️ 20 Penyebab Kematian Tertinggi")

if is_global: # Jika memilih "All" Maka akan ditampilkan berdasarkan 25 negara
    top_25_countries = df['COUNTRY'].unique()
    top_death_filtered = df[(df['YEAR'] == selected_year) & (df['COUNTRY'].isin(top_25_countries))]
    top_death_cause = (
        top_death_filtered.groupby('GHE_CAUSE_TITLE')['DEATHS']
        .sum()
        .sort_values(ascending=False)
        .head(20)
        .reset_index()
    )

    top_death_cause['label'] = top_death_cause['GHE_CAUSE_TITLE']

    source2 = ColumnDataSource(top_death_cause)
    index_cmap2 = factor_cmap('label', palette=Plasma256[:len(top_death_cause)], factors=top_death_cause['label'])

    p2 = figure(y_range=top_death_cause['label'][::-1], height=600, title=f"Top 20 Penyebab Kematian dari 25 Negara ({selected_year})",
                toolbar_location=None, tools="hover", tooltips=[("Jumlah Kematian", "@DEATHS{0,0}"),("Penyebab", "@label")])
    p2.hbar(y='label', right='DEATHS', height=0.8, source=source2,
            fill_color=index_cmap2, line_color='white')
    p2.xaxis.axis_label = "Jumlah Kematian"
    p2.yaxis.axis_label = "Penyebab Kematian"
    p2.xaxis.formatter = NumeralTickFormatter(format="0,0")
    p2.y_range.range_padding = 0.05
    p2.xgrid.grid_line_color = None
    p2.outline_line_color = None

    st.bokeh_chart(p2, use_container_width=True)

else: # Jika memilih negara tertentu, berdasarkan selected_country
    top_death_filtered = df[(df['YEAR'] == selected_year) & (df['COUNTRY'] == selected_country)]
    top_death_cause = (
        top_death_filtered.groupby('GHE_CAUSE_TITLE')['DEATHS']
        .sum()
        .sort_values(ascending=False)
        .head(20)
        .reset_index()
    )

    top_death_cause['label'] = top_death_cause['GHE_CAUSE_TITLE']
    source2 = ColumnDataSource(top_death_cause)
    index_cmap2 = factor_cmap('label', palette=Plasma256[:len(top_death_cause)], factors=top_death_cause['label'])

    p2 = figure(y_range=top_death_cause['label'][::-1], height=600, title=f"Top 20 Penyebab Kematian di {selected_country} ({selected_year})",
                toolbar_location=None, tools="hover", tooltips=[("Jumlah Kematian", "@DEATHS{0,0}"),("Penyebab", "@label")])
    p2.hbar(y='label', right='DEATHS', height=0.8, source=source2,
            fill_color=index_cmap2, line_color='white')
    p2.xaxis.axis_label = "Jumlah Kematian"
    p2.yaxis.axis_label = "Penyebab Kematian"
    p2.xaxis.formatter = NumeralTickFormatter(format="0,0")
    p2.y_range.range_padding = 0.05
    p2.xgrid.grid_line_color = None
    p2.outline_line_color = None

    st.bokeh_chart(p2, use_container_width=True)

# PLOT 3: Tren DALY per Tahun Menggunakan line plot, ditampilkan jika memilih "ALL"
if is_global:
    st.subheader("📉 Tren Rata-rata DALY Rate Global")
    # Hitung rata-rata DALY Rate per tahun
    daly_trend = df.groupby('YEAR', as_index=False)['DALY_RATE'].mean()
    daly_trend['DALY_LABEL'] = daly_trend['DALY_RATE'].apply(lambda x: f"{x:.5f}")

    source3 = ColumnDataSource(data={
        'YEAR': daly_trend['YEAR'],
        'DALY_RATE': daly_trend['DALY_RATE'],
        'DALY_LABEL': daly_trend['DALY_LABEL']
    })

    p3 = figure(title="Rata-rata DALY Rate (2000–2019)", 
                x_axis_label='Tahun', y_axis_label='DALY Rate', 
                height=400, tools="")

    p3.line(x='YEAR', y='DALY_RATE', source=source3, line_width=3, color="orange")
    circles = p3.circle(x='YEAR', y='DALY_RATE', source=source3, size=8, color="red")

    hover = HoverTool(renderers=[circles],
                    tooltips=[("Tahun", "@YEAR"), ("DALY Rate", "@DALY_LABEL")])
    p3.add_tools(hover)

    st.bokeh_chart(p3, use_container_width=True)    

# PLOT 4: Peta Dunia yang menampilkan informasi kematian dan DALY per negara
st.subheader("\U0001F30E Peta Kematian & DALY Global per Negara")

@st.cache_data
def load_world_geojson(): # Mengimport geojson (file untuk peta dunia)
    geojson_path = "world_countries.geojson"
    if not os.path.exists(geojson_path):
        st.error("File 'world_countries.geojson' tidak ditemukan.")
        return None
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
    return geojson_data

geodata = load_world_geojson()
if geodata:
    world_df = pd.json_normalize(geodata['features'])
    world_df["COUNTRY"] = world_df["properties.ADMIN"]

    agg_data = df[df['YEAR'] == selected_year].groupby('COUNTRY')[['DEATHS', 'DALY']].sum().reset_index()

    # BKarena pada dataset hanya terdapat Republic of Korea, maka Korea selatan dan Utara akan memiliki data yang sama
    korea_data = agg_data[agg_data['COUNTRY'] == 'South Korea']
    for korea in ['North Korea', 'Republic of Korea']:
        if not korea_data.empty:
            new_row = korea_data.copy()
            new_row['COUNTRY'] = korea
            agg_data = pd.concat([agg_data, new_row], ignore_index=True)

    world_df = world_df.merge(agg_data, on="COUNTRY", how="left")
    world_df["DEATHS"] = world_df["DEATHS"].fillna(0)
    world_df["DALY"] = world_df["DALY"].fillna(0)

    def enrich_geojson(base_geojson, value_df):
        for feature in base_geojson['features']:
            country = feature['properties']['ADMIN']
            match = value_df[value_df['COUNTRY'] == country]
            if not match.empty:
                feature['properties']['DEATHS'] = float(match['DEATHS'].values[0])
                feature['properties']['DALY'] = float(match['DALY'].values[0])
            else:
                feature['properties']['DEATHS'] = None
                feature['properties']['DALY'] = None
        return base_geojson

    enriched_geojson = enrich_geojson(geodata, world_df)
    geo_source = GeoJSONDataSource(geojson=json.dumps(enriched_geojson))

    # Membuat range warna untuk peta berdasarkan jumlah kematian
    color_mapper = LinearColorMapper(palette=Plasma256, low=world_df["DEATHS"].min(), high=world_df["DEATHS"].max())
    
    # Mengaktifkan hover tool untuk menampilkan informasi kematian dan DALY
    hover = HoverTool(tooltips=[("Negara", "@ADMIN"),
                                ("Kematian", "@DEATHS{0,0}"),
                                ("DALY", "@DALY{0,0}")])

    selected_shape = None
    for feature in geodata['features']:
        if feature['properties']['ADMIN'] == selected_country:
            selected_shape = shape(feature['geometry'])
            break

    if selected_shape:
        minx, miny, maxx, maxy = selected_shape.bounds
        x_range = (minx - 5, maxx + 5)
        y_range = (miny - 5, maxy + 5)
    else:
        x_range = None
        y_range = None

    # Mengaktifkan fitur pan, zoom, reset, dan hover pada peta
    p_map = figure(title="Total Kematian dan DALY per Negara (2000–2019)",
                   tools=["pan", "wheel_zoom", "reset", hover],
                   x_axis_location=None, y_axis_location=None,
                   x_range=x_range, y_range=y_range)
    p_map.grid.grid_line_color = None
    p_map.patches('xs', 'ys', source=geo_source,
                  fill_color={'field': 'DEATHS', 'transform': color_mapper},
                  line_color="white", line_width=0.5, fill_alpha=0.8)
    color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))
    p_map.add_layout(color_bar, 'right')

    st.bokeh_chart(p_map, use_container_width=True)


# PLOT 5: Perbandingan Jumlah DALY dan Kematian per Kelompok Usia menggunakan vertical bar plot
st.subheader(f"🧒👵 Perbandingan Jumlah DALY dan Kematian di {selected_year}")

# Group by agegroup dan jumlahkan DALY dan DEATHS per kelompok usia
agegroup_stats = df[df['YEAR'] == selected_year].groupby('AGEGROUP_CODE')[['DEATHS', 'DALY']].sum().reset_index()
agegroups = agegroup_stats['AGEGROUP_CODE'].astype(str).tolist()

source6 = ColumnDataSource(data=dict(
    agegroups=agegroups,
    DALY=agegroup_stats['DALY'],
    DEATHS=agegroup_stats['DEATHS']
))

p6 = figure(x_range=FactorRange(*agegroups), height=420,
            title=f"Jumlah DALY vs Kematian per Kelompok Usia ({selected_year})",
            toolbar_location=None, tools="")

p6.vbar(x=dodge('agegroups', -0.15, range=p6.x_range), top='DEATHS', width=0.3,
        source=source6, color="#c9d9d3", legend_label="Jumlah Kematian")

p6.vbar(x=dodge('agegroups', 0.15, range=p6.x_range), top='DALY', width=0.3,
        source=source6, color="#3f53d6", legend_label="Jumlah DALY")

# Aktidkan hover tool untuk menampilkan informasi jumlah kematian dan DALY
hover6 = HoverTool(tooltips=[
    ("Kelompok Usia", "@agegroups"),
    ("Jumlah Kematian", "@DEATHS{0,0}"),
    ("Jumlah DALY", "@DALY{0,0}")
])
p6.add_tools(hover6)

p6.y_range.start = 0
p6.xaxis.axis_label = "Kelompok Usia"
p6.yaxis.axis_label = "Jumlah"
p6.xaxis.major_label_orientation = 1
p6.xgrid.grid_line_color = None
p6.legend.orientation = "horizontal"
p6.legend.location = "top_left"

st.bokeh_chart(p6, use_container_width=True)