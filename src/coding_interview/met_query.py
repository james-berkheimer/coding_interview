import asyncio

import aiohttp
import requests
from aiohttp.client_exceptions import ClientConnectorError
from asyncio_throttle import Throttler
from tenacity import retry, stop_after_attempt, wait_fixed


class InvalidInputError(Exception):
    """Raised when the input to a function is not as expected."""

    pass


class MetQuery:
    """
    A class used to query the Met Museum's collection API.

    ...

    Attributes
    ----------
    collections_endpoint : str
        the endpoint to query the Met Museum's collection API
    use_async : bool
        a flag indicating whether to use async or sync requests
    throttler : Throttler
        a throttler to limit the rate of requests

    Methods
    -------
    handle_response(response)
        Handles the response from the API.
    fetch_object_data_async(object_id, semaphore)
        Fetches the data for a specific object asynchronously.
    fetch_object_data_sync(object_id)
        Fetches the data for a specific object synchronously.
    fetch_object_data(object_id, semaphore=None)
        Fetches the data for a specific object.
    fetch_objects_total()
        Fetches the total number of objects in the collection.
    parse_ids(id_input)
        Parses the input IDs.
    fetch_and_process_async(obj, query_results, search_string, semaphore)
        Fetches and processes the data for a specific object asynchronously.
    fetch_and_process_sync(obj, query_results, search_string)
        Fetches and processes the data for a specific object synchronously.
    fetch_and_process(obj, query_results, search_string, semaphore=None)
        Fetches and processes the data for a specific object.
    query_by_classification_async(id_input=None, limit=None, search_string=None, ascending=True)
        Queries the collection by classification asynchronously.
    query_by_classification_sync(id_input=None, limit=None, search_string=None, ascending=True)
        Queries the collection by classification synchronously.
    query_by_classification(id_input=None, limit=None, search_string=None, ascending=True)
        Queries the collection by classification.
    """

    collections_endpoint = (
        "https://collectionapi.metmuseum.org/public/collection/v1/objects"
    )

    def __init__(self, use_async=False):
        """Initializes the MetQuery class."""
        self.use_async = use_async
        if self.use_async:
            self.throttler = Throttler(rate_limit=40)  # Limit to 40 requests per second

    @staticmethod
    def handle_response(response):
        """Handles the response from the API."""
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 502:
            print("Error: The server is currently unavailable. Please try again later.")
            return None
        else:
            print(f"Error: {response.status_code}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def fetch_object_data_async(self, object_id, semaphore):
        """Fetches the data for a specific object asynchronously."""
        url = f"{self.collections_endpoint}/{object_id}"
        async with semaphore, self.throttler:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        return await response.json()
            except ClientConnectorError:
                print(
                    f"Failed to connect to host for object ID: {object_id}. Retrying..."
                )
                raise

    def fetch_object_data_sync(self, object_id):
        """Fetches the data for a specific object synchronously."""
        url = f"{self.collections_endpoint}/{object_id}"
        try:
            response = requests.get(url)
            return self.handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to host for object ID: {object_id}. Retrying...")
            raise

    def fetch_object_data(self, object_id, semaphore=None):
        """Fetches the data for a specific object."""
        if self.use_async:
            return self.fetch_object_data_async(object_id, semaphore)
        else:
            return self.fetch_object_data_sync(object_id)

    @classmethod
    def fetch_objects_total(self):
        """Fetches the total number of objects in the collection."""
        url = f"{self.collections_endpoint}"
        response = requests.get(url)
        data = self.handle_response(response)
        return data.get("total")

    @classmethod
    def parse_ids(self, id_input):
        """Parses the input IDs."""
        if id_input == 0 or id_input is None:
            total_objects = self.fetch_objects_total()
            return iter(range(1, total_objects + 1))
        elif isinstance(id_input, int):
            return iter([id_input])
        elif isinstance(id_input, str):

            def gen_ids_from_str():
                for part in id_input.split(","):
                    part = part.strip()
                    if "-" in part:
                        start, end = map(int, part.split("-"))
                        yield from range(start, end + 1)
                    else:
                        yield int(part)

            return gen_ids_from_str()
        elif isinstance(id_input, list):
            return iter(id_input)
        else:
            raise InvalidInputError("Invalid input type. Expected int, str, or list.")

    async def fetch_and_process_async(
        self, obj, query_results, search_string, semaphore, limit=None
    ):
        """
        Fetches and processes the data for a specific object asynchronously.

        Parameters:
        obj (int): The object ID.
        query_results (asyncio.Queue): The queue to append the query results to.
        search_string (str): The search string to match in the classification.
        semaphore (asyncio.Semaphore): The semaphore to limit the number of concurrent requests.
        limit (int, optional): The limit on the number of results. Defaults to None.
        """
        if limit is not None and query_results.qsize() >= limit:
            return

        data = await self.fetch_object_data(obj, semaphore)
        if data is None:
            print(f"Failed to fetch data for object ID: {obj}")
            return

        primary_image = data.get("primaryImage")
        primary_image_small = data.get("primaryImageSmall")
        additional_images = data.get("additionalImages")
        classification = data.get("classification")

        if (
            (primary_image or primary_image_small or additional_images)
            and classification
            and (search_string in classification)
        ):
            if limit is None or query_results.qsize() < limit:
                await query_results.put(data)

        await asyncio.sleep(0.5)  # Add a delay of seconds between each request

    def fetch_and_process_sync(self, obj, query_results, search_string, limit=None):
        """
        Fetches and processes the data for a specific object synchronously.

        Parameters:
        obj (int): The object ID.
        query_results (list): The list to append the query results to.
        search_string (str): The search string to match in the classification.
        limit (int, optional): The limit on the number of results. Defaults to None.
        """
        if limit is not None and len(query_results) >= limit:
            return
        data = self.fetch_object_data(obj)
        if data is None:
            print(f"Failed to fetch data for object ID: {obj}")
            return

        primary_image = data.get("primaryImage")
        primary_image_small = data.get("primaryImageSmall")
        additional_images = data.get("additionalImages")
        classification = data.get("classification")

        if (
            (primary_image or primary_image_small or additional_images)
            and classification
            and (search_string in classification)
        ):
            query_results.append(data)

    def fetch_and_process(self, obj, query_results, search_string, semaphore=None):
        """
        Fetches and processes the data for a specific object.

        Parameters:
        obj (int): The object ID.
        query_results (list): The list to append the query results to.
        search_string (str): The search string to match in the classification.
        semaphore (asyncio.Semaphore, optional): The semaphore to limit the number of concurrent requests. Defaults to None.
        """
        if self.use_async:
            return self.fetch_and_process_async(
                obj, query_results, search_string, semaphore
            )
        else:
            return self.fetch_and_process_sync(obj, query_results, search_string)

    import asyncio

    async def query_by_classification_async(
        self, id_input=None, limit=None, search_string=None, ascending=True
    ):
        """
        Queries the collection by classification asynchronously.

        Parameters:
        id_input (int, optional): The input ID. Defaults to None.
        limit (int, optional): The limit on the number of results. Defaults to None.
        search_string (str, optional): The search string to match in the classification. Defaults to None.
        ascending (bool, optional): Whether to sort the results in ascending order. Defaults to True.
        """
        if id_input is None:
            id_input = self.fetch_objects_total()
        ids = self.parse_ids(id_input)

        # Create an asyncio Queue with maxsize equal to limit
        query_results = asyncio.Queue(maxsize=limit)

        semaphore = asyncio.Semaphore(40)  # Limit to 40 requests per second
        await asyncio.gather(
            *(
                self.fetch_and_process_async(
                    obj, query_results, search_string, semaphore, limit
                )
                for obj in ids
            )
        )

        # Get the results from the queue
        results = []
        while not query_results.empty():
            results.append(await query_results.get())

        results.sort(key=lambda x: x.get("objectBeginDate"), reverse=not ascending)

        return results

    def query_by_classification_sync(
        self, id_input=None, limit=None, search_string=None, ascending=True
    ):
        """
        Queries the collection by classification synchronously.

        Parameters:
        id_input (int, optional): The input ID. Defaults to None.
        limit (int, optional): The limit on the number of results. Defaults to None.
        search_string (str, optional): The search string to match in the classification. Defaults to None.
        ascending (bool, optional): Whether to sort the results in ascending order. Defaults to True.
        """
        if id_input is None:
            id_input = self.fetch_objects_total()
        ids = self.parse_ids(id_input)
        query_results = []

        for obj in ids:
            if limit is not None and len(query_results) >= limit:
                break
            self.fetch_and_process(obj, query_results, search_string)

        query_results.sort(
            key=lambda x: x.get("objectBeginDate"), reverse=not ascending
        )

        return query_results

    def query_by_classification(
        self, id_input=None, limit=None, search_string=None, ascending=True
    ):
        """
        Queries the collection by classification.

        Parameters:
        id_input (int, optional): The input ID. Defaults to None.
        limit (int, optional): The limit on the number of results. Defaults to None.
        search_string (str, optional): The search string to match in the classification. Defaults to None.
        ascending (bool, optional): Whether to sort the results in ascending order. Defaults to True.
        """
        if self.use_async:
            return self.query_by_classification_async(
                id_input, limit, search_string, ascending
            )
        else:
            return self.query_by_classification_sync(
                id_input, limit, search_string, ascending
            )
