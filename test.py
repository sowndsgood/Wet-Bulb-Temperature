import requests
import math
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
import streamlit as st
from datetime import datetime
import pandas as pd
import os
import folium
from streamlit_folium import folium_static
from PIL import Image
import pytz  # Add this import for timezone support
import plotly.express as px

def get_weather_data(city):
    api_key = '71aa83b817d6fff071b7d63b02843f66'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={api_key}&units=metric'
    response = requests.get(url)
    data = response.json()
    try:
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        return temperature, humidity
    except KeyError:
        try:
            temperature = data['current']['temp']
            humidity = data['current']['humidity']
            return temperature, humidity
        except KeyError:
            print("Error: Unable to fetch weather data for", city)
            print("API response:", data)
            return None, None

def calculate_wet_bulb_temperature(temperature, humidity):
    T = temperature
    RH = humidity
    term1 = T * math.atan(0.151977 * ((RH + 8.313659) ** 0.5))
    term2 = math.atan(T + RH)
    term3 = math.atan(RH - 1.676331)
    term4 = 0.00391838 * (RH ** 1.5) * math.atan(0.023101 * RH)
    constant_term = -4.686035
    WBT = term1 + term2 - term3 + term4 + constant_term
    return WBT

def get_current_time(timezone_str='Asia/Kolkata'):
    tz = pytz.timezone(timezone_str)
    current_time = datetime.now(tz)
    return current_time.strftime("%Y-%m-%d %H:%M:%S")

