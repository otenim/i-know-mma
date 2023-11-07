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
    df = pd.json_normalize(
        jsondata,
        "results",
        [
            "id",
            "nationality",
            "weight_class",
            "reach",
            "height",
            "date_of_birth",
            ["affiliation", "id"],
            "college",
        ],
        errors="ignore",
    )
    df.info()


if __name__ == "__main__":
    main()
