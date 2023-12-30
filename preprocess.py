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
    profiles, results, _, _ = load_dataframes(json_dir)

    # Fill columns of profiles
    click.secho("Profiles (plain)", bg="green")
    profiles.info(verbose=True)
    for column in ["nationality", "affiliation", "college", "head_coach"]:
        profiles[column].fillna("n/a", inplace=True)
    profiles = fill_height_and_reach(profiles)
    profiles = fill_date_of_birth(profiles, results)
    click.secho("Profiles (filled)", bg="yellow")
    profiles.info(verbose=True)

    # Fill columns of results
    click.secho("Results (plain)", bg="green")
    results.info(verbose=True)
    for column in ["billing", "referee", "title_info.for", "title_info.as"]:
        results[column].fillna("n/a", inplace=True)
    results = fill_age(results, profiles)
    click.secho("Results (filled)", bg="yellow")
    results.info(verbose=True)


def load_dataframes(
    json_dir: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with open(os.path.join(json_dir, "profiles.json")) as f:
        profiles = (
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
        profiles["date_of_birth"] = pd.to_datetime(
            profiles["date_of_birth"], format="%Y-%m-%d"
        )
        for column in ["id", "affiliation"]:
            profiles[column] = shorten_url(profiles[column])
        profiles = profiles.set_index("id")
    with open(os.path.join(json_dir, "results.json")) as f:
        results = (
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
        results["date"] = pd.to_datetime(results["date"], format="%Y-%m-%d")
        for column in ["end_time.time", "end_time.elapsed"]:
            results[column] = to_minutes(results[column])
        for column in ["fighter", "opponent", "match", "event"]:
            results[column] = shorten_url(results[column])
        results = fill_match_id(results)
        results = results.set_index("match")
    with open(os.path.join(json_dir, "events.json")) as f:
        events = (
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
        for column in ["id", "promotion"]:
            events[column] = shorten_url(events[column])
        events["date"] = pd.to_datetime(events["date"], format="%Y-%m-%d")
        events = events.set_index("id")
    with open(os.path.join(json_dir, "promotions.json")) as f:
        promotions = (
            pd.json_normalize(json.load(f))
            .drop(["shorten", "name"], axis="columns")
            .astype({"id": "string", "headquarter": "string"})
        )
        promotions["id"] = shorten_url(promotions["id"])
        promotions = promotions.set_index("id")

    with open(os.path.join(json_dir, "female.json")) as f:
        female = (
            pd.json_normalize(json.load(f))
            .drop(["name"], axis="columns")
            .astype({"id": "string"})
        )
        mask = profiles.index.isin(female["id"].unique())
        profiles.loc[mask, "sex"] = consts.SEX_WOMAN
        profiles.loc[~mask, "sex"] = consts.SEX_MAN
        profiles["sex"] = profiles["sex"].astype("string")

    # Filter records
    profiles = profiles[profiles.index.isin(results["fighter"].unique())]
    events = events[events.index.isin(results["event"].unique())]
    promotions = promotions[promotions.index.isin(events["promotion"].unique())]
    return (profiles, results, events, promotions)


def count_nan(x: pd.Series | pd.DataFrame) -> int:
    if isinstance(x, pd.Series):
        return x.isnull().sum()
    return x.isnull().sum().sum()


def shorten_url(url: pd.Series | str) -> pd.Series | str:
    if isinstance(url, pd.Series):
        return url.map(lambda x: x.split("/")[-1], na_action="ignore").astype(url.dtype)
    return url.split("/")[-1]


def to_minutes(time: pd.Series | str, dtype="float32") -> pd.Series | float:
    def calc_minutes(t: str):
        min, sec = t.split(":")
        return float(min) + float(sec) / 60

    if isinstance(time, pd.Series):
        return time.map(calc_minutes, na_action="ignore").astype(dtype)
    return calc_minutes(time)


def fill_age(results: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(
        results,
        profiles[["date_of_birth"]],
        left_on="fighter",
        right_index=True,
        how="left",
    )
    merged["age"].fillna(
        ((merged["date"] - merged["date_of_birth"]).dt.days / 365.25).astype(
            merged["age"].dtype
        ),
        inplace=True,
    )
    return merged.drop(["date_of_birth"], axis="columns")


def fill_date_of_birth(profiles: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(
        profiles,
        results.groupby("fighter")["date"].min().rename("date_at_debut"),
        left_index=True,
        right_index=True,
        how="left",
    )
    merged = pd.merge(
        merged,
        results.groupby("fighter")["age"].min().rename("age_at_debut"),
        left_index=True,
        right_index=True,
        how="left",
    )
    merged["mean_age_at_debut"] = merged.groupby(["weight_class", "sex"])[
        "age_at_debut"
    ].transform(lambda series: series.mean())
    merged["date_of_birth"].fillna(
        merged["date_at_debut"]
        - pd.to_timedelta(merged["mean_age_at_debut"] * 365.25, unit="d"),
        inplace=True,
    )
    ret = merged.drop(
        ["date_at_debut", "age_at_debut", "mean_age_at_debut"], axis="columns"
    )
    return ret


def fill_height_and_reach(profiles: pd.DataFrame) -> pd.DataFrame:
    ret = profiles.copy()
    for column in ["height", "reach"]:
        ret[column] = ret.groupby(["nationality", "sex", "weight_class"])[
            column
        ].transform(lambda series: series.fillna(series.mean()))
        if count_nan(ret[column]) > 0:
            ret[column] = ret.groupby(["sex", "weight_class"])[column].transform(
                lambda series: series.fillna(series.mean())
            )
            if count_nan(ret[column]) > 0:
                ret[column] = ret.groupby(["weight_class"])[column].transform(
                    lambda series: series.fillna(series.mean())
                )
                if count_nan(ret[column]) > 0:
                    ret[column] = ret.groupby(["sex"])[column].transform(
                        lambda series: series.fillna(series.mean())
                    )
    return ret


def fill_match_id(results: pd.DataFrame) -> pd.DataFrame:
    def generate_match_id(row: pd.DataFrame) -> str:
        id_a = min(row["fighter"], row["opponent"])
        id_b = max(row["fighter"], row["opponent"])
        match_id = id_a + "-vs-" + id_b + "-at-" + row["date"].strftime("%Y-%m-%d")
        return match_id

    ret = results.copy()
    mask = (
        results["match"].isna()
        & ~results["fighter"].isna()
        & ~results["opponent"].isna()
        & ~results["date"].isna()
    )
    ret["match"].fillna(
        results.loc[mask, ["fighter", "opponent", "date"]].apply(
            generate_match_id, axis=1
        ),
        inplace=True,
    )
    return ret


if __name__ == "__main__":
    main()
