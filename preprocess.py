import pandas as pd
import numpy as np
import click
import json
import os


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
    print(json_dir)
    print(out_dir)
    pass


def count_nan(x: pd.Series | pd.DataFrame) -> int:
    if isinstance(x, pd.Series):
        return x.isnull().sum()
    return x.isnull().sum().sum()


if __name__ == "__main__":
    main()
