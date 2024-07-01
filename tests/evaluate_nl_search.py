import json
from src.utils.search_utils import handle_nl_search

def evaluate_nl_search():
    """
    Function runs the queries provided in test_set and returns the filter and sort params. It then prompt the user to returm
    "T" if the filter and sort params are correct and "F" if they are incorrect. In some cases the model will return errors, and 
    these will be recorded as a different case. At the end a percent score is given based on the number of correct responses.
    """

    with open('tests/test_set.json') as f:
        test_set = json.load(f)

    score = 0
    failed = 0
    for test in test_set:
        print("------------------------------------")
        print("Query: ", test['query'])

        output = handle_nl_search(test["query"], 5, 0)

        if ('errors' in output):
            print("Errors: ", output['errors'])
            failed += 1
        elif "results" not in output or len(output["results"]) < 5:
            print("Fewer than five results returned.")
        else:
            print("Filter Params: ", json.dumps(output['filter_params'], indent=4))
            print("Sort Params: ", json.dumps(output['sort_params'], indent=4))

            response = input("Correct? (T/F): ")
            if response == "T":
                score += 1
    
    print("------------------------------------")
    print("Score: ", score, "/", len(test_set))
    print("Failed: ", failed , "/", len(test_set))


if __name__ == "__main__":
    evaluate_nl_search()