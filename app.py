### load all necessary libraries
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

dataset = "Motor_Vehicle_Collisions_-_Crashes.csv"

### Project title
st.title("Motor Vehicle Collisions in New York City")

st.markdown("""
    ### This application is an interactive dashboard that can be used to analyze motor vehicle collisions in the city of New York. 
    
    #### The app was built using Python's relatively new [Streamlit](https://streamlit.io) Web Framework.

    #### <b>Data Description</b>:
    
    <i>Dataset used in this project is an open-source data and is availbale to the public at
    [DATA.GOV](https://catalog.data.gov/dataset/nypd-motor-vehicle-collisions-07420)'s data catalog.
     The following dataset is based on NYPD's past reports on traffic accidents and includes more than 1.6 million incidents of vehicle crashes.
    </i>
        """, unsafe_allow_html=True)

### Add image
image = "NY_collision_image_1.jpg"
st.image(image, use_column_width=True)

### Add image source
st.markdown("""<p style="text-align:left;">
                    <i> Image Source:</i> <u> <b>  CNN News Agency </b> </u> 
                </p> """, unsafe_allow_html=True)

### Break the lines between two consecutive objects
st.markdown("<br> </br>", unsafe_allow_html=True)


### The decorator below ensures that data is loaded only once and is cached for future use.
@st.cache(persist = True) ### Thus, code is rerun only when input data or code inside has changed.
def load_data(nrows = 100_000):
    data = pd.read_csv(dataset, nrows=nrows,parse_dates = [['CRASH_DATE', 'CRASH_TIME']])    
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace = True)  ### Otherwise map plotting in Streamlit 
                                                                   ### will not work if values for longitude and/or latitute are missing

    lowercase = lambda x: str(x).lower() ### For the sake of personal convenience, I will lowercase all column names
    data.rename(lowercase, axis = 'columns', inplace = True)
    data.rename(columns={'crash_date_crash_time': "date/time"}, inplace = True)
    return data

data = load_data()
original_data = data


### Filter vehicle collisions on hourly basis
st.header('How many collisions occur during a given time of a day?')
hour = st.sidebar.slider("Hours to look at", 0, 23)
data = data[data['date/time'].dt.hour == hour]


### Option to see data inside the table 
show_raw_data_checkbox = st.sidebar.checkbox(label = 'Show Raw Data', value = False)
if show_raw_data_checkbox is True:
    st.sidebar.subheader("Data Display Options")
    display_options = st.sidebar.radio(label = "Please select one:", options = ["Show Full Data", "Selected Data" ])
    
    if display_options == "Show Full Data":
        st.subheader("Raw Data")
        st.write(data)
    

    elif display_options == "Selected Data":
        st.write("If you are interested in viewing only certain columns, you can refine your selection in the menu below")

        defaultcols = ["date/time", "borough", "on_street_name", 'cross_street_name', 'injured_persons', 
                    'killed_persons', 'injured_pedestrians', 'killed_pedestrians', 'injured_cyclists',
                    'killed_cyclists', 'injured_motorists', 'killed_motorists']

        cols_needed = st.multiselect("Columns selected", data.columns.tolist(), default=defaultcols)
        st.dataframe(data[cols_needed].head(10))

st.markdown("<hr>", unsafe_allow_html=True)
st.subheader(f"""Vehicle Collissions between {hour}:00 and {hour+1}:00 """) 


# Adding code so we can have map default to the center of the data
midpoint_NY = (np.median(data['latitude']), np.median(data['longitude']))

### Show the locations of accidents on a map
st.write(pdk.Deck(
    map_style = "mapbox://styles/mapbox/light-v9",
    initial_view_state = {"latitude": midpoint_NY[0],
                          "longitude": midpoint_NY[1],
                          "zoom": 10,
                          "pitch": 50,
                          },
    layers = [pdk.Layer(
                    "HexagonLayer",
                    data = data[['date/time', 'latitude', 'longitude']],
                    get_position = ['longitude', 'latitude'],
                    radius = 100,
                    extruded = True, ## This makes 3D data points instead of 2D
                    pickable = True,
                    elevation_scale = 4,
                    elevation_range = [0,1000],
                    ),],
    ))

st.markdown("<br> </br>", unsafe_allow_html=True)

### Create a similar map representing the number of people injured during accidents
st.header("Where in NYC do most people get injured?")
injured_people = st.slider('Number of people injured in vehicle collisions', 0, int(data["injured_persons"].max()) )

st.write(pdk.Deck(
    map_style = "mapbox://styles/mapbox/streets-v11",
    initial_view_state = {"latitude": midpoint_NY[0],
                          "longitude": midpoint_NY[1],
                          "zoom": 10,
                          "pitch": 50,
                          },
    layers = [pdk.Layer(
                    "HexagonLayer",                    
                    data = data.query("injured_persons >= @injured_people")[["latitude", "longitude"]].dropna(how = "any"),
                    get_position = ['longitude', 'latitude'],
                    radius = 100,
                    extruded = True,
                    pickable = True,
                    elevation_scale = 4,
                    elevation_range = [0,1000],
                    ),],
    ))

st.markdown("<hr> ", unsafe_allow_html=True)


### Histogram showing a ditribution of car accidents during a chosen hour
st.header("Distribution of accidents on a minute basis")
st.subheader(f'Breakdown of collisions by minutes between {hour}:00 and {hour+1}:00')

filtered = data[((data['date/time'].dt.hour>=hour) & (data['date/time'].dt.hour<hour+1))]
hist = np.histogram(filtered['date/time'].dt.minute, bins = 60, range = (0,60))[0]
chart_data = pd.DataFrame({'minute': range(60), 'crashes': hist})
fig = px.bar(chart_data, x = 'minute', y = 'crashes', hover_data = ['minute', 'crashes'], height = 400)
st.write(fig)

### Add a table that shows top 5 most dangerous streets 
st.header("New York's top 5 streets with the greatest number of people affected during accidents")
select = st.selectbox('Filter by category of people affected', ['Pedestrians', 'Cyclists', 'Motorists'])

if select == 'Pedestrians':
    st.write(original_data.query("injured_pedestrians >= 1")[["on_street_name", "injured_pedestrians"]].sort_values(by = ['injured_pedestrians'], ascending = False).dropna(how='any')[:5])

elif select == 'Cyclists':
    st.write(original_data.query("injured_cyclists >= 1")[["on_street_name", "injured_cyclists"]].sort_values(by = ['injured_cyclists'], ascending = False).dropna(how='any')[:5])

elif select == 'Motorists':
    st.write(original_data.query("injured_motorists >= 1")[["on_street_name", "injured_motorists"]].sort_values(by = ['injured_motorists'], ascending = False).dropna(how='any')[:5])




