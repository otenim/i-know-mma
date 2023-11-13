import pandas as pd
import click
import json
from sklearn.preprocessing import LabelEncoder
from scraper.spiders.constants import *


@click.command()
@click.argument(
    "jsonfile", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
def main(jsonfile: str):
    # Load json file
    jsondata = None
    with open(jsonfile) as fp:
        jsondata = json.load(fp)

    # Load dataframe of fighter data
    df_fighters = pd.json_normalize(jsondata).drop(["results"], axis="columns")
    df_fighters.info(verbose=True, show_counts=True)

    # Load dataframe of result data
    df_results = pd.json_normalize(jsondata, record_path="results", meta=["id"])
    df_results.info(verbose=True, show_counts=True)

    # Merge fighters & results
    df = pd.merge(df_fighters, df_results, on="id").drop(
        [
            "url",
            "name",
            "nickname",
            "last_weigh_in",
            "affiliation.url",
            "affiliation.name",
            "promotion.url",
            "opponent.name",
            "opponent.url",
        ],
        axis="columns",
    )

    # Convert data type
    dtypes = {
        "id": pd.StringDtype(),
        "nationality": pd.CategoricalDtype(),
        "weight_class": pd.CategoricalDtype(),
        "career_earnings": pd.Int32Dtype(),
        "height": pd.Float32Dtype(),
        "reach": pd.Float32Dtype(),
        "affiliation.id": pd.CategoricalDtype(),
        "head_coach": pd.CategoricalDtype(),
        "college": pd.CategoricalDtype(),
        "division": pd.CategoricalDtype(),
        "status": pd.CategoricalDtype(),
        "age": pd.Int16Dtype(),
        "billing": pd.CategoricalDtype(),
        "referee": pd.StringDtype(),
        "promotion.id": pd.StringDtype(),
        "ended_by.type": pd.CategoricalDtype(),
        "ended_by.detail": pd.StringDtype(),
        "ended_at.round": pd.Int16Dtype(),
        "weight.is_open": pd.BooleanDtype(),
        "weight.is_catch": pd.BooleanDtype(),
        "weight.class": pd.CategoricalDtype(),
        "weight.limit": pd.Float32Dtype(),
        "weight.weigh_in": pd.Float32Dtype(),
        "opponent.id": pd.StringDtype(),
        "opponent.record.w": pd.Int16Dtype(),
        "opponent.record.l": pd.Int16Dtype(),
        "opponent.record.d": pd.Int16Dtype(),
        "record.w": pd.Int16Dtype(),
        "record.l": pd.Int16Dtype(),
        "record.d": pd.Int16Dtype(),
        "title_info.name": pd.StringDtype(),
        "title_info.as": pd.CategoricalDtype(),
        "title_info.type": pd.CategoricalDtype(),
        "odds": pd.Float32Dtype(),
    }
    for c in df.columns:
        if c.startswith("career_record"):
            dtypes[c] = pd.Int16Dtype()
    df = df.astype(dtypes)
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], format="%Y-%m-%d")
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["ended_at.time"] = pd.to_timedelta(df["ended_at.time"])

    # Inputate columns "height" & "reach"
    for c in ["height", "reach"]:
        df[c] = df.groupby(["weight_class", "nationality"])[c].transform(
            lambda x: x.fillna(x.mean())
        )
        df[c] = df.groupby(["weight_class"])[c].transform(lambda x: x.fillna(x.mean()))
        df[c] = df[c].fillna(df[c].mean())

    # Inputate columns "career_record.*.*"
    for c in df.columns:
        if c.startswith("career_record"):
            df[c] = df[c].fillna(0)

    # Inputate na values of categorical data with "unknown"
    for c in ["nationality", "head_coach", "college", "affiliation.id"]:
        df[c] = df[c].cat.add_categories("unknown").fillna("unknown")

    df.info(verbose=True, show_counts=True)


if __name__ == "__main__":
    main()
