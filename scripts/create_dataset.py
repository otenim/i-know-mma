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
    df = pd.merge(df_fighters, df_results, on="id")

    # Convert data type
    dtypes = {
        "url": pd.StringDtype(),
        "id": pd.StringDtype(),
        "name": pd.StringDtype(),
        "nationality": pd.CategoricalDtype(),
        "weight_class": pd.CategoricalDtype(),
        "career_earnings": pd.Int32Dtype(),
        "nickname": pd.StringDtype(),
        "height": pd.Float32Dtype(),
        "reach": pd.Float32Dtype(),
        "last_weigh_in": pd.Float32Dtype(),
        "affiliation.url": pd.StringDtype(),
        "affiliation.id": pd.StringDtype(),
        "affiliation.name": pd.StringDtype(),
        "head_coach": pd.StringDtype(),
        "college": pd.StringDtype(),
        "division": pd.CategoricalDtype(),
        "status": pd.CategoricalDtype(),
        "age": pd.Int16Dtype(),
        "billing": pd.CategoricalDtype(),
        "referee": pd.StringDtype(),
        "promotion.url": pd.StringDtype(),
        "promotion.id": pd.StringDtype(),
        "ended_by.type": pd.CategoricalDtype(),
        "ended_by.detail": pd.StringDtype(),
        "ended_at.round": pd.Int16Dtype(),
        "weight.is_open": pd.BooleanDtype(),
        "weight.is_catch": pd.BooleanDtype(),
        "weight.class": pd.CategoricalDtype(),
        "weight.limit": pd.Float32Dtype(),
        "weight.weigh_in": pd.Float32Dtype(),
        "opponent.name": pd.StringDtype(),
        "opponent.id": pd.StringDtype(),
        "opponent.url": pd.StringDtype(),
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

    # Inputate column "nationality"
    df["nationality"] = (
        df["nationality"].cat.add_categories("unknown").fillna("unknown")
    )

    # Inputate columns "career_record.*.*"
    for c in df.columns:
        if c.startswith("career_record"):
            df[c] = df[c].fillna(0)

    df.info(verbose=True, show_counts=True)


if __name__ == "__main__":
    main()
