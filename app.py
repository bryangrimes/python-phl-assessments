# app.py

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import duckdb
from helpers import get_loc_names, get_index_property, get_match_universe, find_matching_properties  # Import functions from helpers

con = duckdb.connect(database=':memory:')  # Replace with your actual database connection

st.title("Philly Property Assessment Explorer")

st.sidebar.header("Property Lookup")
address_input = st.sidebar.text_input("Enter Address", placeholder="ex: 123 Market St")

if st.sidebar.button("Find Matches"):
    if address_input:
        address_result = get_loc_names(address_input, con)

        if not address_result.empty:
            st.success(f"Address found: {address_input}")

            index_property = get_index_property(address_input, con)

            # if index_property has census_tract column and it's not empty
            if 'census_tract' in index_property.columns and not index_property.empty:
                # list of matching tracts
                matching_tracts = index_property['census_tract'].tolist()

                if matching_tracts:
                    # the universe of matching properties based on the index property
                    match_universe = get_match_universe(index_property, matching_tracts, con)

                    if not match_universe.empty:
                        # Find matching properties based on the universe
                        matches = find_matching_properties(match_universe, index_property)  # Pass index_property

                        # matches
                        st.subheader("Matched Properties")
                        st.dataframe(matches)

                        # map it
                        st.subheader("Map of Matched Properties")
                        map_center = [matches['latitude'].mean(), matches['longitude'].mean()]
                        m = folium.Map(location=map_center, zoom_start=13)
                        for _, row in matches.iterrows():
                            folium.Marker(
                                location=[row['latitude'], row['longitude']],
                                popup=f"{row['location']} - ${row['market_value']:,.0f}",
                                icon=folium.Icon(color='blue')
                            ).add_to(m)
                        st_folium(m, width=700, height=500)

                        # plotly for display
                        st.subheader("Assessment Comparison")
                        fig = px.bar(matches, x='location', y='market_value', title='Assessment Comparison')
                        st.plotly_chart(fig)
                    else:
                        st.warning("No matching properties found in the specified tracts.")
                else:
                    st.warning("No census tracts found for the given address.")
            else:
                st.warning("No census tracts available for the selected address.")
        else:
            st.warning("Address not found. Please enter a valid address.")
    else:
        st.warning("Please enter an address to search for matches.")
