import pandas as pd
import click
import json
from sklearn.preprocessing import LabelEncoder


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
    )
    df_fighters.info()


if __name__ == "__main__":
    main()
