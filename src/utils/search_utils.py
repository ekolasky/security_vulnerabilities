from src.db_connection import get_db_connection

def handle_nl_search(query, return_n=100, return_offset=0):
    """
    This function takes a natural language search string and returns matching results along with filters and sorting parameters.
    """

    # Recurrently correct model if json response doesn't match expected format



    pass

def get_filters_and_sorts(query):
    """
    This function takes a natural language search string and returns a list of filters and sorting parameters.
    """

    pass

def retrieve_cves(mongo_filters, mongo_sorts, return_n=100, return_offset=0):
    """
    This function retrieves CVEs from the MongoDB database based on filters and sorting parameters.
    """

    db = get_db_connection()
    collection = db['cve']

    results = list(collection.find({
        "$and": [
            {"attributes": {"$elemMatch": filter}}
            for filter in mongo_filters
        ]
    }).sort(mongo_sorts).skip(return_offset).limit(return_n))

    return results


