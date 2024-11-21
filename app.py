import os
import dash
import dash_bootstrap_components as dbc
import dash_table
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State

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

industry_options = [{'label': ind, 'value': ind} for ind in industries]
industry_options.insert(0, {"label": "All", "value": "All"})  # Add "All" option

nativity_options = [
    {"label": "All", "value": "All"},
    {"label": "Domestic", "value": "1"},
    {"label": "Foreign-Born", "value": "0"}
]

# Dash app layout
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SIMPLEX])

app.layout = html.Div(
    style={"margin": "5% 5%"}, 
    children=[
        html.H4('Underemployment by Industry and Nativity',
                style={"margin-bottom": "30px"}),

        dbc.Row([
            # Industry Dropdown
            dbc.Col([
                html.P("Select an Industry:"),
                dcc.Dropdown(
                    id='industry',
                    options=industry_options,
                    value='All',  
                    clearable=False
                ),
            ], width=8),  

            # Nativity Dropdown
            dbc.Col([
                html.P("Select Nativity:"),
                dcc.Dropdown(
                    id='nativity',
                    options=nativity_options,
                    value="All",  
                    clearable=False
                ),
            ], width=4),  
        ]),

        # Checklist for hover fields with custom styling for boxes
        dbc.Row([
            dbc.Col([
                html.P("Select Other Variables To Display While Hovering:", style={"margin-top": "30px"}),  
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
                    value=['GISMATCH_COMBINED', 'Education Level', 'Required Education Level', 'Mean Wage', 'Mean Other Income', 'Mean Age', 'Percent of Workforce', 'State', 'Counties'],  
                    inline=True,  
                    inputStyle={"margin-left": "20px", "margin-right": "5px", "margin-bottom": "15px"}  
                )
            ], width=12),
        ]),

        # Message for update status
        html.Div(id='updating-note', style={'color': 'red', 'fontSize': '16px', 'margin-top': '20px', 'display': 'none'}),

        # Graph Output (within a loading indicator)
        dcc.Loading(
            id="loading-graph",
            type="default",  
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
                        'textAlign': 'left',  
                        'whiteSpace': 'normal',  
                        'overflow': 'hidden',  
                    },
                ],
                style_header={
                    'fontWeight': 'bold',
                    'textAlign': 'center',  
                    'whiteSpace': 'normal',  
                    'wordBreak': 'break-word',  
                    'height': 'auto',  
                    'minHeight': '50px',  
                },
                style_header_conditional=[
                    {
                        'if': {'column_id': 'COUNTIES'},
                        'textAlign': 'center',  
                    },
                ],
                style_filter={
                    'textAlign': 'center',  
                    'padding': '4px',  
                    'lineHeight': '1',  
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

# JavaScript Callback
app.clientside_callback(
    """
    function(industry, nativity, hover_fields, selected_rows) {
        // Construct the GeoJSON filename
        let industryFile = industry === "All" ? "All" : industry;
        let nativityFile = nativity === "All" ? "All" : nativity;
        let geojsonFilename = `${industryFile} ${nativityFile}.geojson`;
        
        // Fetch GeoJSON data
        return fetch(`/assets/${geojsonFilename}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`File '${geojsonFilename}' not found!`);
                }
                return response.json();
            })
            .then(data => {
                // Handle the data processing and chart/table updates
                let gdf = data.features;

                // Ensure the required columns exist
                let requiredColumns = ['Underemployment Level', 'Mean Wage', 'Mean Age', 'Percent of Workforce'];
                let missingCols = requiredColumns.filter(col => !gdf[0].properties[col]);

                if (missingCols.length > 0) {
                    return {
                        figure: {
                            data: [],
                            layout: { title: "Missing Data!", geo: { showland: true } }
                        },
                        tableData: [],
                        updatingNoteStyle: { display: 'none' }
                    };
                }

                // Process data (similar to Python logic)
                let tableData = gdf.map(feature => {
                    return {
                        'GISMATCH_COMBINED': feature.properties.GISMATCH_COMBINED,
                        'Underemployment Level': feature.properties['Underemployment Level'],
                        'Education Level': feature.properties['Education Level'],
                        'Required Education Level': feature.properties['Required Education Level'],
                        'Mean Wage': feature.properties['Mean Wage'],
                        'Mean Other Income': feature.properties['Mean Other Income'],
                        'Mean Age': feature.properties['Mean Age'],
                        'Percent of Workforce': feature.properties['Percent of Workforce'],
                        'State': feature.properties['State'],
                        'COUNTIES': feature.properties['COUNTIES']
                    };
                });

                // Create hovertemplate dynamically
                let hovertemplate = "<b>Underemployment Level: %{z:.2f}</b><br>";
                hover_fields.forEach(field => {
                    hovertemplate += `${field}: %{customdata[${hover_fields.indexOf(field)}]}<br>`;
                });
                hovertemplate += "<extra></extra>";

                // Create figure (choropleth)
                let figure = {
                    data: [{
                        type: "choropleth",
                        geojson: data,
                        locations: gdf.map(d => d.properties.GISMATCH_COMBINED),
                        z: gdf.map(d => d.properties['Underemployment Level']),
                        hovertemplate: hovertemplate,
                        colorscale: "Viridis",
                        colorbar: { title: 'Underemployment Level' }
                    }],
                    layout: {
                        geo: {
                            center: { lat: 39.8283, lon: -98.5795 }, 
                            projection: { type: 'albers usa' }
                        },
                        title: 'Underemployment by Industry and Nativity',
                    }
                };

                return {
                    figure: figure,
                    tableData: tableData,
                    updatingNoteStyle: { display: 'none' }
                };
            })
            .catch(error => {
                return {
                    figure: {
                        data: [],
                        layout: { title: error.message, geo: { showland: true } }
                    },
                    tableData: [],
                    updatingNoteStyle: { display: 'none' }
                };
            });
    }
    """,
    Output("graph", "figure"),
    Output("data-table", "data"),
    Output("updating-note", "style"),
    Input("industry", "value"),
    Input("nativity", "value"),
    Input("hover-fields", "value"),
    State("data-table", "selected_rows")
)

if __name__ == '__main__':
    app.run_server(debug=True)
