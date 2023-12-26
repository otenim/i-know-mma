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
    profiles, results, events, promotions = load_dataframes(json_dir)

    # Fill columns of profiles
    for column in ["nationality", "affiliation", "college", "head_coach"]:
        profiles[column].fillna("n/a", inplace=True)
    profiles = fill_weight_class(profiles, results)
    profiles = fill_height_and_reach(profiles)
    profiles = fill_date_of_birth(profiles, results)

    # Fill columns of results
    results = fill_match_id(results)
    results = fill_age(results, profiles)
    profiles.info(verbose=True)
    results.info(verbose=True)
    events.info(verbose=True)
    promotions.info(verbose=True)


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
            profiles[column] = shorten_url(profiles[column])
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
        events["id"] = shorten_url(events["id"])
        events["promotion"] = shorten_url(events["promotion"])
        events["date"] = pd.to_datetime(events["date"], format="%Y-%m-%d")
    with open(os.path.join(json_dir, "promotions.json")) as f:
        promotions = (
            pd.json_normalize(json.load(f))
            .drop(["shorten", "name"], axis="columns")
            .astype({"id": "string", "headquarter": "string"})
        )
        promotions["id"] = shorten_url(promotions["id"])

    with open(os.path.join(json_dir, "female.json")) as f:
        female_ids = set(map(lambda x: shorten_url(x["id"]), json.load(f)))
        mask = profiles["id"].isin(female_ids)
        profiles.loc[mask, "sex"] = consts.SEX_WOMAN
        profiles.loc[~mask, "sex"] = consts.SEX_MAN
        profiles["sex"] = profiles["sex"].astype("string")

    # Filter records
    profiles = profiles[profiles["id"].isin(set(results["fighter"]))]
    events = events[events["id"].isin(set(results["event"]))]
    promotions = promotions[promotions["id"].isin(set(events["promotion"]))]
    return (profiles, results, events, promotions)


def count_nan(x: pd.Series | pd.DataFrame) -> int:
    if isinstance(x, pd.Series):
        return x.isnull().sum()
    return x.isnull().sum().sum()


def shorten_url(url: pd.Series | str) -> pd.Series | str:
    if isinstance(url, pd.Series):
        return url.apply(lambda x: x if pd.isna(x) else x.split("/")[-1]).astype(
            url.dtype
        )
    return url.split("/")[-1]


def to_minutes(time: pd.Series | str, dtype="float32") -> pd.Series | float:
    def calc_minutes(x: str) -> float:
        if pd.isna(x):
            return x
        split = x.split(":")
        return float(split[0]) + float(split[1]) / 60

    if isinstance(time, pd.Series):
        return time.apply(calc_minutes).astype(dtype)
    return calc_minutes(time)


def fill_age(results: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(
        results,
        profiles[["id", "date_of_birth"]].set_index("id"),
        left_on="fighter",
        right_index=True,
        how="left",
    )
    results["age"].fillna(
        ((merged["date"] - merged["date_of_birth"]).dt.days / 365.25).astype(
            results["age"].dtype
        ),
        inplace=True,
    )
    return results


def fill_date_of_birth(profiles: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    date_at_debut = results.groupby("fighter")["date"].min().rename("date_at_debut")
    merged = pd.merge(
        profiles, date_at_debut, left_on="id", right_index=True, how="left"
    )
    age_at_debut = results.groupby("fighter")["age"].min().rename("age_at_debut")
    merged = pd.merge(merged, age_at_debut, left_on="id", right_index=True, how="left")
    mean_age_at_debut = (
        merged.groupby(["weight_class", "sex"])["age_at_debut"]
        .mean()
        .rename("mean_age_at_debut")
    )
    merged = pd.merge(
        merged,
        mean_age_at_debut,
        left_on=["weight_class", "sex"],
        right_index=True,
        how="left",
    )
    profiles["date_of_birth"].fillna(
        merged["date_at_debut"]
        - pd.to_timedelta(merged["mean_age_at_debut"] * 365.25, unit="d"),
        inplace=True,
    )
    return profiles


def fill_weight_class(profiles: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    def helper(id: str) -> str | float:
        ser = (
            results[results["fighter"] == id]
            .sort_values(by="date", ascending=False)["weight.class"]
            .dropna()
        )
        if ser.empty:
            return np.nan
        return ser.iloc[0]

    mask = profiles["weight_class"].isna()
    profiles.loc[mask, "weight_class"] = profiles.loc[mask, "id"].apply(helper)
    return profiles


def fill_height_and_reach(profiles: pd.DataFrame) -> pd.DataFrame:
    for column in ["height", "reach"]:
        profiles[column] = profiles.groupby(["nationality", "sex", "weight_class"])[
            column
        ].transform(lambda ser: ser.fillna(ser.mean()))
        profiles[column] = profiles.groupby(["sex", "weight_class"])[column].transform(
            lambda ser: ser.fillna(ser.mean())
        )
        profiles[column] = profiles.groupby(["weight_class"])[column].transform(
            lambda ser: ser.fillna(ser.mean())
        )
        profiles[column] = profiles.groupby(["sex"])[column].transform(
            lambda ser: ser.fillna(ser.mean())
        )
    return profiles


def fill_match_id(results: pd.DataFrame) -> pd.DataFrame:
    def helper(row: pd.DataFrame) -> str:
        if not pd.isna(row["match"]):
            return row["match"]
        id_a = min(row["fighter"], row["opponent"])
        id_b = max(row["fighter"], row["opponent"])
        match_id = (
            id_a.split("/")[-1]
            + "-vs-"
            + id_b.split("/")[-1]
            + "-at-"
            + row["date"].strftime("%Y-%m-%d")
        )
        return match_id

    mask = ~(
        results["fighter"].isna() & results["opponent"].isna() & results["date"].isna()
    )
    results.loc[mask, "match"] = results.loc[mask].apply(helper, axis=1)
    return results


if __name__ == "__main__":
    main()
