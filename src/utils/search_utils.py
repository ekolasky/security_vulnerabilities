import json

from src.db_connection import get_db_connection
from src.utils.mongo_queries import convert_filter_to_mongo_queries, convert_sort_to_mongo_queries, get_custom_sort_fields
from src.utils.nl_search_utils import initial_request, reprompt_with_errors
from src.utils.search_validators import validate_filters, validate_sorts


def handle_nl_search(query, return_n=100, return_offset=0):
    """
    This function takes a natural language search string and returns matching results along with filters and sorting parameters.
    """

    # Make initial model call with query
    messages = initial_request(query)
    errors, json_response = _get_response_errors(messages[-1]['content'])

    # Reprompt to correct errors
    i = 0
    while len(errors) > 0 and i < 5:
        messages = reprompt_with_errors(messages, errors)
        errors, json_response = _get_response_errors(messages[-1]['content'])
        i += 1

    if len(errors) == 0:
        cves = retrieve_cves(json_response['filter_params'], json_response['sort_params'], return_n, return_offset)
        return {**json_response, 'results': cves}
    else:
        return {'errors': errors}
    

def _get_response_errors(response):

    try:
        # Clean response
        if "```json" in response:
            response = response.split("```json")[1]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        json_response = json.loads(response)

    except json.JSONDecodeError:
        return (["Please return a JSON function call that searches the database to answer the user's search."], None)

    # Check for errors
    errors = []
    if 'filter_params' not in json_response or 'sort_params' not in json_response:
        errors.append('Either "filter_params" and "sort_params" must be provided, or "query" must be provided')
    else:
        errors += validate_filters(json_response['filter_params'])
        errors += validate_sorts(json_response['sort_params'])
    
    return (errors, json_response)


def retrieve_cves(filter_params, sort_params, return_n=100, return_offset=0):
    """
    This function converts filter_params and sort_params to MongoDB queries and then returns CVEs from the database.
    """

    mongo_filters = convert_filter_to_mongo_queries(filter_params)
    mongo_sorts = convert_sort_to_mongo_queries(sort_params)

    # If no sorts are provided, default to sorting by date
    if (len(mongo_sorts) == 0):
        mongo_sorts = {"date_public": -1}

    db = get_db_connection()
    collection = db['cve']


    # Define custom sort order
    custom_sort_fields = get_custom_sort_fields(sort_params)
    
    # Create pipeline from filters and sorts
    pipeline = [
        {"$addFields": custom_sort_fields}
    ]

    if len(mongo_filters) > 0:
        pipeline.append({"$match": {"$and": mongo_filters}})

    print(mongo_sorts)
    pipeline += [
        {"$sort": mongo_sorts},
        {"$skip": return_offset},
        {"$limit": return_n},
        {"$project": {k: 0 for k in custom_sort_fields.keys()}}
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