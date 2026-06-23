import argparse

def create_base_parser(description: str) -> argparse.ArgumentParser:
    """Creates an ArgumentParser preconfigured with the standard --data_folder argument."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--data_folder',
        type=str,
        default='../scraping/data/ewondo',
        help='Path to the data folder containing the scraped/processed files.'
    )
    return parser

def add_granularity_arguments(parser: argparse.ArgumentParser, include_verse: bool = False, include_preprocessor: bool = False):
    """Adds standard --book and --chapter arguments, and optionally --verse and --preprocessor."""
    parser.add_argument(
        '--book',
        type=str,
        default=None,
        help='Specific book to process (e.g., MAT).'
    )
    parser.add_argument(
        '--chapter',
        type=str,
        default=None,
        help='Specific chapter to process (e.g., MAT_1). Must be used with --book.'
    )
    if include_verse:
        parser.add_argument(
            '--verse',
            type=str,
            default=None,
            help='Specific verse to process (e.g., V_1).'
        )
    if include_preprocessor:
        parser.add_argument(
            '--preprocessor',
            type=str,
            default=None,
            help='Specific preprocessor workload (e.g., pre_processor_1).'
        )
