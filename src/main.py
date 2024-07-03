"""
Main.py runs the both scraper and the API. The scraper detects recent posts on included websites and extracts included security 
vulnerabilities from those websites. The API allows the user to see a feed of the most recent security vulnerabilities.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

from .utils.search_utils import handle_nl_search, retrieve_cves
from .utils.search_validators import validate_filters, validate_sorts
from .utils.update_database import update_database

"""
Periodically check CVE GitHub repositories for new CVEs and add them to the database.
"""

@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Starting scheduler")
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_database, "interval", seconds=30)
    scheduler.start()
    update_database()
    yield


app = FastAPI(lifespan=lifespan)
scheduler = AsyncIOScheduler()



# Get request for testing
@app.get("/")
def read_root():
    return {"message": "Welcome to the Alaris Vulnerabilities Feed API!"}


"""
Validator for Search Endpoint
"""
# Validate search request
class SearchModel(BaseModel):
    filter_params: Optional[list] = None
    sort_params: Optional[list] = None
    query: Optional[str] = None
    return_n: Optional[int] = Field(100, lt=100)
    return_offset: Optional[int] = 0

    @model_validator(mode='before')
    @classmethod
    def check_filter_params_or_query(cls, values):
        filter_params, sort_params, query = values.get('filter_params'), values.get('sort_params'), values.get('query')
        print((not filter_params or not sort_params) and not query)
        print(not sort_params)
        if (filter_params == None or sort_params == None) and not query:
            raise ValueError('Either "filter_params" and "sort_params" must be provided, or "query" must be provided')
        return values

    @model_validator(mode='before')
    @classmethod
    def check_integers(cls, values):
        return_n, return_offset = values.get('return_n'), values.get('return_offset')

        if return_n is not None and not isinstance(return_n, int):
            raise ValueError(f'"return_n" must be an integer')
        if return_n is not None and (return_n <= 0 or return_n > 100):
            raise ValueError('return_n must be between 1 and 100')
        if return_offset is not None and not isinstance(return_offset, int):
            raise ValueError(f'"return_offset" must be an integer')
        if return_offset is not None and return_offset < 0:
            raise ValueError('return_offset must be greater than or equal to 0')
        return values

"""
Search and sort database for CVEs.
This function takes both a filter and a sort parameter and returns a list of matching CVEs. The function can also handle natural 
language searches. It works by feeding the search to an LLM which generates a list of filters and sorting parameters, which are then 
used to filter and sort the database. The natural language search is currently incompatible with the filter and sort parameters.

Inputs:
- filter_params: A dictionary of filters to apply to the search.
- sort_params: A dictionary of sorting parameters to apply to the search.
- query: A natural language search string.
- return_n: The number of results to return.
- return_offset: The number of results to skip before returning results.

Returns:
- results: A list of matching CVEs.
- filter_params: A list of filters applied to the search.
- sort_params: A list of sorting parameters applied to the search.
"""

@app.post("/search/")
async def search(request_body: SearchModel):
    
    # Handle natural language search
    if (request_body.query):
        output = handle_nl_search(request_body.query, request_body.return_n, request_body.return_offset)

        if ('errors' in output):
            return output['errors']
        
        return output
    
    else:
        # Validate filter_params and sort_params
        errors = []
        errors += validate_filters(request_body.filter_params)
        errors += validate_sorts(request_body.sort_params)

        if (len(errors) > 0):
            return JSONResponse(status_code=422, content={"errors": errors})

        # Retrieve CVEs from MongoDB
        results = retrieve_cves(request_body.filter_params, request_body.sort_params, request_body.return_n, request_body.return_offset)

        return {
            'results': results,
            'filter_params': request_body.filter_params,
            'sort_params': request_body.sort_params
        }



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)