# Create Streamlit app
def main():
    # Display image at the top of the app
    st.image("heat.jpg", use_column_width=True)

    st.title('Wet Bulb Temperature for Coastal Cities in India')
    st.markdown("""
    Welcome to the Wet Bulb Temperature Monitoring App. This tool helps you monitor the wet bulb temperatures in various coastal cities in India.
    Select a city from the dropdown menu to see the current temperature, humidity, and wet bulb temperature.You can also visualize the Wet Bulb Temperature (WBT) data for different cities and years. The wet bulb temperature is an important metric to understand heat stress. 
    If the wet bulb temperature exceeds 30°C (86°F), it can pose serious health risks.
    """)

    # Data source
    st.markdown("**Data Source:**<span style='color:orange;'> OpenWeatherMap API</span> for current data and <span style='color:orange;'>Iowa State University</span> for historical data", unsafe_allow_html=True)

    # Get current date and time
    

    st.sidebar.markdown("# Current Date and Time")
    current_time = get_current_time()
    
    st.sidebar.write(f"{current_time}")
   
    # About section in the sidebar with color
    st.sidebar.title("About")

    # Description of the app with color
    st.sidebar.markdown("""This web application provides real-time weather information, including temperature, humidity, and wet bulb temperature, for coastal cities in India. Users can visualize the Wet Bulb Temperature (WBT) data for different cities and years.
    """)

    # Data source with color
    st.sidebar.markdown("""
    <span style='color: #008000;'>Data Source:</span> OpenWeatherMap API and Iowa State University
    """, unsafe_allow_html=True)

    # Developer information with color
    st.sidebar.markdown("""
    <span style='color:red;'>Developed by:</span> Sowndarya S
    """, unsafe_allow_html=True)

    # Acknowledgments with color
    st.sidebar.markdown("""
    <span style='color: #8A2BE2;'>Reference: https://www.omnicalculator.com/physics/wet-bulb
    """, unsafe_allow_html=True)

    # Add any additional information as needed


    
    
    # List of coastal cities in India
    cities = [
        'Mumbai', 'Chennai', 'Kolkata', 'Goa', 'Kochi', 
        'Visakhapatnam', 'Mangalore', 'Pondicherry', 
        'Kanyakumari', 'Surat', 'Karaikal', 'Nagapattinam', 
        'Alappuzha'
    ]

    # Dropdown menu to select city
    selected_city = st.selectbox('Select a city to check Wet Bulb Temperature:', cities)

    temperature, humidity = get_weather_data(selected_city)
    if temperature is not None and humidity is not None:
        wbt = calculate_wet_bulb_temperature(temperature, humidity)
        
        with st.expander("View Weather Information here"):
            st.write(f'Temperature: {temperature} °C')
            st.write(f'Humidity: {humidity}%')
            st.write(f'Wet Bulb Temperature (WBT): {wbt:.2f} °C')

        # Display appropriate message based on WBT value
        if wbt > 30:
            st.markdown("<span style='color:red;'>Wet-bulb temperatures above 30 °C (86 °F) can be deadly outside. Avoid direct sunlight and drink plenty of water.</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:green;'>Wet-bulb temperatures are within safe limits. Enjoy the weather responsibly and stay hydrated.</span>", unsafe_allow_html=True)
    else:
        st.error("No data available. Please try again later.")

      # Create a Folium map object
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

    # Add markers for each city with wet bulb temperature as popup
    for city in cities:
        temperature, humidity = get_weather_data(city)
        if temperature is not None and humidity is not None:
            wbt = calculate_wet_bulb_temperature(temperature, humidity)
            popup_text = f"{city}<br>Wet Bulb Temperature: {wbt:.2f} °C"
            folium.Marker(location=get_coordinates(city), popup=popup_text).add_to(m)
    
    st.write("### Map of coastal cities:")
    st.write("You can view the Wet Bulb Temperature by clicking on each city.")

    # Display the map in Streamlit
    folium_static(m)

    st.write("### Plot of Wet Bulb Temperature of coastal cities:")

    plot_map(cities) 


    # Load the temperature data, converting "M" to NaN
    temp_df = pd.read_csv('temp.csv', na_values='M')

    # Load the humidity data, converting "M" to NaN
    humid_df = pd.read_csv('humid.csv', na_values='M')

    # Rename 'relh' to 'humidity' to match the calculation function
    humid_df.rename(columns={'relh': 'humidity'}, inplace=True)

    # Handling NaN values - example: dropping rows with NaNs
    temp_df.dropna(inplace=True)
    humid_df.dropna(inplace=True)

    # Merge the dataframes on 'station' and 'valid' columns
    combined_df = pd.merge(temp_df, humid_df, on=['station', 'valid'])


    # Calculate the Wet Bulb Temperature for each row
    combined_df['WBT_C'] = combined_df.apply(lambda row: calculate_wet_bulb_temperature(row['tmpc'], row['humidity']), axis=1)

    # Save the combined DataFrame with WBT to a new CSV file
    combined_df.to_csv('combined_with_wbt.csv', index=False)

    # Load the combined data
    df = pd.read_csv('combined_with_wbt.csv')

    # Mapping station codes to station names
    station_names = {
    'VECC': 'Calcutta',
    'VABB': 'Mumbai',
    'VASU': 'Surat',
    'VOCI': 'Cochin',
    'VOGO': 'Goa',
    'VOMM': 'Madras',
    'VOVZ': 'Vishakhapatnam',
    'VOTV': 'Trivandrum'
    }

    # Add a column with station names
    df['station_name'] = df['station'].map(station_names)

    # Streamlit app
    st.header(" Wet Bulb Temperature Visualization")

    # Main area for filters
    st.write("##### Filters")

    # City selection
    cities = df['station_name'].unique()
    selected_city = st.selectbox('Select City', cities)

    # Year selection
    df['year'] = pd.to_datetime(df['valid']).dt.year
    years = df['year'].unique()
    selected_year = st.selectbox('Select Year', years)

    # Filter data based on selections
    filtered_df = df[(df['station_name'] == selected_city) & (df['year'] == selected_year)]

    # Plotting
    
    fig = px.line(filtered_df, x='valid', y='WBT_C', title=f'Wet Bulb Temperature in {selected_city} for {selected_year}')
    fig.update_layout(xaxis_title='Date', yaxis_title='Wet Bulb Temperature (C)')
    st.plotly_chart(fig)



    
    # Add interactive FAQ section below the main content
    st.write("""
    ### Frequently Asked Questions (FAQ)

    """)
        # Define FAQ items as a dictionary with questions as keys and answers as values
    faq_items = {
    "What is wet bulb temperature?": "Wet bulb temperature is a measure of air temperature that takes into account the cooling effect of evaporation. It's an important metric for assessing heat stress and humidity levels.",
    "How is wet bulb temperature calculated?": "Wet bulb temperature is calculated using various meteorological parameters, including air temperature and humidity. A formula, such as the one implemented in this app, is used to derive the wet bulb temperature value.",
    "Why is wet bulb temperature important?": "Wet bulb temperature is important because it reflects the combined effects of temperature and humidity on human comfort and health. High wet bulb temperatures can indicate increased risk of heat-related illnesses.",
    "What are the health risks associated with high wet bulb temperatures?": "High wet bulb temperatures can lead to heat stress, heat exhaustion, and heatstroke, particularly in outdoor settings where individuals may be exposed to prolonged heat and humidity.",
    "How can I stay safe during periods of high wet bulb temperatures?": "To stay safe during periods of high wet bulb temperatures, it's essential to stay hydrated, seek shade or air-conditioned environments, wear light and breathable clothing, and avoid strenuous activities during the hottest parts of the day."
    }

    # Iterate over FAQ items and create expanders for each question-answer pair
    for question, answer in faq_items.items():
        with st.expander(question):
            st.write(answer)
    

