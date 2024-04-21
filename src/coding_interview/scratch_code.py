from .met_query import MetQuery


def query1():
    met_query = MetQuery()
    search_range = [7829, 9367, 13737, 13740, 14054, 14056, 14081, 14086, 14098, 14101]
    result = met_query.query_collection(search_range, limit=5, search_string="Textiles")
    for i in result:
        print(f'Title: {i.get("title")}')
        print(f'Classification: {i.get("classification")}')
        print(f"Date: {i.get('objectBeginDate')}")
        print("-" * 80)  # prints a separator line of dashes


def query2():
    met_query = MetQuery()
    # pprint(fetch_object_data(7829))
    # print(parse_ids("1-5, 7, 9-10, 12"))
    # for i in parse_ids([1, 5, 8, 10]):
    #     print(i)
    # print(parse_ids(100))
    # print(parse_ids(100))
    print(met_query.fetch_objects_total())
