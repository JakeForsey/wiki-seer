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
    time_series_forecast = response.json()
    time_series = time_series_forecast["time_series"]
    forecast = time_series_forecast["forecast"]

    traces = [
        # Historic data
        {
            "x": [
                str(date.fromisoformat(time_series["start_date"]) + timedelta(days=i))
                for i in range(len(time_series["page_views"]))
            ],
            "y": time_series["page_views"], "type": "scatter"
         },
        # Median forecast
        {
            "x": [
                str(date.fromisoformat(forecast["start_date"]) + timedelta(days=i))
                for i in range(len(forecast["median"]))
            ],
            "y": forecast["median"],
            "type": "scatter",
            "line": {"color": "grey"}
        },
        # Area quantile forecast
        {
            "x": [
                str(date.fromisoformat(forecast["start_date"]) + timedelta(days=i))
                for i in range(len(forecast["lower"]))
            ] + [
                str(date.fromisoformat(forecast["start_date"]) + timedelta(days=i))
                for i in range(len(forecast["upper"]))
            ][::-1],
            "y": forecast["lower"] + forecast["upper"][::-1],
            "type": "scatter",
            "fill": "toself",
            "line": {"color": "rgba(0,0,0,0)"},
            "fillcolor": "rgba(50,50,50,0.2)",
        },
    ]
    layout = {
        'title': None,
        'xaxis': {'title': 'Date'},
        'yaxis': {'title': 'Page views'},
        "showlegend": False
    }
    return {'data': traces, 'layout': layout, "showlegend": False}



if __name__ == '__main__':
    app.run_server(port=8001, host="0.0.0.0")
