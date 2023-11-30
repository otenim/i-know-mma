import pandas as pd
import click
import json
import numpy as np
from scraper.spiders.constants import *
from typing import Union


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

    # Load dataframe of result data
    df_results = pd.json_normalize(jsondata, record_path="results", meta=["id"])

    # Merge fighters & results
    df = (
        pd.merge(df_fighters, df_results, on="id")
        .drop(
            [
                "name",
                "born",
                "out_of",
                "nickname",
                "foundation_styles",
                "title_info.for",
                "title_info.as",
                "odds",
            ],
            axis="columns",
        )
        .astype(
            {
                "id": "string",
                "nationality": "string",
                "weight_class": "string",
                "career_earnings": "float32",
                "affiliation": "string",
                "height": "float32",
                "reach": "float32",
                "head_coach": "string",
                "college": "string",
                "division": "string",
                "sport": "string",
                "status": "string",
                "opponent": "string",
                "promotion": "string",
                "method": "string",
                "supplemental": "string",
                "billing": "string",
                "round_format": "string",
                "referee": "string",
                "record.w": "float32",
                "record.l": "float32",
                "record.d": "float32",
                "round": "float32",
                "time.m": "float32",
                "time.s": "float32",
                "age": "float32",
                "weight.class": "string",
                "weight.limit": "float32",
                "weight.weigh_in": "float32",
            }
        )
    )
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], format="%Y-%m-%d")
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df.info(verbose=True)

    # Correct dataset
    df = correct(df)

    # Fill height & reach
    df = fill_height(df)
    df = fill_reach(df)

    # Fill nans with "n/a"
    for c in [
        "nationality",
        "head_coach",
        "college",
        "affiliation",
        "referee",
        "billing",
        "promotion",
    ]:
        df[c].fillna("n/a", inplace=True)

    # Fill date_of_birth
    df = fill_date_of_birth(df)

    # Fill age
    df = fill_age(df)

    # Fill round_format
    df = fill_round_format(df)

    # # Fill ended_by
    # df = fill_ended_by(df)

    # # Fill ended_at
    # df = fill_ended_at(df)
    df.info(verbose=True)


def correct(df: pd.DataFrame) -> pd.DataFrame:
    mask = (df["id"] == "174315-crob-pugliesi") & (
        df["date"] == pd.to_datetime("2019-10-17", format="%Y-%m-%d")
    )
    if mask.sum() == 1:
        df.loc[mask, "round_format"] = "15"
    return df


def count_nan(x: Union[pd.Series, pd.DataFrame]) -> int:
    if isinstance(x, pd.Series):
        return x.isnull().sum()
    return x.isnull().sum().sum()


def fill_height(df: pd.DataFrame) -> pd.DataFrame:
    df["height"] = df.groupby(["weight_class", "nationality"])["height"].transform(
        lambda x: x.fillna(x.mean())
    )
    if count_nan(df["height"]) > 0:
        df["height"] = df.groupby("weight_class")["height"].transform(
            lambda x: x.fillna(x.mean())
        )
        if count_nan(df["height"]) > 0:
            df["height"].fillna(df["height"].mean(), inplace=True)
    return df


def fill_reach(df: pd.DataFrame) -> pd.DataFrame:
    df["reach"] = df.groupby(["weight_class", "nationality"])["reach"].transform(
        lambda x: x.fillna(x.mean())
    )
    if count_nan(df["reach"]) > 0:
        df["reach"] = df.groupby("weight_class")["reach"].transform(
            lambda x: x.fillna(x.mean())
        )
        if count_nan(df["reach"]) > 0:
            df["reach"].fillna(df["reach"].mean(), inplace=True)
    return df


def fill_date_of_birth(df: pd.DataFrame) -> pd.DataFrame:
    date_at_debut = df.groupby("id")["date"].min()
    mean_age_at_debut = df.groupby("id")["age"].min().mean()
    date_of_birth_inferred = (
        date_at_debut - pd.Timedelta(mean_age_at_debut * 365.25, unit="d")
    ).rename("date_of_birth.inferred")
    merged = pd.merge(
        df, date_of_birth_inferred, left_on="id", right_index=True, how="left"
    )
    df["date_of_birth"].fillna(merged["date_of_birth.inferred"], inplace=True)
    return df


