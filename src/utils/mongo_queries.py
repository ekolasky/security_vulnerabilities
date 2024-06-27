import json

# Open parameters json file
with open("src/parameters.json", "r") as f:
    parameters = json.load(f)


def convert_filter_to_mongo_queries(filter_params):
    """
    This function converts a list of filter_params to a list of MongoDB search queries.
    """

    # Iterate through all filter params
    mongo_queries = []
    for filter_param in filter_params:

        # Find the parameter in the parameters list
        parameter = [x for x in parameters if x["parameter"] == filter_param["parameter"]][0]

        inner_query = {}
        mongo_query = {}

        # Handle range query when parameter is a string with possible values
        if "included_range" in filter_param and parameter["data_type"] == "string-options":
            min_index = parameter["possible_values"].index(filter_param["included_range"]["min"])
            max_index = parameter["possible_values"].index(filter_param["included_range"]["max"])
            included_values = parameter["possible_values"][min_index:max_index+1]
            inner_query = {
                "attribute": filter_param["parameter"],
                "value": {
                    "$in": included_values
                }
            }
        
        # Handle range query when parameter is a date
        elif "included_range" in filter_param and parameter["data_type"] == "iso8601":
            inner_query = {
                "attribute": filter_param["parameter"],
                "value": {
                    "$gte": filter_param["included_range"]["min"],
                    "$lte": filter_param["included_range"]["max"]
                }
            }

        # Handle range query when parameter is a number
        elif "included_range" in filter_param and parameter["data_type"] == "number":
            inner_query = {
                "attribute": filter_param["parameter"],
                "value": {
                    "$gte": filter_param["included_range"]["min"],
                    "$lte": filter_param["included_range"]["max"]
                }
            }

        # Handle values query when filter_param is a string
        elif "included_values" in filter_param:
            inner_query = {
                "attribute": filter_param["parameter"],
                "value": {
                    "$in": filter_param["included_values"]
                }
            }




        # Handle nesting
        if "nested_in" in parameter and parameter["parent_type"] == "list":
            mongo_query = {
                parameter["nested_in"]: {
                    "$elemMatch": inner_query
                }
            }
        elif "nested_in" in parameter and parameter["parent_type"] == "list":
            mongo_query = {
                f"{parameter["nested_in"]}.{inner_query['attribute']}": inner_query["value"]
            }
        # Handle case where there's no nesting
        else:
            mongo_query = {
                inner_query["attribute"]: inner_query["value"]
            }

        mongo_queries.append(mongo_query)

    return mongo_queries