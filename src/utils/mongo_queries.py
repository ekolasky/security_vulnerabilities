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
            possible_vals = [val.lower() for val in parameter["possible_values"]]
            min_index = possible_vals.index(filter_param["included_range"]["min"].lower()) if "min" in filter_param["included_range"] else None
            max_index = possible_vals.index(filter_param["included_range"]["max"].lower()) if "max" in filter_param["included_range"] else None
            included_values = parameter["possible_values"][min_index:max_index+1] if max_index is not None else parameter["possible_values"][min_index:]
            inner_query = {
                "attribute": filter_param["parameter"],
                "value": {
                    "$in": included_values
                }
            }
        
        # Handle range query when parameter is a date
        elif "included_range" in filter_param and parameter["data_type"] == "iso8601":
            if "min" in filter_param["included_range"] and "max" in filter_param["included_range"]:
                inner_query = {
                    "attribute": filter_param["parameter"],
                    "value": {
                        "$gte": filter_param["included_range"]["min"],
                        "$lte": filter_param["included_range"]["max"]
                    }
                }
            elif "max" in filter_param["included_range"]:
                inner_query = {
                    "attribute": filter_param["parameter"],
                    "value": {
                        "$lte": filter_param["included_range"]["max"]
                    }
                }
            elif "min" in filter_param["included_range"]:
                inner_query = {
                    "attribute": filter_param["parameter"],
                    "value": {
                        "$gte": filter_param["included_range"]["min"]
                    }
                }

        # Handle range query when parameter is a number
        elif "included_range" in filter_param and parameter["data_type"] == "numeric":
            if "min" in filter_param["included_range"] and "max" in filter_param["included_range"]:
                inner_query = {
                    "attribute": filter_param["parameter"],
                    "value": {
                        "$gte": filter_param["included_range"]["min"],
                        "$lte": filter_param["included_range"]["max"]
                    }
                }
            elif "max" in filter_param["included_range"]:
                inner_query = {
                    "attribute": filter_param["parameter"],
                    "value": {
                        "$lte": filter_param["included_range"]["max"]
                    }
                }
            elif "min" in filter_param["included_range"]:
                inner_query = {
                    "attribute": filter_param["parameter"],
                    "value": {
                        "$gte": filter_param["included_range"]["min"]
                    }
                }

        # Handle values query when filter_param is a string
        elif "included_values" in filter_param and parameter["data_type"] == "string":
            if ("substring_search" in parameter and parameter["substring_search"]):
                inner_query = [
                    {
                        "attribute": filter_param["parameter"],
                        "value": {
                            "$regex": f".*{val}.*",
                            "$options": "i"
                        }
                    } for val in filter_param["included_values"]
                ]
            else:
                inner_query = {
                    "attribute": filter_param["parameter"],
                    "value": {
                        "$in": filter_param["included_values"]
                    }
                }

        # Handle values query when filter_param is a string-options
        elif "included_values" in filter_param and parameter["data_type"] == "string-options":
            possible_vals = [val.lower() for val in filter_param["included_values"]]
            included_values = [val for val in parameter["possible_values"] if val.lower() in possible_vals]
            inner_query = {
                "attribute": filter_param["parameter"],
                "value": {
                    "$in": included_values
                }
            }


        # Handle nesting
        if "nested_in" in parameter and parameter["parent_type"] == "list":
            mongo_query = {
                "$or": [
                    {f"{parameter['nested_in']}.{elem['attribute']}": elem["value"]} for elem in inner_query
                ]
            }
        elif "nested_in" in parameter and parameter["parent_type"] == "dict":
            mongo_query = {
                f"{parameter['nested_in']}.{inner_query['attribute']}": inner_query["value"]
            }
        # Handle case where there's no nesting
        else:
            mongo_query = {
                inner_query["attribute"]: inner_query["value"]
            }

        mongo_queries.append(mongo_query)

    return mongo_queries


def convert_sort_to_mongo_queries(sort_params):
    """
    This function converts a list of sort_params to a list of MongoDB sort queries.
    """

    # Iterate through all sort params
    mongo_sorts = {}
    for sort_param in sort_params:
        
        # Find the parameter in the parameters list
        parameter = [x for x in parameters if x["parameter"] == sort_param["parameter"]][0]

        mongo_sort = None

        # If parameter is string-options
        if parameter["data_type"] == "string-options":
            mongo_sort = (f"{sort_param['parameter']}CustomSort", -1 if sort_param["direction"] == "high" else 1)
        # If parameter is iso8601 or numeric
        else:
            if "nested_in" in parameter:
                mongo_sort = (f"{parameter['nested_in']}.{sort_param['parameter']}", -1 if sort_param["direction"] == "high" else 1)
            else:
                mongo_sort = (sort_param["parameter"], -1 if sort_param["direction"] == "high" else 1)

        mongo_sorts[mongo_sort[0]] = mongo_sort[1]

    return mongo_sorts

def get_custom_sort_fields(sort_params=[]):
    """
    This function returns a dictionary of custom sort fields for the database.
    """

    # Get sortable "string-options" parameters
    sortable_params = [x for x in parameters if x["data_type"] == "string-options" and "sort" in x["accepted_operations"]]

    # Create custom sort fields
    sort_fields = {}

    for param in sortable_params:

        # Get branches for param
        branches = []
        for idx, option in enumerate(param["possible_values"]):
            if "nested_in" in param:
                branches.append({"case": {"$eq": [f"${param['nested_in']}.{param['parameter']}", option]}, "then": idx + 1})
            else:
                branches.append({"case": {"$eq": [f"${param['parameter']}", option]}, "then": idx + 1})

        # Set default based on sort direction
        sort_param = [x for x in sort_params if x["parameter"] == param["parameter"]]
        default = 0
        if len(sort_param) > 0 and sort_param[0]["direction"] == "low":
            default = 999
            

        sort_fields[f"{param['parameter']}CustomSort"] = {
            "$switch": {
                "branches": branches,
                "default": default
            }
        }

    return sort_fields