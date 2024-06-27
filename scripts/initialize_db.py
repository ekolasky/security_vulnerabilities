import os
import requests
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

from src.db_connection import get_db_connection
from src.utils.cve_utils import extract_cve_json

load_dotenv()

def upload_all_cves_to_mongo():
    """
    This function uploads all CVEs to the MongoDB database.
    """
    db = get_db_connection()
    collection = db['cve']

    # Get all year folders
    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
        }
        response = requests.get(f"https://api.github.com/repos/CVEProject/cvelistV5/contents/cves", headers=headers)
        response.raise_for_status()
        response = json.loads(response.text)
        year_folders = [obj["name"] for obj in response if obj["type"] == "dir"]
    except Exception as e:
        raise Exception(f"Error getting year folders from CVE repo: {e}")

    # Iterate through all year folders
    num_cves = 0
    failed_cves = []
    metrics = {
        "missing_descriptions": 0,
        "missing_dates": 0,
        "missing_affected_products": 0,
        "missing_metrics": 0
    }
    for year_folder in [year_folders[-20]]:

        # Get all subfolders in year folder
        try:
            headers = {
                "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
            }
            response = requests.get(f"https://api.github.com/repos/CVEProject/cvelistV5/contents/cves/{year_folder}", headers=headers)
            response.raise_for_status()
            response = json.loads(response.text)
            subfolders = [obj["name"] for obj in response if obj["type"] == "dir"]
        except Exception as e:
            raise Exception(f"Error getting subfolders from year folder {year_folder}: {e}")
        
        # Get all json CVEs from subfolder and upload contents to MongoDB
        for subfolder in subfolders:
            try:
                # Add personal token to request
                headers = {
                    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
                }
                response = requests.get(f"https://api.github.com/repos/CVEProject/cvelistV5/contents/cves/{year_folder}/{subfolder}", headers=headers)
                
                response.raise_for_status()
                response = json.loads(response.text)
                cve_jsons = [obj["name"][:-5] for obj in response if obj["name"].endswith(".json")]

            except Exception as e:
                raise Exception(f"Error getting json CVEs from subfolder {subfolder}: {e}")
            
            # Process 100 CVEs at a time in parallel
            new_cve_jsons = []
            for i in range(0, len(cve_jsons), 100):
                cve_jsons_batch = cve_jsons[i:i+100]
                with ThreadPoolExecutor(max_workers=100) as executor:
                    cve_jsons_batch = list(executor.map(extract_cve_json, cve_jsons_batch))
                    failed_cves += [cve_json for cve_json in cve_jsons_batch if isinstance(cve_json, str)]
                    new_cve_jsons += [cve_json for cve_json in cve_jsons_batch if isinstance(cve_json, dict)]
            
            # Check for missing fields
            num_cves += len(new_cve_jsons)
            missing_descriptions = [cve_json for cve_json in new_cve_jsons if "description" not in cve_json or cve_json["description"] == None]
            missing_dates = [cve_json for cve_json in new_cve_jsons if "date_public" not in cve_json or cve_json["date_public"] == None]
            missing_affected_products = [cve_json for cve_json in new_cve_jsons if "affected_products" not in cve_json or cve_json["affected_products"] == None]
            missing_metrics = [cve_json for cve_json in new_cve_jsons if "metrics" not in cve_json or cve_json["metrics"] == None]

            metrics["missing_descriptions"] += len(missing_descriptions)
            metrics["missing_dates"] += len(missing_dates)
            metrics["missing_affected_products"] += len(missing_affected_products)
            metrics["missing_metrics"] += len(missing_metrics)
            
            # Delete keys in each object that have value of None
            new_cve_jsons = [{k: v for k, v in cve_json.items() if v != None} for cve_json in new_cve_jsons]

            # Upload to MongoDB
            # collection.insert_many(new_cve_jsons)

            print(f"Uploaded subfolder: {year_folder}/{subfolder}")

    print(f"Uploaded {num_cves} CVEs to MongoDB")
    if len(failed_cves) > 0:
        print(f"Failed to upload {len(failed_cves)} CVEs: {failed_cves}")
    print(f"Missing descriptions: {100 * metrics['missing_descriptions'] / num_cves}%")
    print(f"Missing dates: {100 * metrics['missing_dates'] / num_cves}%")
    print(f"Missing affected products: {100 * metrics['missing_affected_products'] / num_cves}%")
    print(f"Missing metrics: {100 * metrics['missing_metrics'] / num_cves}%")

# When called from terminal run the function
if __name__ == "__main__":
    upload_all_cves_to_mongo()