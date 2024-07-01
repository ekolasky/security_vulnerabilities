import json
import time

# Open parameters json file
with open("src/parameters.json", "r") as f:
    parameters = json.load(f)

def validate_filters(filter_params):
    """
    This function validates the filters parameters. It returns a list of errors with the filters parameters.
    """

    errors = []
    # Validate basic schema of filter params - should be lists with
    if not isinstance(filter_params, list):
        errors.append("Filter parameters should be a list.")
        return errors
    if any(["parameter" not in filter_param or not isinstance(filter_param["parameter"], str) for filter_param in filter_params]):
        errors.append("Filter parameters should have a 'parameter' key, which is a string.")
    if any(["included_range" not in filter_param and "included_values" not in filter_param for filter_param in filter_params]):
        errors.append("Filter parameters need to include either an 'included_range' or 'included_values' key but not both.")
    if any(["included_range" in filter_param and "included_values" in filter_param for filter_param in filter_params]):
        errors.append("Filter parameters cannot include both an 'included_range' and 'included_values' key.")
    
    if (len(errors) > 0):
        return errors

    # Validate basic schema of included_range
    for filter_param in filter_params:
        if "included_range" in filter_param:
            if not isinstance(filter_param["included_range"], dict):
                errors.append("Filter parameters 'included_range' should be a list.")
                return errors
            if "max" not in filter_param["included_range"] and "min" not in filter_param["included_range"]:
                errors.append("Filter parameters 'included_range' should have exactly two elements.")
            
            if (len(errors) > 0):
                return errors

    # Validate basic schema of included_values
    for filter_param in filter_params:
        if "included_values" in filter_param:
            if not isinstance(filter_param["included_values"], list):
                errors.append("Filter parameters 'included_values' should be a list.")
                return errors
            
            if (len(errors) > 0):
                return errors

    # Parameter dependent validation
    # Check that each filter_param is for a valid parameter
    if (any([filter_param["parameter"] not in [x["parameter"] for x in parameters] for filter_param in filter_params])):
        errors.append("Filter parameters need to be included in list of possible parameters.")
        return errors
    
    # Check for duplicate parameters
    if (len(filter_params) != len(set([filter_param["parameter"] for filter_param in filter_params]))):
        errors.append("Filter parameters should not contain duplicates.")
        return errors
    
    # Check that "included_range" or "included_values" is valid for that parameter
    for filter_param in filter_params:
        parameter = [x for x in parameters if x["parameter"] == filter_param["parameter"]][0]
        if "included_range" in filter_param and "filter-range" not in parameter["accepted_operations"]:
            errors.append(f"Parameter {filter_param['parameter']} cannot be filtered by a range.")
        if "included_values" in filter_param and "filter-value" not in parameter["accepted_operations"]:
            errors.append(f"Parameter {filter_param['parameter']} cannot be filtered by values.")
    if (len(errors) > 0):
        return errors
    
    # Check datatypes of included_range
    for filter_param in filter_params:
        parameter = [x for x in parameters if x["parameter"] == filter_param["parameter"]][0]

        # Handle data types for included_range
        if "included_range" in filter_param:
            
            # Handle string-options
            if (parameter["data_type"] == "string-options"):
                if not all([isinstance(val, str) for val in filter_param["included_range"].values()]):
                    errors.append(f"Max and min range values for {filter_param['parameter']} should both be strings.")
                possible_vals = [val.lower() for val in parameter["possible_values"]]
                if (not all([val.lower() in possible_vals for val in filter_param["included_range"].values()])):
                    errors.append(f"Max and min range values for {filter_param['parameter']} should be in the list of options.")                
                if ("min" in filter_param["included_range"] and "max" in filter_param["included_range"] and len(errors) == 0):
                    if (possible_vals.index(filter_param["included_range"]["min"].lower()) >= possible_vals.index(filter_param["included_range"]["max"].lower())):
                        errors.append(f"Min value for {filter_param['parameter']} should be less than max value.")
            
            # Handle iso8601
            if (parameter["data_type"] == "iso8601"):
                if not all([isinstance(val, str) for val in filter_param["included_range"].values()]):
                    errors.append(f"Max and min range values for {filter_param['parameter']} should both be iso8601 strings.")
                
                # Check that the date is in the correct format using time library not datetime
                try:
                    max_time = None
                    min_time = None
                    if "max" in filter_param["included_range"]:
                        max_time = time.strptime(filter_param["included_range"]["max"], "%Y-%m-%dT%H:%M:%SZ")
                    if "min" in filter_param["included_range"]:
                        min_time = time.strptime(filter_param["included_range"]["min"], "%Y-%m-%dT%H:%M:%SZ")
                    if (max_time and min_time and max_time <= min_time):
                        errors.append(f"Min value for {filter_param['parameter']} should be less than max value.")
                except ValueError:
                    errors.append(f"Max and min range values for {filter_param['parameter']} should be in the correct iso8601 format.")

            # Handle numeric, either integer or float are appropriate
            if (parameter["data_type"] == "numeric"):
                if not all([isinstance(val, (int, float)) for val in filter_param["included_range"].values()]):
                    errors.append(f"Max and min range values for {filter_param['parameter']} should both be numeric.")
                    return errors
                if ("min" in filter_param["included_range"] and "max" in filter_param["included_range"]):
                    if (filter_param["included_range"]["min"] >= filter_param["included_range"]["max"]):
                        errors.append(f"Min value for {filter_param['parameter']} should be less than max value.")

        # Handle included_values
        if "included_values" in filter_param:

            # Check if there are multiple duplicate values
            if (len(filter_param["included_values"]) != len(set(filter_param["included_values"]))):
                errors.append(f"Values for {filter_param['parameter']} should not contain duplicates.")

            # Handle string-options
            if (parameter["data_type"] == "string-options"):
                possible_vals = [val.lower() for val in parameter["possible_values"]]
                if (not all([val.lower() in possible_vals for val in filter_param["included_values"]])):
                    errors.append(f"Values for {filter_param['parameter']} should be in the list of options.")

            # Handle string
            if (parameter["data_type"] == "string"):
                if (not all([isinstance(val, str) for val in filter_param["included_values"]])):
                    errors.append(f"Values for {filter_param['parameter']} should be strings.")

    return errors

