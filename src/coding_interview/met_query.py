import asyncio

import aiohttp
import requests
from aiohttp.client_exceptions import ClientConnectorError
from asyncio_throttle import Throttler
from tenacity import retry, stop_after_attempt, wait_fixed


class MetQuery:
    collections_endpoint = (
        "https://collectionapi.metmuseum.org/public/collection/v1/objects"
    )

    def __init__(self, use_async=False):
        self.use_async = use_async
        if self.use_async:
            self.throttler = Throttler(rate_limit=40)  # Limit to 40 requests per second

    @staticmethod
    def handle_response(response):
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
        url = f"{self.collections_endpoint}/{object_id}"
        try:
            response = requests.get(url)
            return self.handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to host for object ID: {object_id}. Retrying...")
            raise

    def fetch_object_data(self, object_id, semaphore=None):
        if self.use_async:
            return self.fetch_object_data_async(object_id, semaphore)
        else:
            return self.fetch_object_data_sync(object_id)

    @classmethod
    def fetch_objects_total(self):
        url = f"{self.collections_endpoint}"
        response = requests.get(url)
        data = self.handle_response(response)
        return data.get("total")

    @classmethod
    def parse_ids(self, id_input):
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
            raise ValueError("Invalid input type. Expected int, str, or list.")

    async def fetch_and_process_async(
        self, obj, query_results, search_string, semaphore
    ):
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
            query_results.append(data)

        await asyncio.sleep(0.5)  # Add a delay of seconds between each request

    def fetch_and_process_sync(self, obj, query_results, search_string):
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
        if self.use_async:
            return self.fetch_and_process_async(
                obj, query_results, search_string, semaphore
            )
        else:
            return self.fetch_and_process_sync(obj, query_results, search_string)

    async def query_by_classification_async(
        self, id_input=None, limit=None, search_string=None, ascending=True
    ):
        if id_input is None:
            id_input = self.fetch_objects_total()
        ids = self.parse_ids(id_input)
        query_results = []

        semaphore = asyncio.Semaphore(40)  # Limit to 40 requests per second
        await asyncio.gather(
            *(
                self.fetch_and_process(obj, query_results, search_string, semaphore)
                for obj in ids
            )
        )

        query_results.sort(
            key=lambda x: x.get("objectBeginDate"), reverse=not ascending
        )

        return query_results

    def query_by_classification_sync(
        self, id_input=None, limit=None, search_string=None, ascending=True
    ):
        if id_input is None:
            id_input = self.fetch_objects_total()
        ids = self.parse_ids(id_input)
        query_results = []

        for obj in ids:
            self.fetch_and_process(obj, query_results, search_string)

        query_results.sort(
            key=lambda x: x.get("objectBeginDate"), reverse=not ascending
        )

        return query_results

    def query_by_classification(
        self, id_input=None, limit=None, search_string=None, ascending=True
    ):
        if self.use_async:
            return self.query_by_classification_async(
                id_input, limit, search_string, ascending
            )
        else:
            return self.query_by_classification_sync(
                id_input, limit, search_string, ascending
            )
