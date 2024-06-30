import unittest
import requests


"""
NEED TO IMPLEMENT
Test filtering / sorting by every possible parameter. Also test obvious validation edge cases
"""

"""
Test filters for each parameter
"""

class APITests(unittest.TestCase):

    """
    Test basic API errors: filter_params without sort_params, weird valies for return_n, etc.
    - Empty filter and sort params
    - Missing filter params but sort params
    - Missing sort params but filter params
    NEED TO ADD TEST FOR WEIRD VALUES OF RETURN_N AND RETURN_OFFSET
    """

    """
    Test filters with different parameters and values. Here's a list of tests:
    - Parameter that isn't in parameters list
    - cve_id
        - included_values list for cve_id
    - date_public
        - included_range for date_public
        - included_range with max but no min
        - included_range with min but no max
        - included_range with min and max switched
        - included_range with incorrectly formatted dates
        - included_values for date_public
    - product
        - included_values for product
    - attackComplexity
        - included_range starting from "HIGH"

    Test sort_params with different parameters and values. Here's a list of tests:

    Test other parameters:
    - Return n
        - return_n = 10
        - return_n = 101
        - return_n = -1
        - return_n = "string"
    - Return offset
        - return_offset = 200
        - return_offset = -1
        - return_offset = "string"
    
    """

    def test_basic_api_errors(self):
            
        # Test empty filter and sort params
        request_body = {
            "filter_params": [],
            "sort_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("errors" in response.json())

        # Test missing filter params but sort params
        request_body = {
            "sort_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("errors" in response.json())

        # Test missing sort params but filter params
        request_body = {
            "filter_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("errors" in response.json())

    def test_cve_id(self):
        
        request_body = {
            "filter_params": [
                {
                    "parameter": "cve_id",
                    "included_values": ["CVE-2024-0874", "CVE-2024-3727"]
                }
            ],
            "sort_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())
        self.assertEqual(len(response.json()["results"]), 2)


    def test_date_public(self):
            
        # Test normal request
        request_body = {
            "filter_params": [
                {
                    "parameter": "date_public",
                    "included_range": {
                        "min": "2024-02-27T16:39:42Z",
                        "max": "2024-06-27T16:39:42Z"
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Test min but no max
        request_body = {
            "filter_params": [
                {
                    "parameter": "date_public",
                    "included_range": {
                        "min": "2024-02-27T16:39:42Z"
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Test max but no min
        request_body = {
            "filter_params": [
                {
                    "parameter": "date_public",
                    "included_range": {
                        "max": "2024-06-27T16:39:42Z"
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Test min and max switched
        request_body = {
            "filter_params": [
                {
                    "parameter": "date_public",
                    "included_range": {
                        "min": "2024-06-27T16:39:42Z",
                        "max": "2024-02-27T16:39:42Z"
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("errors" in response.json())

        # Test incorrectly formatted dates
        request_body = {
            "filter_params": [
                {
                    "parameter": "date_public",
                    "included_range": {
                        "min": "2024-02-27T16:39:42Z",
                        "max": "2024-06-27T16:39:42"
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 400)
        self.assertTrue("errors" in response.json())
        
    
    def test_product(self):
        
        request_body = {
            "filter_params": [
                {
                    "parameter": "product",
                    "included_values": ["windows"]
                }
            ],
            "sort_params": []
        }

        response = requests.post("localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())
        self.assertEqual(len(response.json()["results"]), 2)


if __name__ == '__main__':
    unittest.main()