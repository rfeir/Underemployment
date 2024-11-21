# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 09:19:19 2024

@author: Ricky Feir
"""

###############################################################
########################## DASH APP ###########################
###############################################################

#%% TABLE MAP
# Make Currency format for Income Vars

import os
import geopandas as gpd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import dash_table
import pandas as pd

# Define the path to your folder with GeoJSON files
geojson_folder = 'map_dfs'

# Define list of industries for the dropdown
industries = [
    "Accommodation and Food Services", "Administrative and Support and Waste Management and Remediation Services", 
    "Agriculture, Forestry, Fishing and Hunting", "Arts, Entertainment, and Recreation", "Construction",
    "Educational Services", "Finance and Insurance", "Health Care and Social Assistance", "Information", 
    "Management of Companies and Enterprises", "Manufacturing", "Mining, Quarrying, and Oil and Gas Extraction", 
    "Other Services (except Public Administration)", "Professional, Scientific, and Technical Services", 
    "Public Administration", "Real Estate and Rental Leasing", "Retail Trade", "Transportation and Warehousing", 
    "Utilities", "Wholesale Trade"
]

# Dropdown options for Industry
industry_options = [{'label': ind, 'value': ind} for ind in industries]
industry_options.insert(0, {"label": "All", "value": "All"})  # Add "All" option

# Nativity options
nativity_options = [
    {"label": "All", "value": "All"},
    {"label": "Domestic", "value": "1"},
    {"label": "Foreign-Born", "value": "0"}
]

# Dash app layout
app = Dash(__name__, external_stylesheets=[dbc.themes.SIMPLEX])

# Define the wrap_text function to avoid cutting words
def wrap_text(text, length=25):
    """Wrap the text without cutting words."""
    words = text.split()  # Split the text into words
    lines = []
    current_line = ""

    for word in words:
        # If adding the word exceeds the length, start a new line
        if len(current_line + word) + 1 > length:
            lines.append(current_line)
            current_line = word  # Start a new line with the current word
        else:
            if current_line:
                current_line += " " + word  # Add the word to the current line
            else:
                current_line = word  # First word of the line

    if current_line:
        lines.append(current_line)  # Add the last line

    return '<br>'.join(lines)  # Join all lines with line breaks

app.layout = html.Div(
    style={"margin": "5% 5%"},  # Add margin around the entire page
    children=[
        html.H4('Underemployment by Industry and Nativity',
                style={"margin-bottom": "30px"}
        ),

        # Dropdown row
        dbc.Row([
            # Industry Dropdown
            dbc.Col([
                html.P("Select an Industry:"),
                dcc.Dropdown(
                    id='industry',
                    options=industry_options,
                    value='All',  # Default value
                    clearable=False
                ),
            ], width=8),  # Width 6 (half the row width)

            # Nativity Dropdown
            dbc.Col([
                html.P("Select Nativity:"),
                dcc.Dropdown(
                    id='nativity',
                    options=nativity_options,
                    value="All",  # Default value
                    clearable=False
                ),
            ], width=4),  # Width 6 (half the row width)
        ]),

        # Checklist for hover fields with custom styling for boxes
        dbc.Row([
            dbc.Col([
                html.P("Select Other Variables To Display While Hovering:", style={"margin-top": "30px"}),  # Added space before title
                dcc.Checklist(
                    id='hover-fields',
                    options=[
                        {'label': 'ID', 'value': 'GISMATCH_COMBINED'},
                        {'label': 'Ed Attained', 'value': 'Education Level'},
                        {'label': 'Ed Required', 'value': 'Required Education Level'},
                        {'label': 'Mean Wage', 'value': 'Mean Wage'},
                        {'label': 'Mean Other Income', 'value': 'Mean Other Income'},
                        {'label': 'Mean Age', 'value': 'Mean Age'},
                        {'label': 'Nativity %', 'value': 'Percent of Workforce'},
                        {'label': 'State', 'value': 'State'},
                        {'label': 'Counties', 'value': 'Counties'}
                    ],
                    value=['GISMATCH_COMBINED', 'Education Level', 'Required Education Level', 'Mean Wage', 'Mean Other Income', 'Mean Age', 'Percent of Workforce', 'State', 'Counties'],  # Default values
                    inline=True,  # Keep them inline
                    inputStyle={"margin-left": "20px", "margin-right": "5px", "margin-bottom": "15px"}  # Space between checkboxes
                )
            ], width=12),
        ]),

        # Message for update status
        html.Div(id='updating-note', style={'color': 'red', 'fontSize': '16px', 'margin-top': '20px', 'display': 'none'}),

        # Graph Output (within a loading indicator)
        dcc.Loading(
            id="loading-graph",
            type="default",  # Use a spinner while loading
            children=[dcc.Graph(id="graph")],
        ),

        # Data table
        html.Div(
            dash_table.DataTable(
                id='data-table',
                style_table={'height': '300px', 'overflowY': 'auto'},
                columns=[
                    {"name": 'ID', "id": 'GISMATCH_COMBINED', "hideable": True},
                    {"name": 'Underemployment Level', "id": 'Underemployment Level', "hideable": True},
                    {"name": 'Education Level', "id": 'Education Level', "hideable": True},
                    {"name": 'Required Education Level', "id": 'Required Education Level', "hideable": True},
                    {"name": 'Mean Wage', "id": 'Mean Wage', "hideable": True},
                    {"name": 'Mean Other Income', "id": 'Mean Other Income', "hideable": True},
                    {"name": 'Mean Age', "id": 'Mean Age', "hideable": True},
                    {"name": 'Nativity %', "id": 'Percent of Workforce', "hideable": True},
                    {"name": 'State', "id": 'State', "hideable": True},
                    {"name": 'Counties', "id": 'COUNTIES', "hideable": True}
                ],
                data=[],
                row_selectable="multi",
                selected_rows=[],
                style_cell={
                    'textAlign': 'center',
                    'font-family': 'Segoe UI',
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'COUNTIES'},
                        'textAlign': 'left',  # Left-align the 'Counties' column data
                        'whiteSpace': 'normal',  # Enable wrapping of content
                        'overflow': 'hidden',  # Prevent horizontal overflow
                    },
                ],
                style_header={
                    'fontWeight': 'bold',
                    'textAlign': 'center',  # Default header alignment
                    'whiteSpace': 'normal',  # Allow text wrapping
                    'wordBreak': 'break-word',  # Break long words
                    'height': 'auto',  # Adjust the height for the two-line headers
                    'minHeight': '50px',  # Set minimum height for headers to support two rows
                },
                style_header_conditional=[
                    {
                        'if': {'column_id': 'COUNTIES'},
                        'textAlign': 'center',  # Left-align the 'Counties' header
                    },
                ],
                style_filter={
                    'textAlign': 'center',  # Center the filter fields by default
                    'padding': '4px',  # Reduce padding for compactness
                    'lineHeight': '1',  # Adjust line height
                    'font-family': 'Segoe UI',
                },
                filter_action="native",
                filter_options={"case": "insensitive", "placeholder_text": "Filter column..."},
                sort_action="native",
            ),
            style={"margin-top": "30px"}
        ),
    ]
)

@app.callback(
    [Output("graph", "figure"), Output('data-table', 'data'), Output('updating-note', 'style')],
    [Input("industry", "value"), Input("nativity", "value"), Input('hover-fields', 'value'), Input('data-table', 'selected_rows')]
)
def update_graph_and_table(industry, nativity, hover_fields, selected_rows):
    # Show the updating message while loading
    updating_style = {'color': 'red', 'fontSize': '16px', 'margin-top': '20px'}

    # Build the filename based on industry and nativity selection
    if industry == "All":
        industry_file = "All"
    else:
        industry_file = industry

    if nativity == "All":
        nativity_file = "All"
    else:
        nativity_file = nativity
    
    # Construct the GeoJSON filename
    geojson_filename = f"{industry_file} {nativity_file}.geojson"
    geojson_file_path = os.path.join(geojson_folder, geojson_filename)
    
    # Check if the file exists
    if not os.path.exists(geojson_file_path):
        return (
            {'data': [], 'layout': go.Layout(title=f"File '{geojson_filename}' not found!", geo=dict(showland=True))},
            [],
            {'display': 'none'}  # Hide the updating note if no file is found
        )

    # Load GeoJSON file
    gdf = gpd.read_file(geojson_file_path)

    # Ensure the required columns are present
    required_columns = ['Underemployment Level', 'Mean Wage', 'Mean Age', 'Percent of Workforce']
    missing_cols = [col for col in required_columns if col not in gdf.columns]
    if missing_cols:
        return (
            {'data': [], 'layout': go.Layout(title="Missing Data!", geo=dict(showland=True))},
            [],
            updating_style  # Show the "Updating" note
        )

    # Apply wrap_text to the counties column
    gdf['Wrapped Counties'] = gdf['COUNTIES'].apply(wrap_text)

    # Round the columns as specified
    gdf['Underemployment Level'] = gdf['Underemployment Level'].round(3)
    gdf['Education Level'] = gdf['Education Level'].round(2)
    gdf['Required Education Level'] = gdf['Required Education Level'].round(2)
    gdf['Mean Wage'] = gdf['Mean Wage'].round(0)
    gdf['Mean Other Income'] = gdf['Mean Other Income'].round(0)
    gdf['Mean Age'] = gdf['Mean Age'].round(1)
    gdf['Percent of Workforce'] = (gdf['Percent of Workforce'] * 100).round(1)

    # Prepare data for table
    table_data = gdf[['GISMATCH_COMBINED', 'Underemployment Level', 'Education Level', 'Required Education Level', 'Mean Wage', 'Mean Other Income', 'Mean Age', 'Percent of Workforce', 'State', 'COUNTIES']].to_dict('records')

    # Define the color scale
    colorscale = [
        [0/14, "#F4F6DB"],
        [1/14, "#DFEEB4"],
        [2/14, "#C4F08F"],
        [3/14, "#A8EA81"],
        [4/14, "#8DE07E"],
        [5/14, "#73D67E"],
        [6/14, "#57CD82"],
        [7/14, "#3BC38A"],
        [8/14, "#21B697"],
        [9/14, "#0E9FA2"],
        [10/14, "#0580A1"],
        [11/14, "#016092"],
        [12/14, "#01407B"],
        [13/14, "#02215F"],
        [14/14, "#030240"],
    ]

    # Prepare hover template dynamically based on selected fields
    hovertemplate = "<b>Underemployment Level: %{z:.2f}</b><br>"
    
    # Add custom fields to the hovertemplate
    if 'GISMATCH_COMBINED' in hover_fields:
        hovertemplate += "ID: %{customdata[0]}<br>"
    if 'Education Level' in hover_fields:
        hovertemplate += "Education Level: %{customdata[1]}<br>"
    if 'Required Education Level' in hover_fields:
        hovertemplate += "Required Education Level: %{customdata[2]}<br>"
    if 'Mean Wage' in hover_fields:
        hovertemplate += "Mean Wage: $%{customdata[3]:,.0f}<br>"
    if 'Mean Other Income' in hover_fields:
        hovertemplate += "Mean Other Income: $%{customdata[4]:,.0f}<br>"
    if 'Mean Age' in hover_fields:
        hovertemplate += "Mean Age: %{customdata[5]:,.1f}<br>"
    if 'Percent of Workforce' in hover_fields:
        hovertemplate += "Nativity: %{customdata[6]}%<br>"
    if 'State' in hover_fields:
        hovertemplate += "State: %{customdata[7]}<br>"
    if 'Counties' in hover_fields:
        hovertemplate += "Counties: %{customdata[8]}<br>"
    
    # Add '%{text}' to remove the default trace metadata
    hovertemplate += "<extra></extra>"  # This explicitly removes trace metadata
    
    # Highlight the selected rows by changing border width
    border_width = [2 if i in selected_rows else 0 for i in range(len(gdf))]
    
    # Create the choropleth map with a dynamic colorbar position
    fig = go.Figure(go.Choropleth(
        geojson=gdf.geometry.__geo_interface__,
        locations=gdf.index,
        z=gdf['Underemployment Level'],
        colorscale=colorscale,
        zmin=0,
        zmax=2,
        colorbar=dict(
            title="Underemployment Level",
            x=1,  # Keep it close to the right edge of the map
            y=0.5,  # Keep it vertically centered with the map
            xanchor='left',  # Left-align the colorbar with the x position
            yanchor='middle',  # Vertically center it
            thickness=20,  # Thickness of the colorbar
            len=0.65  # Length of the colorbar relative to the map height
        ),
        hovertemplate=hovertemplate,  # Hover data template
        customdata=gdf[['GISMATCH_COMBINED', 'Education Level', 'Required Education Level', 'Mean Wage', 'Mean Other Income', 'Mean Age', 'Percent of Workforce', 'State', 'Wrapped Counties']].values
    ))
    
    # Update the map's layout to maintain a flexible, responsive design
    fig.update_geos(
        visible=False, resolution=110, scope="usa",
        showcountries=True, countrycolor="rgba(255, 255, 255, 0)",
        showsubunits=True, subunitcolor="#C2C2C2"
    )
    
    # Update layout with flexible spacing for the map and colorbar
    fig.update_layout(
        margin=dict(t=30, b=0, l=0, r=0),  # Reduce margins to keep elements tight
        geo=dict(
            showland=False,
            landcolor="white",
            showlakes=True,
            lakecolor="white",
        ),
    )
    
    # Apply adjustments to the traces for cleaner visual appearance
    fig.update_traces(
        marker_line_width=border_width,
        marker_line_color="#ff69b4",
        hoverlabel=dict(
            bgcolor="rgba(255, 255, 255, 0.8)",
            font=dict(color="black")
        )
    )
    
    return fig, table_data, {'display': 'none'}  # Hide the updating note after update


if __name__ == '__main__':
    app.run_server(debug=True)



