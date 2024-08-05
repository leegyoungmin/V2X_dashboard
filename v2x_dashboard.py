import json
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import plotly.graph_objects as go
from urllib.request import urlopen
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# batchtime = datetime.now() - timedelta(days=1)
# batchtime = batchtime.strftime("%y%m%d")
data = pd.read_csv('/home/ubuntu/work/data/car_info/state_speed_240802.csv')
data = data.loc[:, ['vhcleTypeCd', 'vhcleSped', 'addr']]

state_geo_path = 'https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json'
with urlopen(state_geo_path) as response:
    state_geo = json.load(response)

code_dict = {
    "그외": 9217,
    "승용차/택시": 9220,
    "버스": 9228,
    "버스외 전기차": 9252,
    "hybrid차": 9253,
    "상용차/트럭": 9255
}

color_theme_list = {
    "YlGn": "#31a354",
    "BuGn": "#1c9099",
    "BuPu": "#756bb1",
    "GnBu": "#43a2ca",
    "OrRd": "#e34a33",
    "PuBu": "#2b8cbe",
    "PuBuGn": "#02818a",
    "PuRd": "#dd1c77",
    "RdPu": "#c51b8a",
    "YlGnBu": "#41b6c4",
    "YlOrRd": "#f03b20"
}

st.set_page_config(
    page_title="서울시 자율주행차 대시보드",
    page_icon="🚙",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.title("🚙 서울시 자율주행차 대시보드")

    code_list = list(data['vhcleTypeCd'].unique())
    filtered_code_dict = {key: value for key, value in code_dict.items() if value in code_list}
    selected_code_name = st.selectbox('차량코드를 선택하세요', list(filtered_code_dict.keys()), index=len(filtered_code_dict) - 1)
    selected_code_value = filtered_code_dict.get(selected_code_name)
    data_selected_code = data[data['vhcleTypeCd'] == selected_code_value]
    data_selected_code_sorted = data_selected_code.sort_values(by="vhcleTypeCd", ascending=True)

    selected_color_theme = st.selectbox('색상 테마를 선택하세요', list(color_theme_list.keys()))

col = st.columns((3, 4, 3), gap='small', vertical_alignment="top")

overall_avg_speed = data_selected_code['vhcleSped'].mean()
overall_max_speed = data_selected_code['vhcleSped'].max()

total_count_data = data_selected_code.groupby("addr").count()
total_count_data["addr"] = total_count_data.index.tolist()
total_count_data = total_count_data.loc[:, ["vhcleTypeCd", "addr"]]
total_count_data = total_count_data.sort_values(by=['vhcleTypeCd'], axis=0, ascending=False)

avg_fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=overall_avg_speed,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font_color': 'black', 'font_size': 60},
        title={'text': "전체 평균 속도", 'font_color': 'black', 'font_size': 25},
        delta={'reference': 90},
        gauge={'axis': {'range': [None, 60]},
               'bar': {'color': color_theme_list[selected_color_theme]},
               'steps': [
                   {'range': [0, 250], 'color': 'white'},
                   {'range': [250, 400], 'color': "black"}
               ]
               }
    )
)

max_fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=overall_max_speed,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font_color': 'black', 'font_size': 60},
        title={'text': "최고 속도", 'font_color': 'black', 'font_size': 25},
        delta={'reference': 10},
        gauge={'axis': {'range': [None, 60]},
               'bar': {'color': color_theme_list[selected_color_theme]},
               'steps': [
                   {'range': [0, 250], 'color': 'white'},
                   {'range': [250, 400], 'color': "gray"}
               ]}
    )
)

with col[0]:
    with st.container(border=True, height=800):
        avg_fig.update_layout(height=350)
        max_fig.update_layout(height=350)
        st.plotly_chart(avg_fig)
        st.plotly_chart(max_fig)

with col[1]:
    with st.container(border=True, height=800):
        st.markdown('#### 행정구별 평균속도')
        m = folium.Map(
            location=[37.557, 126.979],
            tiles='cartodbpositron',
            zoom_start=11
        )

        folium.Choropleth(
            geo_data=state_geo,
            name='choropleth',
            data=data_selected_code,
            columns=['addr', 'vhcleSped'],
            key_on='feature.properties.name',
            fill_color=selected_color_theme,
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='행정구별 평균속도'
        ).add_to(m)

        st_folium(m, width=800, height=600, use_container_width=True)

        with st.expander("더보기"):
            groupby_speed = data_selected_code.groupby("addr").mean().iloc[:, 1]
            groupby_speed.columns = ["구", "평균 속도"]
            st.table(groupby_speed)

with col[2]:
    with st.container(border=True, height=600):
        st.markdown('#### 서울시 측정 차량수')
        fig = px.bar(
            total_count_data,
            x='vhcleTypeCd',
            y='addr',
            orientation='h',
            color_discrete_sequence=[color_theme_list[selected_color_theme]],
            labels={'addr': '행정구', 'vhcleTypeCd': '차량 수'},
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig)
    with st.container(border=True):
        st.write(
            '''
            - 데이터 : [차량 상태 위치 정보 서비스](<https://t-data.seoul.go.kr/dataprovide/trafficdataviewopenapi.do?data_id=10118>)
            - :blue-background[서울시] 정보만 수집하여 분석했습니다.
            - :blue[매일 1:00] 에 업데이트됩니다. 
            ''')
