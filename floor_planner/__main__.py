"""
Render project.

"""


import argparse

from floor_planner.runner import run_project


def parse_cli_args() -> argparse.Namespace:
    """
    Parse arguments passed via Command Line Interface (CLI).

    :return:
        namespace with arguments
    """
    parser = argparse.ArgumentParser(description='Rendering of renovation project floor plans.')
    parser.add_argument(
        '-c', '--config_path', type=str, default=None, help='path to configuration file'
    )
    cli_args = parser.parse_args()
    return cli_args


def main() -> None:
    """Parse CLI arguments and run the project."""
    cli_args = parse_cli_args()
    run_project(cli_args.config_path)


if __name__ == '__main__':
    main()
