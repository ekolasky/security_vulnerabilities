# Searchable CVE (Common Vulnerabilities and Exposures) Feed
This API gives the user access to a feed of recently discovered security vulnerabilities. This feed is searchable either by giving a list of filters and sorting parameters, or by using a natural language search.

## Table of Contents
- [How to run](#how-to-run)
- [API Documentation](#api-documentation)
- [Document Schema](#document-schema)
- [Run Tests](#run-tests)

## How to run
The code is running on a Heroku server which can be accessed at this address: https://searchable-cve-feed.herokuapp.com/ Please access the API using the POST endpoint described in the API Documentation section below.

**Alternatively you can run the server locally by doing the following:**

To run you must first initialize a MongoDB database and put the username and password in the .env file. The .env file should also have your API key for OpenAI and GitHub. It should be formatted as follows:
```bash
MONGODB_USERNAME=FILL-IN
MONGODB_PASSWORD=FILL-IN
MONGODB_CLUSTER_URL=FILL-IN
GITHUB_TOKEN=FILL-IN
OPENAI_API_KEY=FILL-IN
```

Then you must upload the CVEs to the MongoDB database. You can do so by running the following script:
```bash
python -m scripts.initialize_db
```
To start the API, you can use the following command:
```bash
python -m src.main
```

## API Documentation

### `POST /search/` Endpoint
This endpoint allows the user to search for CVEs. It allows the user to either filter and sort the database by manually providing filter and sorting parameters, or to search the database using natural language search. The natural language search uses an LLM to create a set of database filters to return the relevant results. It does not use a vector database. If you provide a query and filter parameters, the query will be override the filter parameters.

**Request body format:**
```json
{
    "filter_params": ["LIST OF PARAMETERS TO FILTER WITH"],
    "sort_params": ["LIST OF PARAMETERS TO FILTER WITH"],
    "query": "NATURAL LANGUAGE SEARCH",
    "return_n": "NUMBER OF RESULTS TO RETURN; UP TO 100; DEFAULT 100",
    "return_offset": "OFFSET OF RESULTS; DEFAULT 0"
}
```

**Filter Parameters:**
Each element in the filter parameters list has the format given below. "included_range" requires all results to be within the range, including values equal to the max or min. If "min" or "max" are left out they are assumed to be 0 of inf respectively. "included_values" excludes all results where the parameter value does not fall within the list. It's important to note that parameters with values like "LOW, MEDIUM, HIGH" are treated as a range rather than a value list. "included_range" and "included_values" cannot be both applied for the same parameter.
```json
{
    "parameter": "PARAMETER TO FILTER BY",
    "included_range": {
        "min": "MIN OF RANGE",
        "max": "MAX OF RANGE"
    },
    "included_values": ["LIST OF PARAMETER VALUES TO INCLUDE"]
}
```
Here's a list of parameters that can be used in the filters, along with whether you should use "included_range" or "included_values" for each one. Possible values for each parameter are given in the schema section below. The parameters are as follows:
- `cve_id`: "included_values"
- `date_public`: "included_range"
- `product`: "included_values"
- `attackComplexity`: "included_range"
- `attackVector`: "included_values"
- `availabilityImpact`: "included_range"
- `baseScore`: "included_range"
- `baseSeverity`: "included_values"
- `confidentialityImpact`: "included_range"
- `privilegesRequired`: "included_values"
- `scope`: "included_values"
- `userInteraction`: "included_values"


**Sorting Parameters**: These determine the order of the returned CVE entries. Possible sorting parameters include:
```json
{
    "parameter": "PARAMETER TO FILTER BY",
    "direction": "low or high"
}
```
Here's a list of possible parameters to use for sorting:
  - `date_public`
  - `attackComplexity`
  - `availabilityImpact`
  - `baseScore`
  - `baseSeverity`
  - `confidentialityImpact`


As mentioned earlier this database is also searchable using a natural language search. Here is an example POST request body for a natural language search:
```json
{
    "query": "Recent high severity vulnerabilities for windows"
}
```

## Document Schema
The MongoDB database contains documents with the following schema:

```json
{
    "cve_id": "CVE ID",
    "date_public": "DATE",
    "description": "STRING",
    "affected_products": [
        {
            "product": "PRODUCT NAME",
            "version": "VERSION",
            "update": "UPDATE"
        }
    ],
    "metrics": {
        "attackComplexity": "LOW, HIGH",
        "attackVector": "NETWORK, ADJACENT_NETWORK, LOCAL, PHYSICAL",
        "availabilityImpact": "NONE, LOW, HIGH",
        "baseScore": "0-10",
        "baseSeverity": "NONE, LOW, MEDIUM, HIGH, CRITICAL",
        "confidentialityImpact": "NONE, LOW, HIGH",
        "integrityImpact": "NONE, LOW, HIGH",
        "privilegesRequired": "NONE, LOW, HIGH",
        "scope": "UNCHANGED, CHANGED",
        "userInteraction": "NONE, REQUIRED",
    }
}
```

## Run Tests
To run the tests, you can first start the API, then open a new terminal and run the following command:
```bash
python ./tests/test_api.py
```

To evaluate the models performance on example natural language queries, you can run evaluate_nl_search.py. This script will output the results of the LLM for each query in the test set. You can then manually label whether you think each output makes sense to get a score for the model.
```bash
python -m tests.evaluate_nl_search
```