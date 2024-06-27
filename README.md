# Searchable CVE (Common Vulnerabilities and Exposures) Feed
This API gives the user access to both a feed of recently discovered security vulnerabilities. These vulnerabilities are detected by an agent that reads online forums and pages that discuss security vulnerabilities.

## How to run
To run you must first initialize a MongoDB database and put the username and password in the .env file.

Then you must upload the CVEs to the MongoDB database. You can do so by running the following script:
```bash
python -m scripts.initialize_db
```
To run the server, you can use the following command:
```bash
python -m src.main
```

## How does it work?
At set intervals the server detects recent CVE posts and saves them to the database. The server displays these in a feed of recent events. The database is also searchable either by providing a list of filters and sorting params or using a natural language search.

NOTE: Alot of the CVEs do not include metrics (eg things like severity). These CVEs seem to be less common and less of a threat. That being said requests that filter by metrics will not return CVEs without metrics.

### `POST /search/` Endpoint

**Request body format:**
```json
{
    "filter_params": ["LIST OF PARAMETERS TO FILTER WITH"],
    "sort_params": ["LIST OF PARAMETERS TO FILTER WITH"],
    "query": "NATURAL LANGUAGE SEARCH",
    "return_n": "NUMBER OF RESULTS TO RETURN; UP TO 100",
    "return_offset": "OFFSET OF RESULTS"
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
Here's a list of parameters that can be used in the filters, along with whether you should use "included_range" or "included_values" for each one:
- `cve_id`: "included_values"
- `date_public`: "included_range"
- `affected_products.product`: "included_values"
- `affected_products.version`: "included_values"
- `affected_products.update`: "included_values"
- `metrics.attackComplexity`: "included_range"
- `metrics.attackVector`: "included_values"
- `metrics.availabilityImpact`: "included_range"
- `metrics.baseScore`: "included_range"
- `metrics.baseSeverity`: "included_values"
- `metrics.confidentialityImpact`: "included_range"
- `metrics.privilegesRequired`: "included_values"
- `metrics.scope`: "included_values"
- `metrics.userInteraction`: "included_values"


**Sorting Parameters**: Determine the order of the returned CVE entries. Possible sorting parameters include:
```json
{
    "parameter": "PARAMETER TO FILTER BY",
    "direction": "low or high"
}
```
  - `date_public`
  - `attackComplexity`
  - `availabilityImpact`
  - `baseScore`
  - `baseSeverity`
  - `confidentialityImpact`

Possible Sorting Parameters: Recency, attackComplexity, availabilityImpact, baseScore, baseSeverity, confidentialityImpact


It is also searchable via a natural language search, such as the following:

```text
"Recent high severity vulnerabilities for windows"
```

This search is converted into a database filter via an LLM and then used to return matching results. The LLM also includes "priority" parameters which prioritize CVEs it thinks are most relevant for the user.

## CVE Schema
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