def plot_map(cities):
    weather_data = {}

    for city in cities:
        temperature, humidity = get_weather_data(city)
        if temperature is not None and humidity is not None:
            wbt = calculate_wet_bulb_temperature(temperature, humidity)
            weather_data[city] = {'Temperature': temperature, 'Humidity': humidity, 'WBT': wbt}
        else:
            print(f"Unable to fetch weather data for {city}")

    # Check if any WBT value exceeds the threshold
    dangerous_cities = [city for city, data in weather_data.items() if data['WBT'] > 30]

    # If there are dangerous cities, display the message
    if dangerous_cities:
        st.markdown("<span style='color:red;'>Wet-bulb temperatures above 30 °C (86 °F) can be deadly outside. Avoid direct sunlight and drink plenty of water.</span>", unsafe_allow_html=True)

    # Extract cities and corresponding WBT values
    cities = list(weather_data.keys())
    wbt_values = [data['WBT'] for data in weather_data.values()]

    # Define threshold for safe and unsafe Wet Bulb Temperature (WBT)
    threshold_safe = 32
    threshold_unsafe = 35

    # Define colors for the color range
    color_range = [(0, 'green'), (0.5, 'yellow'), (1, 'red')]  # Green to Yellow to Red
    cmap_name = 'custom_cmap'
    custom_cmap = LinearSegmentedColormap.from_list(cmap_name, color_range)

    # Normalize the WBT values
    normalize = Normalize(vmin=min(wbt_values), vmax=max(wbt_values))

    # Create a color map scalar mappable
    color_mapper = ScalarMappable(norm=normalize, cmap=custom_cmap)

    # Create a list of colors based on WBT values using the color map
    colors = [color_mapper.to_rgba(wbt) for wbt in wbt_values]

    # Create scatter plot
    plt.figure(figsize=(10, 6))
    plt.scatter(cities, wbt_values, c=colors, s=100, alpha=0.7)

    # Add horizontal lines for critical thresholds
    plt.axhline(y=threshold_safe, color='red', linestyle='--', label='Critical Threshold (32°C)')
    plt.axhline(y=threshold_unsafe, color='orange', linestyle='--', label='Maximum Threshold (35°C)')

    # Add text annotations for each point
    for i, (city, wbt) in enumerate(zip(cities, wbt_values)):
        plt.text(i, wbt, f'{wbt:.1f}°C', ha='center', va='bottom', color='black')

    # Add labels and title
    plt.xlabel('City')
    plt.ylabel('Wet Bulb Temperature (°C)')
    plt.title('Wet Bulb Temperature for Coastal Cities in India')

    # Customize the legend
    plt.legend(loc='upper left')

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')

    # Display plot in Streamlit
    st.pyplot(plt)



def get_coordinates(city):
    coordinates = {
        'Mumbai': [19.0760, 72.8777],
        'Chennai': [13.0827, 80.2707],
        'Kolkata': [22.5726, 88.3639],
        'Goa': [15.2993, 74.1240],
        'Kochi': [9.9312, 76.2673],
        'Visakhapatnam': [17.6868, 83.2185],
        'Mangalore': [12.9141, 74.8560],
        'Pondicherry': [11.9139, 79.8145],
        'Kanyakumari': [8.0883, 77.5385],
        'Surat': [21.1702, 72.8311],
        'Karaikal': [10.9254, 79.8380],
        'Nagapattinam': [10.7660, 79.8447],
        'Alappuzha': [9.4981, 76.3388]
    }
    return coordinates[city]



# Run the app
if __name__ == "__main__":
    main()
