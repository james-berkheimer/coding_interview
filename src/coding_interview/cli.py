"""'
NOTES:
https://metmuseum.github.io/#object
https://metmuseum.github.io/#search
https://collectionapi.metmuseum.org/public/collection/v1/objects
"""

import asyncio
import json
import time

import click

from .met_query import MetQuery


@click.command()
def print_total_objects():
    met_query = MetQuery()
    total_objects = met_query.fetch_objects_total()
    print(f"Total objects: {total_objects}")


@click.group()
def met_cli():
    pass


met_cli.add_command(print_total_objects)


@click.command()
@click.option(
    "--id_input",
    default=None,
    help="Input IDs to search for. Can be a single integer (e.g., '5'), a range of integers (e.g., '1-20') a list of integers (e.g., '1, 4, 6, 8'), or 0 for all object IDs.",
)
@click.option(
    "--limit", default=None, type=int, help="Limit the number of results returned."
)
@click.option("--search_string", default=None, help="Search string for classification.")
@click.option("--ascending", default=True, type=bool, help="Order of date of creation.")
@click.option("--debug", default=False, is_flag=True, help="Print debug information.")
@click.option("--use_async", default=False, is_flag=True, help="Use async execution.")
def classifications(id_input, limit, search_string, ascending, debug, use_async):
    start_time = time.time()
    if use_async:
        asyncio.run(_classifications(id_input, limit, search_string, ascending))
    else:
        met_query = MetQuery(use_async=False)
        results = met_query.query_by_classification(
            id_input, limit, search_string, ascending
        )
        for result in results:
            print(json.dumps(result))
    end_time = time.time()
    if debug:
        print(f"Time taken: {end_time - start_time} seconds")


async def _classifications(id_input, limit, search_string, ascending):
    met_query = MetQuery(use_async=True)
    results = await met_query.query_by_classification(
        id_input, limit, search_string, ascending
    )
    for result in results:
        print(json.dumps(result))


met_cli.add_command(classifications)

if __name__ == "__main__":
    met_cli()
