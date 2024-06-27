import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def get_db_connection():
    """
    Initialize database connection with CVE collection and schema.
    """
    # Connect to MongoDB
    client_atlas = MongoClient(
        f"mongodb+srv://{os.getenv('MONGODB_USERNAME')}:{os.getenv('MONGODB_PASSWORD')}@{os.getenv('MONGODB_CLUSTER_URL')}?retryWrites=true&w=majority"
    )
    db = client_atlas['cve_database']  # For the Atlas example
    return db


def get_cve_by_param(param, value):
    """
    This function queries the MongoDB database for CVEs based on a parameter and value. Returns random document.
        - param: The parameter to filter by.
        - value: The value to filter by.
    """
    db = get_db_connection()
    collection = db['cve']
    # Use aggregation to match the specified criteria and then randomly select one document
    pipeline = [
        {"$match": {param: value}},
        {"$sample": {"size": 1}}
    ]
    cve = list(collection.aggregate(pipeline))
    return json.dumps(cve[0], indent=4) if cve else None