def validate_sorts(sort_params):
    """
    This function validates the sorting parameters. It returns a list of errors with the sorting parameters.
    """

    errors = []
    # Validate basic schema of filter params
    if not isinstance(sort_params, list):
        errors.append("Sort parameters should be a list.")
    if any(["parameter" not in sort_param or sort_param["parameter"] is None for sort_param in sort_params]):
        errors.append("Sort parameters should all have a 'parameter' key, which is a string.")
    if any(["direction" not in sort_param or sort_param["direction"] is None for sort_param in sort_params]):
        errors.append("Sort parameters should all have a 'direction' key, which is a string.")
    if (len(errors) > 0):
        return errors
    
    # Check that parameters and directions are strings
    if any([not isinstance(sort_param["parameter"], str) for sort_param in sort_params]):
        errors.append("Sort parameters 'parameter' should be a string.")
    if any([not isinstance(sort_param["direction"], str) for sort_param in sort_params]):
        errors.append("Sort parameters 'direction' should be a string.")
    if (len(errors) > 0):
        return errors
    
    # Check for duplicate parameters
    if (len(sort_params) != len(set([sort_param["parameter"] for sort_param in sort_params]))):
        errors.append("Sort parameters should not contain duplicates.")
    
    # Check that directions are either "low" or "high"
    if any([sort_param["direction"] not in ["low", "high"] for sort_param in sort_params]):
        errors.append("Sort parameters 'direction' should be either 'low' or 'high'.")

    # Check that each parameter in sort params is in the list of parameters
    if (any([sort_param["parameter"] not in [x["parameter"] for x in parameters] for sort_param in sort_params])):
        errors.append("Sort parameters need to be included in list of possible parameters.")
    
    if (len(errors) > 0):
        return errors
    
    # Check that the parameter can be sorted
    for sort_param in sort_params:
        parameter = [x for x in parameters if x["parameter"] == sort_param["parameter"]][0]
        if ("sort" not in parameter["accepted_operations"]):
            errors.append(f"Parameter {sort_param['parameter']} cannot be sorted.")

    return errors