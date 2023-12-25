import pandas as pd
import numpy as np
import click
import json
import os
from scraper.scraper.tapology import consts


@click.command()
@click.argument(
    "json_dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.argument(
    "out_dir",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def main(json_dir: str, out_dir: str):
    # Load json files
    df_profiles, df_results, df_events, df_promotions = load_dataframes(json_dir)
    df_profiles.info(verbose=True)
    df_results.info(verbose=True)
    df_events.info(verbose=True)
    df_promotions.info(verbose=True)


def load_dataframes(
    json_dir: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with open(os.path.join(json_dir, "profiles.json")) as f:
        df_profiles = (
            pd.json_normalize(json.load(f))
            .drop(
                [
                    "name",
                    "nickname",
                    "record.w",
                    "record.l",
                    "record.d",
                    "last_weigh_in",
                    "foundation_styles",
                    "born",
                    "out_of",
                ],
                axis="columns",
            )
            .astype(
                {
                    "id": "string",
                    "nationality": "string",
                    "weight_class": "string",
                    "earnings": "float32",
                    "affiliation": "string",
                    "height": "float32",
                    "reach": "float32",
                    "college": "string",
                    "head_coach": "string",
                }
            )
        )
        df_profiles["date_of_birth"] = pd.to_datetime(
            df_profiles["date_of_birth"], format="%Y-%m-%d"
        )
    with open(os.path.join(json_dir, "results.json")) as f:
        df_results = (
            pd.json_normalize(json.load(f))
            .drop(["odds"], axis="columns")
            .astype(
                {
                    "fighter": "string",
                    "division": "string",
                    "match": "string",
                    "status": "string",
                    "sport": "string",
                    "age": "float32",
                    "opponent": "string",
                    "record_before.w": "float32",
                    "record_before.l": "float32",
                    "record_before.d": "float32",
                    "record_after.w": "float32",
                    "record_after.l": "float32",
                    "record_after.d": "float32",
                    "event": "string",
                    "billing": "string",
                    "round_format": "string",
                    "referee": "string",
                    "weight.class": "string",
                    "weight.limit": "float32",
                    "weight.weigh_in": "float32",
                    "method.type": "string",
                    "method.by": "string",
                    "end_time.round": "float32",
                    "title_info.as": "string",
                    "title_info.for": "string",
                }
            )
        )
        df_results["date"] = pd.to_datetime(df_results["date"], format="%Y-%m-%d")
        df_results["end_time.time"] = to_minutes(df_results["end_time.time"])
        df_results["end_time.elapsed"] = to_minutes(df_results["end_time.elapsed"])
    with open(os.path.join(json_dir, "events.json")) as f:
        df_events = (
            pd.json_normalize(json.load(f))
            .drop(
                [
                    "name",
                    "ownership",
                    "venue",
                    "location",
                    "cards",
                    "total_cards",
                    "ring_announcer",
                ],
                axis="columns",
            )
            .astype(
                {
                    "id": "string",
                    "promotion": "string",
                    "region": "string",
                    "enclosure": "string",
                }
            )
        )
    with open(os.path.join(json_dir, "promotions.json")) as f:
        df_promotions = (
            pd.json_normalize(json.load(f))
            .drop(["shorten"], axis="columns")
            .astype({"id": "string", "headquarter": "string"})
        )

    with open(os.path.join(json_dir, "female.json")) as f:
        female_ids = set(map(lambda x: x["id"], json.load(f)))
        mask = df_profiles["id"].isin(female_ids)
        df_profiles.loc[mask, "sex"] = consts.SEX_WOMAN
        df_profiles.loc[~mask, "sex"] = consts.SEX_MAN
        df_profiles["sex"] = df_profiles["sex"].astype("string")
    return (df_profiles, df_results, df_events, df_promotions)


def count_nan(x: pd.Series | pd.DataFrame) -> int:
    if isinstance(x, pd.Series):
        return x.isnull().sum()
    return x.isnull().sum().sum()


def to_minutes(time: pd.Series, dtype="float32") -> float:
    def calc_minutes(x: str) -> float:
        if pd.isna(x):
            return x
        split = x.split(":")
        return float(split[0]) + float(split[1]) / 60

    return time.apply(calc_minutes).astype(dtype)


if __name__ == "__main__":
    main()