def fill_age(df: pd.DataFrame) -> pd.DataFrame:
    df["age"].fillna(
        ((df["date"] - df["date_of_birth"]).dt.days / 365.25).astype("float32"),
        inplace=True,
    )
    return df


def fill_ending_method(df: pd.DataFrame) -> pd.DataFrame:
    df["ended_by.detail"] = df.groupby("id")["ended_by.detail"].transform(
        lambda x: x if x.mode().empty else x.fillna(x.mode().iat[0])
    )
    if count_nan(df["ended_by.detail"]) > 0:
        df["ended_by.detail"] = df.groupby("weight_class")["ended_by.detail"].transform(
            lambda x: x if x.mode().empty else x.fillna(x.mode().iat[0])
        )
        if count_nan(df["ended_by.detail"]) > 0:
            df["ended_by.detail"].fillna(
                df["ended_by.detail"].mode().iat[0], inplace=True
            )
    df["ended_by.type"].fillna(
        (df["ended_by.detail"].apply(lambda x: infer(x))).astype("string"), inplace=True
    )
    return df


def fill_round_format(df: pd.DataFrame) -> pd.DataFrame:
    df["round_format"] = df.groupby(["promotion"])["round_format"].transform(
        lambda x: x if x.mode().empty else x.fillna(x.mode().iat[0])
    )
    if count_nan(df["round_format"]) > 0:
        df["round_format"] = df.groupby(["sport", "division"])[
            "round_format"
        ].transform(lambda x: x if x.mode().empty else x.fillna(x.mode().iat[0]))
    # # Fill minutes
    # df["regulation.minutes"].fillna(
    #     df["round_format"]
    #     .apply(lambda x: x if x is np.nan else np.nan if "*" in x else calc_minutes(x))
    #     .astype(df["regulation.minutes"].dtype),
    #     inplace=True,
    # )
    # if count_nan(df["regulation.minutes"]) > 0:
    #     df["regulation.minutes"].fillna(df["ended_at.elapsed"], inplace=True)
    #     if count_nan(df["regulation.minutes"]) > 0:
    #         mask = df["round_format"] == "*"
    #         masked = df.loc[mask, "regulation.minutes"]
    #         df.loc[mask, "regulation.minutes"] = masked.fillna(
    #             masked.mean(),
    #         )
    return df


def fill_ended_at(df: pd.DataFrame) -> pd.DataFrame:
    # Fill elapsed time bouts ended by decision
    mask = df["ended_by.type"] == ENDED_BY_DECISION
    df.loc[mask, "ended_at.elapsed"] = df.loc[mask, "ended_at.elapsed"].fillna(
        df.loc[mask, "regulation.minutes"]
    )

    # Progress
    df["ended_at.progress"] = df["ended_at.elapsed"] / df["regulation.minutes"]
    df["ended_at.progress"] = df.groupby("id")["ended_at.progress"].transform(
        lambda x: x.fillna(x.mean())
    )
    if count_nan(df["ended_at.progress"]) > 0:
        df["ended_at.progress"] = df.groupby("weight_class")[
            "ended_at.progress"
        ].transform(lambda x: x.fillna(x.mean()))
        if count_nan(df["ended_at.progress"]) > 0:
            df["ended_at.progress"].fillna(df["ended_at.progress"].mean(), inplace=True)

    # Fill round
    df["ended_at.round"].fillna(
        np.ceil(df["regulation.rounds"] * df["ended_at.progress"]), inplace=True
    )

    # Fill elapsed
    df["ended_at.elapsed"].fillna(
        df["regulation.minutes"] * df["ended_at.progress"], inplace=True
    )

    # Fill time

    df = df.drop(["ended_at.progress"], axis="columns")
    return df


if __name__ == "__main__":
    main()
