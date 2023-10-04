import pandas as pd

EMBER_CSV_LINK = (
    "https://ember-climate.org/app/uploads/2022/07/yearly_full_release_long_format.csv"
)


def fetch_capacities(link: str) -> pd.DataFrame:
    """
    Fetches the capacities from the EMBER dataset.
    """
    df = pd.read_csv(link)


if __name__ == "__main__":
    fetch_capacities(EMBER_CSV_LINK)
