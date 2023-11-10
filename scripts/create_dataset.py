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


if __name__ == "__main__":
    main()
