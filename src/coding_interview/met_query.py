import requests
from ratelimit import limits, sleep_and_retry


class MetQuery:
    collections_endpoint = (
        "https://collectionapi.metmuseum.org/public/collection/v1/objects"
    )

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

    @classmethod
    @sleep_and_retry
    @limits(calls=80, period=1)
    def fetch_object_data(self, object_id):
        url = f"{self.collections_endpoint}/{object_id}"
        response = requests.get(url)
        return response.json()

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

    @classmethod
    def query_by_classification(
        self, id_input=None, limit=None, search_string=None, ascending=True
    ):
        if id_input is None:
            id_input = self.fetch_objects_total()
        ids = self.parse_ids(id_input)
        query_results = []

        for obj in ids:
            if limit is not None and len(query_results) >= limit:
                break

            data = self.fetch_object_data(obj)
            if data is None:
                print(f"Failed to fetch data for object ID: {obj}")
                continue

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

        query_results.sort(
            key=lambda x: x.get("objectBeginDate"), reverse=not ascending
        )

        return query_results
