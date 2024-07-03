import os
import requests
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from src.db_connection import get_db_connection
from src.utils.cve_extract_utils import extract_cve_json

load_dotenv()

"""
This function updates the database with new CVEs from the GitHub repository. It uses the following steps:
1. Get recent commits to the repository.
2. Filter the commits to only include those that are new CVEs.
"""
def update_database():
    print("Getting new CVEs and updating database...")

    # Get last update date from database
    db = get_db_connection()
    collection = db['cve']
    last_update = collection.find_one(sort=[("date_public", -1)])['date_public']
    print("Last update date: ", last_update)
    date_obj = datetime.strptime(last_update[:-5] + "Z", "%Y-%m-%dT%H:%M:%SZ")
    day_before = date_obj - timedelta(days=1)
    day_before_str = day_before.strftime("%Y-%m-%dT%H:%M:%SZ")
    print("Day before last update date: ", day_before_str)

    # Get recent commits
    recent_commits = []
    page = 1
    try:
        while page < 1000:
            headers = {
                "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
            }
            response = requests.get(
                f"https://api.github.com/repos/CVEProject/cvelistV5/commits?per_page={100}&page={page}",
                headers=headers
            )
            response.raise_for_status()
            response = json.loads(response.text)
            new_commits = [commit for commit in response if "commit" in commit and commit["commit"]["author"]["date"] > last_update]
            
            if (len(new_commits) < 100):
                break
            recent_commits += new_commits
            page += 1
    except Exception as e:
        raise Exception(f"Error getting recent commits from GitHub: {e}")
    
    # Filter commits to only include those that update or add new CVEs, not other types of commits
    new_cves = [_get_new_cve(commit) for commit in recent_commits]
    new_cves = [cve for cve_list in new_cves for cve in cve_list]
    updated_cves = [_get_updated_cve(commit) for commit in recent_commits]
    updated_cves = [cve for cve_list in updated_cves for cve in cve_list]

    # Remove duplicates
    new_cves = list(set(new_cves))
    updated_cves = list(set(updated_cves))
    print(f"Found {len(new_cves)} new CVEs")
    print(f"Found {len(updated_cves)} updated CVEs")

    # Fetch CVEs based on commit
    failed_cves = []
    new_cve_jsons = []
    for i in range(0, len(new_cves), 100):
        cve_jsons_batch = new_cves[i:i+100]
        with ThreadPoolExecutor(max_workers=100) as executor:
            cve_jsons_batch = list(executor.map(extract_cve_json, cve_jsons_batch))
            failed_cves += [cve_json for cve_json in cve_jsons_batch if isinstance(cve_json, str)]
            new_cve_jsons += [cve_json for cve_json in cve_jsons_batch if isinstance(cve_json, dict)]

    updated_cve_jsons = []
    for i in range(0, len(updated_cves), 100):
        cve_jsons_batch = updated_cves[i:i+100]
        with ThreadPoolExecutor(max_workers=100) as executor:
            cve_jsons_batch = list(executor.map(extract_cve_json, cve_jsons_batch))
            failed_cves += [cve_json for cve_json in cve_jsons_batch if isinstance(cve_json, str)]
            updated_cve_jsons += [cve_json for cve_json in cve_jsons_batch if isinstance(cve_json, dict)]

    # Replace existing CVEs with updated CVEs
    successful_updates = 0
    for updated_cve in updated_cve_jsons:
        result = collection.replace_one({"cve_id": updated_cve["cve_id"]}, updated_cve)
        if result.matched_count > 0:
            successful_updates += 1
    print(f"Updated {successful_updates}/{len(updated_cve_jsons)} updated CVEs")

    # Add new CVEs to the database
    if new_cve_jsons:  # Ensure there are new CVEs to insert
        insert_result = collection.insert_many(new_cve_jsons)
        successful_inserts = len(insert_result.inserted_ids)
    else:
        successful_inserts = 0
    print(f"Inserted {successful_inserts}/{len(new_cve_jsons)} new CVEs")
    print(f"Failed to fetch {len(failed_cves)} CVEs")
    print(f"Failed CVEs: {failed_cves}")

def _get_new_cve(commit):
    """
    Helper function to get new CVEs from a commit.
    """
    try:
        new_cves_string = commit["commit"]["message"].split('\n')[1]

        # Get number of CVEs from string
        new_cves_substring = new_cves_string.split('new CVEs:')[0]
        new_cves_substring = new_cves_substring.split('-')[1]
        new_cves_substring = new_cves_substring.strip()
        num_new_cves = int(new_cves_substring)

        # Get list of CVEs from string
        new_cves_substring = new_cves_string.split('new CVEs:')[1]
        new_cves = new_cves_substring.split(',')
        new_cves = [cve.strip() for cve in new_cves]
        new_cves = [cve for cve in new_cves if cve.startswith('CVE-')]

        if len(new_cves) != num_new_cves:
            raise Exception("Number of new CVEs does not match number of CVEs in list")
        return new_cves
        
    except:
        return []
    
def _get_updated_cve(commit):
    """
    Helper function to get updated CVEs from a commit.
    """
    try:
        updated_cves_string = commit["commit"]["message"].split('\n')[2]

        # Get number of CVEs from string
        updated_cves_substring = updated_cves_string.split('updated CVEs:')[0]
        updated_cves_substring = updated_cves_substring.split('-')[1]
        updated_cves_substring = updated_cves_substring.strip()
        num_updated_cves = int(updated_cves_substring)

        # Get list of CVEs from string
        updated_cves_substring = updated_cves_string.split('updated CVEs:')[1]
        updated_cves = updated_cves_substring.split(',')
        updated_cves = [cve.strip() for cve in updated_cves]
        updated_cves = [cve for cve in updated_cves if cve.startswith('CVE-')]

        if len(updated_cves) != num_updated_cves:
            raise Exception("Number of updated CVEs does not match number of CVEs in list")
        return updated_cves
        
    except:
        return []
    