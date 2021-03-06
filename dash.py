import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px

import pandas as pd


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'] # stylesheet

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True) # used to run the app, flask under the hood so __name__

# html.Div stores all layout components
app.layout = html.Div([ # this code section taken from Dash docs https://dash.plotly.com/dash-core-components/upload
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files') # select component
        ]), # upload component
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        }, # styling it
        # Allow multiple files to be uploaded
        multiple=True
    ),
    # two empty div for return the empty table from callback below
    html.Div(id='output-div'),  # tied to make_graphs, the graph returned by make_graphs is returned into this div
    html.Div(id='output-datatable'), # tied to update_output, which returns children (the data table at the bottom of page)
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    # returns a big html div
    return html.Div([
        html.H5(filename), # name of excel sheet
        html.H6(datetime.datetime.fromtimestamp(date)), # date of upload component (last modified)
        html.P("Inset X axis data"),
        dcc.Dropdown(id='xaxis-data',
                     options=[{'label':x, 'value':x} for x in df.columns]), # drop down component, with each of the header columns
        html.P("Inset Y axis data"),
        dcc.Dropdown(id='yaxis-data',
                     options=[{'label':x, 'value':x} for x in df.columns]),
        html.Button(id="submit-button", children="Create Graph"), # a buttom
        html.Hr(), # horizontal line

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            page_size=15 # put into a datatable with 15 rows per page limit
        ),
        dcc.Store(id='stored-data', data=df.to_dict('records')),  # store the dataframe in the users broweser, dont do too big

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

# use callback to make it interactive
@app.callback(Output('output-datatable', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    # if excel sheet not empty
    if list_of_contents is not None:
        # create a list, zip three lists together, parse contents
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


@app.callback(Output('output-div', 'children'), # does not trigger the state unless the buttom is clicked
              Input('submit-button','n_clicks'),
              State('stored-data','data'),
              State('xaxis-data','value'),
              State('yaxis-data', 'value'))
def make_graphs(n, data, x_data, y_data): #(n_clicks, stored data, xaxis, yaxis)
    # if not clicked, dont update anything
    if n is None:
        return dash.no_update
    else:
        bar_fig = px.bar(data, x=x_data, y=y_data)
        # print(data)
        return dcc.Graph(figure=bar_fig)

if __name__ == '__main__':
    app.run_server(debug=True)
