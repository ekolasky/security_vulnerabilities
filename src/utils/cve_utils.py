import requests
import json

def get_recent_cve_posts(after_date):
    """
    This function finds recent posts on CVE.
    """
    
    # Get CVE posts from GitHub
    try:
        response = requests.get(f"https://api.github.com/repos/CVEProject/cvelistV5/commits?since={after_date}")
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
        return None
    
    # Get all CVE JSONs
    cve_commits = json.loads(response.text)
    cve_commits = [extract_cve_json_commit(commit) for commit in cve_commits]
    cve_commits = [cve for cve in [commit for commit in cve_commits]]

    return cve_commits

# Convert JSON to desired format
def extract_cve_json_commit(commit):
    if not commit["commit"]["author"]["name"] == "cvelistV5 Github Action":
        return []
    if not commit["commit"]["committer"]["name"] == "cvelistV5 Github Action":
        return []
    
    # If message doesn't include new CVEs then filter out
    message = commit["commit"]["message"]
    message_lines = message.split("\n")
    if len(message_lines) < 2:
        return []
    new_cves_line = message_lines[1]
    new_cves = new_cves_line.split("new CVEs:")[1].split(", ")
    new_cves = [cve.strip() for cve in new_cves if cve != ""]
    if len(new_cves) == 0:
        return []
    
    # Do request to get json for each cve
    cve_jsons = []
    for cve in new_cves:
        try:
            response = requests.get(f"https://cveawg.mitre.org/api/cve/{cve}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print ("Http Error:",errh)
        
        cve_jsons.append(extract_cve_json(cve))

    return cve_jsons

def extract_cve_json(cve_id):
    """
    This function gets the JSON for a specific CVE.
    """
    try:
        response = requests.get(f"https://cveawg.mitre.org/api/cve/{cve_id}")
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
        return cve_id
        
    cve_json = json.loads(response.text)
    cve_json = cve_json["containers"]["cna"]

    # Reformat JSON to desired format (desired format can be found in README)
    final_json = {
        "cve_id": cve_id,
        "description": None,
        "date_public": None,
        "affected_products": None,
        "metrics": None
    }
    
    # Add description
    if "descriptions" in cve_json:
        descriptions = [description for description in cve_json["descriptions"] if description["lang"] == "en" and description["value"] != "n/a"]
        if len(descriptions) > 0:
            final_json["description"] = descriptions[0]["value"]

    # Add date_public
    if "datePublic" in cve_json:
        final_json["date_public"] = cve_json["datePublic"]
    if "providerMetadata" in cve_json and "dateUpdated" in cve_json["providerMetadata"]:
        final_json["date_public"] = cve_json["providerMetadata"]["dateUpdated"]

    # Add affected_systems
    if "affected" in cve_json:
        affected_products = _filter_affected_products(cve_json["affected"], cve_id)
        final_json["affected_products"] = affected_products

    # Add metrics
    if ("metrics" in cve_json):
        acceptable_metrics = ["cvssV3_0", "cvssV3", "cvssV3_1", "cvssV4_0"]
        matching_metrics = [metric for metric in cve_json["metrics"] if any([metric_type in metric for metric_type in acceptable_metrics])]
        if len(matching_metrics) > 0:
            final_json["metrics"] = matching_metrics[0]

    return final_json

def _filter_affected_products(affected_products, cve_id):
    """
    This function filters out affected products that are not useful.
    """
    filtered_affected_products = []
    for affected_product in affected_products:

        if (("vendor" not in affected_product or affected_product["vendor"] == "n/a") and 
            ("product" not in affected_product or affected_product["product"] == "n/a")):
            continue

        filtered_affected_products.append({
            "vendor": affected_product["vendor"] if ("vendor" in affected_product and affected_product["vendor"] != "n/a") else None,
            "product": affected_product["product"] if ("product" in affected_product and affected_product["product"] != "n/a") else None,
            "packageName": affected_product["packageName"] if ("packageName" in affected_product and affected_product["packageName"] != "n/a") else None,
            "versions": [version for version in affected_product["versions"] if version["version"] != "n/a"] if "versions" in affected_product else None,
        })

    return filtered_affected_products