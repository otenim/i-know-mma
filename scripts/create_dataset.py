import pandas as pd
import click
import json


@click.command()
@click.argument(
    "jsonfile", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
def main(jsonfile: str):
    # Load json file
    jsondata = None
    with open(jsonfile) as fp:
        jsondata = json.load(fp)

    # Convert to dataframe
    df = pd.json_normalize(
        jsondata,
        "results",
        [
            "id",
            "nationality",
            "reach",
            "height",
            "date_of_birth",
            ["affiliation", "id"],
            "college",
        ],
        errors="ignore",
    ).astype(
        {
            "id": pd.StringDtype(),
            "nationality": pd.StringDtype(),
            "reach": pd.Float32Dtype(),
            "height": pd.Float32Dtype(),
            "date_of_birth": pd.StringDtype(),
            "affiliation.id": pd.StringDtype(),
            "college": pd.StringDtype(),
            "division": pd.StringDtype(),
            "sport": pd.StringDtype(),
            "status": pd.StringDtype(),
            "date": pd.StringDtype(),
            "opponent.id": pd.StringDtype(),
            "opponent.record.w": pd.Int16Dtype(),
            "opponent.record.l": pd.Int16Dtype(),
            "opponent.record.d": pd.Int16Dtype(),
            "promotion.id": pd.StringDtype(),
            "record.w": pd.Int16Dtype(),
            "record.l": pd.Int16Dtype(),
            "record.d": pd.Int16Dtype(),
            "billing": pd.StringDtype(),
            "referee": pd.StringDtype(),
            "ended_by.type": pd.StringDtype(),
            "ended_by.detail": pd.StringDtype(),
            "ended_at.round": pd.Int16Dtype(),
            "ended_at.time.m": pd.Int16Dtype(),
            "ended_at.time.s": pd.Int16Dtype(),
            "weight.class": pd.StringDtype(),
            "weight.limit": pd.Float32Dtype(),
            "weight.weigh_in": pd.Float32Dtype(),
            "title_info.championship": pd.StringDtype(),
            "title_info.as": pd.StringDtype(),
            "odds": pd.Float32Dtype(),
        }
    )

    # Drop unnecessary columns
    df = df.drop(columns=["opponent.url", "opponent.name", "promotion.url"])

    # Convert date-strings to datetime type
    columns = ["date_of_birth", "date"]
    for column in columns:
        df[column] = pd.to_datetime(df[column], format="%Y-%m-%d")

    # Calculate age at the moment
    df["age"] = ((df["date"] - df["date_of_birth"]) / pd.Timedelta(365, "d")).astype(
        pd.Float32Dtype()
    )

    df.info()


if __name__ == "__main__":
    main()
