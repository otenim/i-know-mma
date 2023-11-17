import pandas as pd
import click
import json
import numpy as np
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
            "born",
            "out_of",
            "last_weigh_in",
            "affiliation.url",
            "affiliation.name",
            "promotion.url",
            "opponent.name",
            "opponent.url",
            "odds",
        ],
        axis="columns",
    )

    # Convert data type
    dtypes = {
        "id": "category",
        "nationality": "category",
        "weight_class": "category",
        "career_earnings": "float32",
        "height": "float32",
        "reach": "float32",
        "affiliation.id": "category",
        "head_coach": "category",
        "college": "category",
        "division": "category",
        "status": "category",
        "age": "float32",
        "billing": "category",
        "referee": "category",
        "promotion.id": "category",
        "ended_by.type": "category",
        "ended_by.detail": "category",
        "ended_at.round": "float32",
        "weight.is_open": "boolean",
        "weight.is_catch": "boolean",
        "weight.class": "category",
        "weight.limit": "float32",
        "weight.weigh_in": "float32",
        "opponent.id": "string",
        "opponent.record.w": "float32",
        "opponent.record.l": "float32",
        "opponent.record.d": "float32",
        "record.w": "float32",
        "record.l": "float32",
        "record.d": "float32",
        "title_info.name": "category",
        "title_info.as": "category",
        "title_info.type": "category",
    }
    for c in df.columns:
        if c.startswith("career_record"):
            dtypes[c] = "float32"
    df = df.astype(dtypes)
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], format="%Y-%m-%d")
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["ended_at.time"] = pd.to_timedelta(df["ended_at.time"])

    # Inputate columns "height" & "reach"
    for c in ["height", "reach"]:
        df[c] = df.groupby(["weight_class", "nationality"], observed=True)[c].transform(
            lambda x: x.fillna(x.mean())
        )
        df[c] = df.groupby("weight_class", observed=True)[c].transform(
            lambda x: x.fillna(x.mean())
        )
        df[c] = df[c].fillna(df[c].mean())

    # Inputate columns "career_record.*.*"
    for c in df.columns:
        if c.startswith("career_record"):
            df[c] = df[c].fillna(0)

    # Inputate na values of categorical data with "unknown"
    for c in [
        "nationality",
        "head_coach",
        "college",
        "affiliation.id",
        "referee",
        "billing",
        "promotion.id",
    ]:
        df[c] = df[c].cat.add_categories("unknown").fillna("unknown")

    # Inputate columns "date_of_birth" & "age"
    date_at_debut = (
        df.groupby("id", observed=True)["date"].min().rename(f"date_at_debut")
    )
    df = pd.merge(df, date_at_debut, left_on="id", right_index=True, how="left")
    mean_age_at_debut_by_weight_class = (
        df.dropna(subset=["age"])
        .groupby("weight_class", observed=True)
        .apply(lambda x: x.groupby("id", observed=True)["age"].min().mean())
        .rename(f"mean_age_at_debut_by_weight_class")
    )
    df = pd.merge(
        df,
        mean_age_at_debut_by_weight_class,
        left_on="weight_class",
        right_index=True,
        how="left",
    )
    df["age"].fillna(
        (
            (df["date"].dt.year - df["date_at_debut"].dt.year)
            + df["mean_age_at_debut_by_weight_class"]
        ).astype("float32"),
        inplace=True,
    )
    df["date_of_birth"].fillna(
        df["date_at_debut"] - pd.to_timedelta(365.0 * df["age"], unit="D"), inplace=True
    )
    df = df.drop(["mean_age_at_debut_by_weight_class", "date_at_debut"], axis="columns")
    df.info(show_counts=True, verbose=True)


if __name__ == "__main__":
    main()
