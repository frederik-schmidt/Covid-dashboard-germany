import json
import requests
import datetime
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go


def request_data(url: str, where_clause: str = "1=1") -> dict:
    """
    Requests data from the ArcGIS api and retuens the response  in JSON format.
    """
    params = {
        "referer": "https://www.mywebapp.com",
        "user-agent": "python-requests/2.9.1",
        "where": where_clause,
        "outFields": "*",  # all fields
        "returnGeometry": True,  # no geometries
        "f": "json",  # json format
        "cacheHint": True,  # request access via CDN
    }
    r = requests.get(url=url, params=params)
    result = json.loads(r.text)
    return result


def convert_millisecond_date(x: int, date_format: str = "%Y-%m-%d") -> str:
    """
    Converts a date in milliseconds to a string date.

    :param x: time in milliseconds
    :param date_format: date format to return
    :return: time in date format
    """
    return time.strftime(date_format, time.gmtime(x / 1000.0))


def return_figures() -> list:
    """
    Creates five plotly visualizations.

    :return: list containing five plotly visualizations
    """
    # settings
    colors = px.colors.sequential.Blues

    # mapping with id and name if state/country
    url_mapping = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/rki_admunit_v/FeatureServer/0/query?"
    result_mapping = request_data(url_mapping)
    df_mapping = pd.DataFrame([i["attributes"] for i in result_mapping["features"]])
    df_mapping = df_mapping[["AdmUnitId", "Name"]]

    # plot 1
    url_history = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/rki_history_blbrdv/FeatureServer/0/query?"
    last_60_days = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime(
        "%Y-%m-%d"
    )

    where_clause = f"Datum > DATE '{last_60_days}' and BundeslandId = 0"
    result_history = request_data(url_history, where_clause=where_clause)

    df_history = pd.DataFrame([i["attributes"] for i in result_history["features"]])
    df_history["Datum"] = df_history["Datum"].apply(
        lambda x: convert_millisecond_date(x)
    )
    df_history = df_history.sort_values(by="Datum")

    plot_1 = [
        go.Scatter(
            x=df_history["Datum"],
            y=df_history["AnzFallMeldung"],
            mode="lines",
        )
    ]

    layout_1 = dict(
        title=dict(
            text="Evolution of COVID-19 cases <br> (60 day period)",
            y=0.95,
        ),
        xaxis=dict(
            title="Date",
            automargin=True,
        ),
        yaxis=dict(title="COVID-19 cases"),
    )

    # plot 2
    url_state = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/rki_key_data_v/FeatureServer/0/query?"
    result_state = request_data(url_state)

    df_key_data = pd.DataFrame([i["attributes"] for i in result_state["features"]])

    mask = (df_key_data["AdmUnitId"] >= 1) & (df_key_data["AdmUnitId"] <= 16)
    df_state = df_key_data[mask].sort_values(by="Inz7T", ascending=False)
    df_state = pd.merge(df_state, df_mapping, how="inner", on="AdmUnitId")

    plot_2 = [
        go.Bar(
            x=df_state["Name"],
            y=df_state["Inz7T"],
        )
    ]

    layout_2 = dict(
        title=dict(
            text="7-day incidence by state <br> (nationwide)",
            y=0.95,
        ),
        xaxis=dict(
            title="State",
            automargin=True,
        ),
        yaxis=dict(title="7-day incidence"),
    )

    # plot 3
    mask = df_key_data["AdmUnitId"] > 16
    df_county = df_key_data[mask].sort_values(by="Inz7T", ascending=False)[:10]
    df_county = pd.merge(df_county, df_mapping, how="inner", on="AdmUnitId")

    plot_3 = [
        go.Bar(
            x=df_county["Name"],
            y=df_county["Inz7T"],
        )
    ]

    layout_3 = dict(
        title=dict(
            text="Counties with highest 7-day incidence <br> (nationwide)",
            y=0.95,
        ),
        xaxis=dict(
            title="County",
            automargin=True,
        ),
        yaxis=dict(title="Local 7-day incidence"),
    )

    # plot 4
    url_age_sex = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/rki_altersgruppen_v/FeatureServer/0/query?"
    result_age_sex = request_data(url_age_sex, where_clause="BundeslandId = 0")

    df_age_sex = pd.DataFrame([i["attributes"] for i in result_age_sex["features"]])

    df_age = (
        df_age_sex.groupby(["Altersgruppe"])["AnzFallM"].sum()
        + df_age_sex.groupby(["Altersgruppe"])["AnzFallW"].sum()
    )

    plot_4 = [
        go.Pie(
            labels=df_age.index,
            textinfo="label+percent",
            values=df_age.values,
            showlegend=True,
            marker=dict(
                colors=[
                    colors[0],
                    colors[1],
                    colors[4],
                    colors[6],
                    colors[7],
                    colors[8],
                ]
            ),
            sort=False,
        )
    ]

    layout_4 = dict(
        title=dict(
            text="COVID-19 cases by age group <br> (all time)",
            y=0.95,
        ),
        legend=dict(
            x=1,
            y=-0.2,
        ),
    )

    # plot 5
    values = [df_age_sex["AnzFallW"].sum(), df_age_sex["AnzFallM"].sum()]
    labels = ["Female", "Male"]

    plot_5 = [
        go.Pie(
            labels=labels,
            textinfo="label+percent",
            values=values,
            showlegend=True,
            marker=dict(colors=[colors[4], colors[8]]),
            sort=False,
        )
    ]

    layout_5 = dict(
        title=dict(
            text="COVID-19 cases by sex <br> (all time)",
        )
    )

    # append all charts to the figures list
    figures = [
        dict(data=plot_1, layout=layout_1),
        dict(data=plot_2, layout=layout_2),
        dict(data=plot_3, layout=layout_3),
        dict(data=plot_4, layout=layout_4),
        dict(data=plot_5, layout=layout_5),
    ]

    return figures
