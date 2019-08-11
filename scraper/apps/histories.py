"""
A script to save a history CSVs for the date range.
"""
import datetime
import argparse


import scraper.apps.common
import scraper.apis


from scraper.apps.common import yyyy_mm_dd


# noinspection DuplicatedCode
def get_arguments() -> argparse.Namespace:
    """
    Get the command line arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--force', action='store_true', help='force redownload?')
    parser.add_argument('--stub', default='{t0:%Y-%m-%d}-{dt:03d}-histories.csv', type=str)
    parser.add_argument('--t0', default=datetime.datetime.now(tz=datetime.timezone.utc), type=yyyy_mm_dd)
    parser.add_argument('--dt', default=1, type=int, help='number of days after t0 to fetch')
    return parser.parse_args()


if __name__ == '__main__':
    scraper.apps.common.run(scraper.apis.HistoriesScraper.export, get_arguments)
