import pandas as pd
import click
import json
import numpy as np
from scraper.spiders.constants import *
from scraper.spiders.fighters_spider import parse_round_format, to_weight_limit
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
    df = pd.merge(df_fighters, df_results, on="id").astype(
        {
            "id": "string",
            "name": "string",
            "nickname": "string",
            "nationality": "string",
            "last_weigh_in": "float32",
            "weight_class": "string",
            "career_earnings": "float32",
            "career_record.w": "float32",
            "career_record.l": "float32",
            "career_record.d": "float32",
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
            "title_info.for": "string",
            "title_info.as": "string",
            "odds": "float32",
        }
    )
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], format="%Y-%m-%d")
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["time"] = df["time.m"] + df["time.s"] / 60
    df = df.drop(
        [
            "name",
            "nickname",
            "career_record.w",
            "career_record.l",
            "career_record.d",
            "time.m",
            "time.s",
            "title_info.for",
            "title_info.as",
            "odds",
            "last_weigh_in",
            "born",
            "out_of",
        ],
        axis="columns",
    )
    click.echo("> Plain")
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
    df["round_format.rounds"] = calc_rounds(df["round_format"])
    df["round_format.minutes"] = calc_minutes(df["round_format"])

    # Fill round
    df = fill_round(df)

    # Fill time
    df = fill_time(df)

    # Fill weight
    df = fill_weight(df)

    click.echo("> Processed")
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


def fill_round_format(df: pd.DataFrame) -> pd.DataFrame:
    df["round_format"] = df.groupby(["promotion", "sport", "division"])[
        "round_format"
    ].transform(lambda x: x if x.mode().empty else x.fillna(x.mode().iat[0]))
    if count_nan(df["round_format"]) > 0:
        df["round_format"] = df.groupby(["sport", "division"])[
            "round_format"
        ].transform(lambda x: x if x.mode().empty else x.fillna(x.mode().iat[0]))
    return df


def fill_round(df: pd.DataFrame) -> pd.DataFrame:
    # Decision
    mask = df["method"].isin(
        [
            ENDING_METHOD_DECISION_UNANIMOUS,
            ENDING_METHOD_DECISION_MAJORITY,
            ENDING_METHOD_DECISION_SPLIT,
            ENDING_METHOD_DECISION,
            ENDING_METHOD_DRAW_UNANIMOUS,
            ENDING_METHOD_DRAW_MAJORITY,
            ENDING_METHOD_DRAW_SPLIT,
            ENDING_METHOD_DRAW_UNKNOWN,
        ]
    )
    rounds = calc_rounds(df["round_format"])[mask]
    df.loc[mask, "round"] = df.loc[mask, "round"].fillna(rounds)
    mask = df["round_format"] == "*"
    df.loc[mask, "round"] = df.loc[mask, "round"].fillna(1)

    # Fill
    df["round"] = df.groupby(["id", "round_format"])["round"].transform(
        lambda x: x if x.mode().empty else x.fillna(x.mode().iat[0])
    )
    if count_nan(df["round"]) > 0:
        df["round"] = df.groupby("id")["round"].transform(
            lambda x: x if x.mode().empty else x.fillna(x.mode().iat[0])
        )
    return df


def fill_time(df: pd.DataFrame) -> pd.DataFrame:
    # Decision
    mask = df["method"].isin(
        [
            ENDING_METHOD_DECISION_UNANIMOUS,
            ENDING_METHOD_DECISION_MAJORITY,
            ENDING_METHOD_DECISION_SPLIT,
            ENDING_METHOD_DECISION,
            ENDING_METHOD_DRAW_UNANIMOUS,
            ENDING_METHOD_DRAW_MAJORITY,
            ENDING_METHOD_DRAW_SPLIT,
            ENDING_METHOD_DRAW_UNKNOWN,
        ]
    )

    def helper(row: pd.DataFrame) -> pd.DataFrame:
        round_format = row["round_format"]
        if pd.isna(round_format):
            return row
        parsed = parse_round_format(round_format)
        if parsed["type"] == ROUND_FORMAT_TYPE_NORMAL:
            if parsed["ot"]:
                row["time"] = parsed["ot_minutes"]
            else:
                row["time"] = parsed["round_minutes"][-1]
            return row
        return row

    df.loc[mask] = df.loc[mask].apply(helper, axis=1)

    # Fill
    df["time"] = df.groupby(["id", "round_format"])["time"].transform(
        lambda x: x.fillna(x.mean())
    )
    return df


def fill_weight(df: pd.DataFrame):
    # Fill weight.class
    df = df.sort_values(by=["date"])
    df["weight.class"] = df.groupby("id")["weight.class"].ffill().bfill()

    # Fill weight.limit
    df["weight.limit"].fillna(
        df["weight.class"]
        .apply(lambda x: x if pd.isna(x) else to_weight_limit(x))
        .astype(df["weight.limit"].dtype),
        inplace=True,
    )

    # Fill weight.weigh_in
    df["weight.weigh_in"].fillna(df["weight.limit"], inplace=True)
    return df


# def create_progress(df: pd.DataFrame) -> pd.DataFrame:
#     def helper(row):
#         if row.isnull().any():
#             return np.nan
#         round_format = row["round_format"]
#         time = row["time"]
#         round = int(row["round"])
#         parsed = parse_round_format(round_format)
#         type_ = parsed["type"]
#         if type_ == ROUND_FORMAT_TYPE_NORMAL:
#             round_minutes = parsed["round_minutes"]
#             elapsed = 0
#             for i in range(round - 1):
#                 elapsed += round_minutes[i]
#             elapsed += time
#             return elapsed
#         elif type_ == ROUND_FORMAT_TYPE_UNLIM_ROUNDS:
#             return parsed["minutes_per_round"] * (round - 1) + time
#         elif type_ == ROUND_FORMAT_TYPE_UNLIM_ROUND_TIME:
#             return time
#         elif type_ == ROUND_FORMAT_TYPE_ROUND_TIME_UNKNONW:
#             return np.nan
#         raise ValueError(f"unexpected round format type: {type_}")

#     elapsed = (
#         df[["time", "round", "round_format"]].apply(helper, axis=1).astype("float32")
#     )
#     df["progress"] = elapsed / df["minutes"]
#     return df


def calc_rounds(round_format: pd.Series) -> pd.Series:
    def helper(x):
        if pd.isna(x):
            return np.nan
        parsed = parse_round_format(x)
        type_ = parsed["type"]
        if type_ in [
            ROUND_FORMAT_TYPE_NORMAL,
            ROUND_FORMAT_TYPE_UNLIM_ROUND_TIME,
            ROUND_FORMAT_TYPE_ROUND_TIME_UNKNONW,
        ]:
            return parsed["rounds"]
        return np.nan

    return round_format.apply(helper).astype("float32")


def calc_minutes(round_format: pd.DataFrame) -> pd.DataFrame:
    def helper(x):
        if pd.isna(x):
            return np.nan
        parsed = parse_round_format(x)
        type_ = parsed["type"]
        if type_ == ROUND_FORMAT_TYPE_NORMAL:
            return parsed["minutes"]
        return np.nan

    return round_format.apply(helper).astype("float32")


if __name__ == "__main__":
    main()