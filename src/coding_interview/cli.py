import asyncio
import json
import time

import click

from .met_query import MetQuery


@click.command()
def print_total_objects():
    """
    Prints the total number of objects in the MetQuery.
    """
    met_query = MetQuery()
    try:
        total_objects = met_query.fetch_objects_total()
        print(f"Total objects: {total_objects}")
    except Exception as e:
        print(f"An error occurred: {e}")


@click.group()
def met_cli():
    """
    Command line interface for MetQuery.
    """
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
    """
    Fetches and prints classifications based on the provided parameters.

    Parameters:
    id_input (str): The input IDs to search for.
    limit (int): The limit on the number of results.
    search_string (str): The search string for classification.
    ascending (bool): The order of date of creation.
    debug (bool): Whether to print debug information.
    use_async (bool): Whether to use async execution.
    """
    start_time = time.time()
    try:
        if use_async:
            asyncio.run(_classifications(id_input, limit, search_string, ascending))
        else:
            met_query = MetQuery(use_async=False)
            results = met_query.query_by_classification(
                id_input, limit, search_string, ascending
            )
            for result in results:
                print(json.dumps(result))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        end_time = time.time()
        if debug:
            print(f"Time taken: {end_time - start_time} seconds")


async def _classifications(id_input, limit, search_string, ascending):
    """
    Fetches and prints classifications asynchronously based on the provided parameters.

    Parameters:
    id_input (str): The input IDs to search for.
    limit (int): The limit on the number of results.
    search_string (str): The search string for classification.
    ascending (bool): The order of date of creation.
    """
    try:
        met_query = MetQuery(use_async=True)
        results = await met_query.query_by_classification(
            id_input, limit, search_string, ascending
        )
        for result in results:
            print(json.dumps(result))
    except Exception as e:
        print(f"An error occurred: {e}")


met_cli.add_command(classifications)

if __name__ == "__main__":
    met_cli()
