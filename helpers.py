import pandas as pd
import duckdb
import plotly.express as px
import geopandas as gpd
from sklearn.ensemble import RandomForestClassifier

def get_loc_names(location: str, connection) -> pd.DataFrame:
    """
    Retrieve distinct property locations matching the input address from the Parquet file.
    """
    prop_path = "res_prop.parquet"
    loc_query = f"""
    SELECT DISTINCT location
    FROM '{prop_path}'
    WHERE LOWER(location) LIKE '%{location.lower()}%'
    ORDER BY location ASC
    """
    res = connection.execute(loc_query).fetchdf()
    return res

def get_prop_assessment(parcel: str, connection) -> pd.DataFrame:
    """
    Retrieve property assessment details based on the parcel number.
    """
    assessment_path = "assessments.parquet"
    assessment_query = f"""
    SELECT parcel_number, year, market_value
    FROM '{assessment_path}'
    WHERE parcel_number = '{parcel}'
    """
    res = connection.execute(assessment_query).fetchdf()
    return res

def get_prop_assessment_plot(data: pd.DataFrame, location: str):
    """
    Create a line plot of property assessment values over time using Plotly.
    """
    fig = px.line(data, x='year', y='market_value', title=f'Assessment Over Time - {location}',
                  labels={'year': 'Year', 'market_value': 'Market Value ($)'})
    fig.update_traces(mode='lines+markers', marker=dict(color='blue'))
    fig.update_layout(yaxis=dict(title='Assessed Value ($)'))
    return fig

def get_index_property(location: str, connection) -> pd.DataFrame:
    """
    Retrieve property details for the input location.
    """
    prop_path = "res_prop.parquet"
    prop_query = f"""
    SELECT *
    FROM '{prop_path}'
    WHERE location = '{location}'
    QUALIFY parcel_number = MIN(parcel_number) OVER (PARTITION BY location ORDER BY location)
    """
    res = connection.execute(prop_query).fetchdf()
    return res

def get_match_universe(index_property: pd.DataFrame, matching_tracts: list, connection) -> pd.DataFrame:
    """
    Retrieve potential matching properties from the same or adjacent census tracts.
    Use `index_property` to filter the properties based on census tract and exclude the index property itself.
    Return an empty DataFrame if no matching tracts are found.
    """
    if not matching_tracts or index_property is None or index_property.empty:
        return pd.DataFrame()  # Return empty DataFrame to avoid executing an invalid query

    prop_path = "res_prop.parquet"
    matching_tracts_str = ", ".join([f"'{tract}'" for tract in matching_tracts])

    index_parcel_number = index_property['parcel_number'].values[0]

    prop_query = f"""
    SELECT *
    FROM '{prop_path}'
    WHERE census_tract IN ({matching_tracts_str})
    AND parcel_number <> '{index_parcel_number}'  -- Exclude the index property itself
    QUALIFY parcel_number = MIN(parcel_number) OVER (PARTITION BY location ORDER BY location)
    """

    res = connection.execute(prop_query).fetchdf()
    return res


def find_matching_properties(match_universe: pd.DataFrame, index_property: pd.DataFrame, n_matches: int = 25) -> pd.DataFrame:
    """
    Find the best matching properties using a Random Forest classifier.
    """
    property_prep = match_universe.copy()
    property_prep['match_ind'] = property_prep['parcel_number'].apply(lambda x: 1 if x == index_property['parcel_number'].values[0] else 0)
    property_prep.dropna(inplace=True)

    features = [
        "exterior_condition", "interior_condition", "number_of_bedrooms",
        "number_stories", "quality_grade", "total_area", "total_livable_area",
        "view_type", "year_built"
    ]
    X = property_prep[features]
    y = property_prep['match_ind']

    model = RandomForestClassifier(n_estimators=100, random_state=354)
    model.fit(X, y)

    property_prep['distance'] = model.predict_proba(X)[:, 1]
    property_prep.sort_values(by='distance', ascending=False, inplace=True)

    top_matches = property_prep.head(n_matches).copy()
    top_matches['type'] = top_matches['match_ind'].apply(lambda x: 'Input' if x == 1 else 'Match')
    top_matches['match_num'] = range(len(top_matches))

    return top_matches
