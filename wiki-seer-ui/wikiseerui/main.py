from datetime import date, timedelta
from typing import Literal

from dash import dcc
from dash import html
from dash import Output, Input, Dash, no_update

import requests


app = Dash()
app.layout = html.Div([
    dcc.Dropdown(
        id="page-dropdown",
        options=[
            {"label": title, "value": title}
            for title in requests.get("http://wikiseerapi:8000/page").json()
        ],
        style={'font-family': 'sans-serif'}
    ),
    dcc.Graph(id='timeseries-graph')
])


@app.server.route("/ruok")
def ruok() -> Literal["OK"]:
  return "OK"


@app.callback(Output('timeseries-graph', 'figure'), [Input('page-dropdown', 'value')])
def update_graph(title: str):
    if title is None:
        return no_update

    response = requests.get(f"http://wikiseerapi:8000/page/{title}/timeseries")
    response.raise_for_status()
    timeseries = response.json()
    
    traces = [
        {
            "x": [
                str(date.fromisoformat(timeseries["start_date"]) + timedelta(days=i))
                for i in range(len(timeseries["page_views"]))
            ],
            "y": timeseries["page_views"], "type": "scatter"
         }
    ]
    layout = {
        'title': f'Time series data for {title}',
        'xaxis': {'title': 'Date'},
        'yaxis': {'title': 'Page views'}
    }
    return {'data': traces, 'layout': layout}


if __name__ == '__main__':
    app.run_server(port=8001, host="0.0.0.0")
