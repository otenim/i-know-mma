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

    # Dataframe of fighters
    df_fighters = pd.json_normalize(
        jsondata,
        errors="ignore",
    ).astype(
        {
            "url": pd.StringDtype(),
            "id": pd.StringDtype(),
            "name": pd.StringDtype(),
            "nickname": pd.StringDtype(),
            "nationality": pd.CategoricalDtype(),
            "weight_class": pd.CategoricalDtype(),
            "career_earnings": pd.Int64Dtype(),
            "height": pd.Float32Dtype(),
            "reach": pd.Float32Dtype(),
            "head_coach": pd.StringDtype(),
            "last_weigh_in": pd.Float32Dtype(),
            "affiliation.url": pd.StringDtype(),
            "affiliation.id": pd.StringDtype(),
            "affiliation.name": pd.StringDtype(),
            "college": pd.StringDtype(),
        }
    )
    df_fighters = df_fighters.drop(["results"], axis=1)
    df_fighters["date_of_birth"] = pd.to_datetime(
        df_fighters["date_of_birth"], format="%Y-%m-%d"
    )
    df_fighters["nationality"] = (
        df_fighters["nationality"].cat.add_categories(["unknown"]).fillna("unknown")
    )
    df_fighters["height"] = df_fighters.groupby("weight_class", observed=True)[
        "height"
    ].transform(lambda x: x.fillna(x.mean()))
    df_fighters["reach"] = df_fighters.groupby("weight_class", observed=True)[
        "reach"
    ].transform(lambda x: x.fillna(x.mean()))
    target_columns = [
        col for col in df_fighters.columns if col.startswith("career_record")
    ]
    df_fighters[target_columns] = df_fighters[target_columns].astype(pd.Int16Dtype())
    df_fighters[target_columns] = df_fighters[target_columns].fillna(0)
    df_fighters.info()

    # Dataframe of results
    df_results = (
        pd.json_normalize(
            jsondata,
            "results",
            ["id"],
            errors="ignore",
        )
        .astype(
            {
                "division": pd.CategoricalDtype(),
                "status": pd.CategoricalDtype(),
                "billing": pd.CategoricalDtype(),
                "opponent.name": pd.StringDtype(),
                "opponent.url": pd.StringDtype(),
                "opponent.id": pd.StringDtype(),
                "opponent.record.w": pd.Int16Dtype(),
                "opponent.record.l": pd.Int16Dtype(),
                "opponent.record.d": pd.Int16Dtype(),
                "record.w": pd.Int16Dtype(),
                "record.l": pd.Int16Dtype(),
                "record.d": pd.Int16Dtype(),
                "ended_by.type": pd.CategoricalDtype(),
                "ended_by.detail": pd.CategoricalDtype(),
                "weight.is_open": pd.BooleanDtype(),
                "weight.is_catch": pd.BooleanDtype(),
                "weight.class": pd.CategoricalDtype(),
                "weight.limit": pd.Float32Dtype(),
                "weight.weigh_in": pd.Float32Dtype(),
                "ended_at.round": pd.Int16Dtype(),
                "promotion.url": pd.StringDtype(),
                "promotion.id": pd.StringDtype(),
                "age": pd.Int16Dtype(),
                "odds": pd.Float32Dtype(),
                "title_info.name": pd.StringDtype(),
                "title_info.type": pd.CategoricalDtype(),
                "referee": pd.CategoricalDtype(),
                "title_info.as": pd.CategoricalDtype(),
                "id": pd.StringDtype(),
            }
        )
        .rename(columns={"id": "fighter_id"})
    )
    df_results.info()


if __name__ == "__main__":
    main()
