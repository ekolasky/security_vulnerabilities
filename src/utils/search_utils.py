from src.db_connection import get_db_connection
from src.utils.mongo_queries import convert_filter_to_mongo_queries, convert_sort_to_mongo_queries, get_custom_sort_fields
from src.utils.nl_search_utils import initial_request

def handle_nl_search(query, return_n=100, return_offset=0):
    """
    This function takes a natural language search string and returns matching results along with filters and sorting parameters.
    """

    # Make initial model call with query
    initial_request(query)

    # Prompt model with function calling
    # Run function json through validator
    # Take errors and feed them back to model

    # Once there's no errors, retrieve cves



    pass

def retrieve_cves(filter_params, sort_params, return_n=100, return_offset=0):
    """
    This function converts filter_params and sort_params to MongoDB queries and then returns CVEs from the database.
    """

    mongo_filters = convert_filter_to_mongo_queries(filter_params)
    mongo_sorts = convert_sort_to_mongo_queries(sort_params)
    print(mongo_filters)

    db = get_db_connection()
    collection = db['cve']


    # Define custom sort order
    custom_sort_fields = get_custom_sort_fields(sort_params)
    print(mongo_sorts)
    
    # Create pipeline from filters and sorts
    pipeline = [
        {"$addFields": custom_sort_fields},
        {"$match": {"$and": mongo_filters}},
        {"$sort": mongo_sorts},  # Adjust 1 to -1 to reverse the order
        {"$skip": return_offset},
        {"$limit": return_n},
        {"$project": {k: 0 for k in custom_sort_fields.keys()}}  # Optionally remove the customSortField from the results
    ]

    results = list(collection.aggregate(pipeline))

    # results = list(collection.find({
    #     "$and": mongo_filters
    # }).sort(mongo_sorts).skip(return_offset).limit(return_n))

    # Convert ObjectId to string
    for result in results:
        if '_id' in result:
            result['_id'] = str(result['_id'])

    return results


