import streamlit as st
import openrouteservice
from shapely.geometry import Point, LineString
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import pandas as pd
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages

API_KEY = '5b3ce3597851110001cf62483c9fa348736d4315a694410fd874e918'
client = openrouteservice.Client(key=API_KEY)

def get_drive_time_and_route(origin, destination):
    try:
        route = client.directions(
            coordinates=[origin, destination],
            profile='driving-car',
            format='geojson'
        )
        duration = route['features'][0]['properties']['segments'][0]['duration']
        geometry = route['features'][0]['geometry']
        return duration, geometry
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None

def main():
    st.title('Multiple Drive Time Calculator')

    option = st.radio("Choose input method", ("Manual Input", "Upload Excel File"))

    if option == "Manual Input":
        num_pairs = st.sidebar.number_input("Number of Origin-Destination Pairs", min_value=1, max_value=10, value=1)
        pairs = []

        for i in range(num_pairs):
            st.sidebar.header(f'Input Coordinates for Pair {i+1}')
            origin_lat = st.sidebar.number_input(f"Origin {i+1} Latitude", min_value=-90.0, max_value=90.0, value=25.003067569091343)
            origin_lon = st.sidebar.number_input(f"Origin {i+1} Longitude", min_value=-180.0, max_value=180.0, value=55.16747261201182)
            dest_lat = st.sidebar.number_input(f"Destination {i+1} Latitude", min_value=-90.0, max_value=90.0, value=25.25714576061916)
            dest_lon = st.sidebar.number_input(f"Destination {i+1} Longitude", min_value=-180.0, max_value=180.0, value=55.29771919667428)
            pairs.append(((origin_lat, origin_lon), (dest_lat, dest_lon)))

        if st.sidebar.button('Calculate Drive Times'):
            all_durations = []
            all_geometries = []
            table_data = []

            for i, ((origin_lat, origin_lon), (dest_lat, dest_lon)) in enumerate(pairs):
                origin = [origin_lon, origin_lat]
                destination = [dest_lon, dest_lat]
                duration, geometry = get_drive_time_and_route(origin, destination)
                if duration and geometry:
                    drive_time = duration / 60
                    table_data.append({
                        'Pair': f'Pair {i+1}',
                        'Origin': f'({origin_lat}, {origin_lon})',
                        'Destination': f'({dest_lat}, {dest_lon})',
                        'Drive Time (minutes)': f'{drive_time:.2f}'
                    })
                    st.write(f"Drive time for Pair {i+1} is approximately {drive_time:.2f} minutes.")
                    all_durations.append(duration)
                    all_geometries.append((geometry, origin, destination))

            if table_data:
                df_results = pd.DataFrame(table_data)
                st.write(df_results)

                fig, ax = plt.subplots(figsize=(10, 10))
                for geometry, origin, destination in all_geometries:
                    line = LineString(geometry['coordinates'])
                    gdf_route = gpd.GeoDataFrame(geometry=[line], crs='EPSG:4326')
                    gdf_points = gpd.GeoDataFrame(geometry=[Point(origin), Point(destination)], crs='EPSG:4326')
                    gdf_route.plot(ax=ax, alpha=0.5, edgecolor='k')
                    gdf_points.plot(ax=ax, color='red', markersize=100)

                ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, crs='EPSG:4326')
                ax.set_title('Drive Routes')
                ax.set_xlabel('Longitude')
                ax.set_ylabel('Latitude')

                st.pyplot(fig)

                pdf_buffer = BytesIO()
                with PdfPages(pdf_buffer) as pdf:
                    pdf.savefig(fig)
               
                st.download_button(
                    label="Download map as PDF",
                    data=pdf_buffer.getvalue(),
                    file_name="drive_routes.pdf",
                    mime="application/pdf"
                )

    elif option == "Upload Excel File":
        uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
        if uploaded_file:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            st.write(df)

            all_durations = []
            all_geometries = []
            table_data = []

            for index, row in df.iterrows():
                origin = [row['Origin_Lon'], row['Origin_Lat']]
                destination = [row['Destination_Lon'], row['Destination_Lat']]
                duration, geometry = get_drive_time_and_route(origin, destination)
                if duration and geometry:
                    drive_time = duration / 60
                    table_data.append({
                        'Origin': row['Origin'],
                        'Destination': row['Destination'],
                        'Drive Time (minutes)': f'{drive_time:.2f}'
                    })
                    st.write(f"Drive time for Origin {row['Origin']} to Destination {row['Destination']} is approximately {drive_time:.2f} minutes.")
                    all_durations.append(duration)
                    all_geometries.append((geometry, origin, destination))

            if table_data:
                df_results = pd.DataFrame(table_data)
                st.write(df_results)

                fig, ax = plt.subplots(figsize=(10, 10))
                for geometry, origin, destination in all_geometries:
                    line = LineString(geometry['coordinates'])
                    gdf_route = gpd.GeoDataFrame(geometry=[line], crs='EPSG:4326')
                    gdf_points = gpd.GeoDataFrame(geometry=[Point(origin), Point(destination)], crs='EPSG:4326')
                    gdf_route.plot(ax=ax, alpha=0.5, edgecolor='k')
                    gdf_points.plot(ax=ax, color='red', markersize=100)

                ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, crs='EPSG:4326')
                ax.set_title('Drive Routes')
                ax.set_xlabel('Longitude')
                ax.set_ylabel('Latitude')

                st.pyplot(fig)

                pdf_buffer = BytesIO()
                with PdfPages(pdf_buffer) as pdf:
                    pdf.savefig(fig)
               
                st.download_button(
                    label="Download map as PDF",
                    data=pdf_buffer.getvalue(),
                    file_name="drive_routes.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
