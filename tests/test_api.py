import unittest
import requests
import inspect


class OrderedTestLoader(unittest.TestLoader):
    def getTestCaseNames(self, testCaseClass):
        """Return a sorted list of test method names found within testCaseClass"""
        test_names = super().getTestCaseNames(testCaseClass)
        test_cases = list(map(lambda name: (name, getattr(testCaseClass, name)), test_names))
        test_cases.sort(key=lambda item: inspect.getsourcelines(item[1])[1])  # Sort by source line number
        return [test[0] for test in test_cases]


class APITests(unittest.TestCase):

    """
    Test basic API errors: filter_params without sort_params, weird valies for return_n, etc.
    - Empty filter and sort params
    - Missing filter params but sort params
    - Missing sort params but filter params
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
    - attackVector
        - included_values for attackVector
        - Try included_range for attackVector
        - Empty included_values for attackVector
    - baseScore
        - included_range for baseScore
        - included_range with max but no min
        - Wrong values for max but not min
        - Swapped min and max
    
    Test sort_params with different parameters and values. Here's a list of tests:
    - Parameter that isn't in parameters list
    - date_public
        - Ascending
        - Descending
    - baseScore
        - Ascending
    - attackComplexity
        - Descending
    - baseSeverity
        - Ascending

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

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Test missing filter params but sort params
        request_body = {
            "sort_params": []
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("detail" in response.json())

        # Test missing sort params but filter params
        request_body = {
            "filter_params": []
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("detail" in response.json())

    def test_parameter_not_in_parameters_list(self):
                
            request_body = {
                "filter_params": [
                    {
                        "parameter": "not_in_parameters_list",
                        "included_values": ["value"]
                    }
                ],
                "sort_params": []
            }
    
            response = requests.post("http://localhost:8000/search/", json=request_body)
    
            self.assertEqual(response.status_code, 422)
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

        response = requests.post("http://localhost:8000/search/", json=request_body)

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

        response = requests.post("http://localhost:8000/search/", json=request_body)

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

        response = requests.post("http://localhost:8000/search/", json=request_body)

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

        response = requests.post("http://localhost:8000/search/", json=request_body)

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

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
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

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("errors" in response.json())
        
    
    def test_product(self):
        
        request_body = {
            "filter_params": [
                {
                    "parameter": "product",
                    "included_values": ["windows", "red hat"]
                }
            ],
            "sort_params": []
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Check that all the results have either "windows" or "red hat"
        for result in response.json()["results"]:
            self.assertTrue(any(['windows' in product["product"].lower() or 'red hat' in product["product"].lower() 
                for product in result["affected_products"]]))
        
        # Check that there are results where the product is "windows" or "red hat" but not both
        one_not_both = False
        for result in response.json()["results"]:
            has_windows = any(['windows' in product["product"].lower() for product in result["affected_products"]])
            has_red_hat = any(['red hat' in product["product"].lower() for product in result["affected_products"]])
            if has_windows != has_red_hat:
                one_not_both = True
                break
        self.assertTrue(one_not_both)

    def test_attackComplexity(self):
            
            request_body = {
                "filter_params": [
                    {
                        "parameter": "attackComplexity",
                        "included_range": {
                            "min": "HIGH"
                        }
                    }
                ],
                "sort_params": []
            }
    
            response = requests.post("http://localhost:8000/search/", json=request_body)
    
            self.assertEqual(response.status_code, 200)
            self.assertTrue("results" in response.json())
    
            # Check that all the results have attackComplexity of "HIGH"
            self.assertTrue(all([result["metrics"]["attackComplexity"].lower() == "high" for result in response.json()["results"]]))

    def test_attackVector(self):
            
            request_body = {
                "filter_params": [
                    {
                        "parameter": "attackVector",
                        "included_values": ["network", "local"]
                    }
                ],
                "sort_params": []
            }
    
            response = requests.post("http://localhost:8000/search/", json=request_body)
    
            self.assertEqual(response.status_code, 200)
            self.assertTrue("results" in response.json())
            self.assertTrue(all([result["metrics"]["attackVector"].lower() in ["network", "local"] for result in response.json()["results"]]))

            # Test included_range for attackVector
            request_body = {
                "filter_params": [
                    {
                        "parameter": "attackVector",
                        "included_range": {
                            "min": "network",
                            "max": "local"
                        }
                    }
                ],
                "sort_params": []
            }

            response = requests.post("http://localhost:8000/search/", json=request_body)

            self.assertEqual(response.status_code, 422)
            self.assertTrue("errors" in response.json())

            # Test empty included_values
            request_body = {
                "filter_params": [
                    {
                        "parameter": "attackVector",
                        "included_values": []
                    }
                ],
                "sort_params": []
            }

            response = requests.post("http://localhost:8000/search/", json=request_body)

            self.assertEqual(response.status_code, 200)
            self.assertTrue("results" in response.json())
            self.assertTrue(len(response.json()["results"]) == 0)

    def test_baseScore(self):
        
        request_body = {
            "filter_params": [
                {
                    "parameter": "baseScore",
                    "included_range": {
                        "min": 4.0,
                        "max": 9.0
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Check that all the results have baseScore between 4.0 and 9.0
        self.assertTrue(all([4.0 <= result["metrics"]["baseScore"] <= 9.0 for result in response.json()["results"]]))

        # Test included_range with max but no min
        request_body = {
            "filter_params": [
                {
                    "parameter": "baseScore",
                    "included_range": {
                        "max": 7.0
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Test wrong values for max but not min
        request_body = {
            "filter_params": [
                {
                    "parameter": "baseScore",
                    "included_range": {
                        "max": 4.0
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Test swapped min and max
        request_body = {
            "filter_params": [
                {
                    "parameter": "baseScore",
                    "included_range": {
                        "min": 7.0,
                        "max": 4.0
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("errors" in response.json())

        # Test wrong value types for min and max
        request_body = {
            "filter_params": [
                {
                    "parameter": "baseScore",
                    "included_range": {
                        "min": "string",
                        "max": 4.0
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("errors" in response.json())

        # Test wrong value types for min and max
        request_body = {
            "filter_params": [
                {
                    "parameter": "baseScore",
                    "included_range": {
                        "min": 4.0,
                        "max": "string"
                    }
                }
            ],
            "sort_params": []
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("errors" in response.json())
        

    """
    Test sort_params
    """

    def test_sorting_parameter_not_in_parameters_list(self):
            
        request_body = {
            "filter_params": [],
            "sort_params": [
                {
                    "parameter": "not_in_parameters_list",
                    "direction": "high"
                }
            ]
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("errors" in response.json())

    def test_sorting_incorrect_format(self):
                    
            request_body = {
                "filter_params": [],
                "sort_params": [
                    {
                        "parameter": "date_public"
                    }
                ]
            }
    
            response = requests.post("http://localhost:8000/search/", json=request_body)
    
            self.assertEqual(response.status_code, 422)
            self.assertTrue("errors" in response.json())

            request_body = {
                "filter_params": [],
                "sort_params": [
                    {
                        "direction": "high"
                    }
                ]
            }
    
            response = requests.post("http://localhost:8000/search/", json=request_body)
    
            self.assertEqual(response.status_code, 422)
            self.assertTrue("errors" in response.json())

            request_body = {
                "filter_params": [],
                "sort_params": [
                    {
                        "parameter": "date_public",
                        "direction": "high"
                    },
                    {
                        "parameter": "date_public",
                        "direction": "low"
                    }
                ]
            }
    
            response = requests.post("http://localhost:8000/search/", json=request_body)
    
            self.assertEqual(response.status_code, 422)
            self.assertTrue("errors" in response.json())

    def test_sorting_date_public(self):
        
        # Test normal request
        request_body = {
            "filter_params": [],
            "sort_params": [
                {
                    "parameter": "date_public",
                    "direction": "high"
                }
            ]
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Check that each result's date is greater than next result
        for i in range(len(response.json()["results"]) - 1):
            self.assertTrue(response.json()["results"][i]["date_public"] >= response.json()["results"][i+1]["date_public"])

        # Test descending direction
        request_body = {
            "filter_params": [],
            "sort_params": [
                {
                    "parameter": "date_public",
                    "direction": "low"
                }
            ]
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Check that each result's date is less than next result
        for i in range(len(response.json()["results"]) - 1):
            self.assertTrue(response.json()["results"][i]["date_public"] <= response.json()["results"][i+1]["date_public"])

    def test_sorting_baseScore(self):
            
        # Test high direction
        request_body = {
            "filter_params": [],
            "sort_params": [
                {
                    "parameter": "baseScore",
                    "direction": "high"
                }
            ]
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Check that each result's baseScore is greater than next result
        for i in range(len(response.json()["results"]) - 1):
            self.assertTrue(response.json()["results"][i]["metrics"]["baseScore"] >= response.json()["results"][i+1]["metrics"]["baseScore"])


    def test_sorting_attackComplexity(self):
            
        # Test low direction
        request_body = {
            "filter_params": [],
            "sort_params": [
                {
                    "parameter": "attackComplexity",
                    "direction": "low"
                }
            ]
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        possible_values = ["LOW", "HIGH"]
        for i in range(len(response.json()["results"]) - 1):
            self.assertTrue(possible_values.index(response.json()["results"][i]["metrics"]["attackComplexity"]) <= possible_values.index(response.json()["results"][i+1]["metrics"]["attackComplexity"]))

    def test_sorting_baseSeverity(self):
         
        # Test low direction
        request_body = {
            "filter_params": [],
            "sort_params": [
                {
                    "parameter": "baseSeverity",
                    "direction": "low"
                }
            ]
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        possible_values = ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        for i in range(len(response.json()["results"]) - 1):
            self.assertTrue(possible_values.index(response.json()["results"][i]["metrics"]["baseSeverity"]) <= possible_values.index(response.json()["results"][i+1]["metrics"]["baseSeverity"]))

    def test_return_n(self):
            
        # Test return_n = 10
        request_body = {
            "filter_params": [],
            "sort_params": [],
            "return_n": 10
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())
        self.assertEqual(len(response.json()["results"]), 10)

        # Test return_n = 101
        request_body = {
            "filter_params": [],
            "sort_params": [],
            "return_n": 101
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("detail" in response.json())

        # Test return_n = -1
        request_body = {
            "filter_params": [],
            "sort_params": [],
            "return_n": -1
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("detail" in response.json())

        # Test return_n = "string"
        request_body = {
            "filter_params": [],
            "sort_params": [],
            "return_n": "string"
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("detail" in response.json())

    def test_return_offset(self):
                
        # Test return_offset = 200
        request_body = {
            "filter_params": [],
            "sort_params": [],
            "return_offset": 200
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("results" in response.json())

        # Test return_offset = -1
        request_body = {
            "filter_params": [],
            "sort_params": [],
            "return_offset": -1
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("detail" in response.json())

        # Test return_offset = "string"
        request_body = {
            "filter_params": [],
            "sort_params": [],
            "return_offset": "string"
        }

        response = requests.post("http://localhost:8000/search/", json=request_body)

        self.assertEqual(response.status_code, 422)
        self.assertTrue("detail" in response.json())

        # Test that return offset actually gives different results
        request_body = {
            "filter_params": [],
            "sort_params": [],
            "return_offset": 0,
            "return_n": 10
        }

        response1 = requests.post("http://localhost:8000/search/", json=request_body)
        original_results = response1.json()["results"]

        request_body = {
            "filter_params": [],
            "sort_params": [],
            "return_offset": 5,
            "return_n": 10
        }

        response2 = requests.post("http://localhost:8000/search/", json=request_body)
        new_results = response2.json()["results"]

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertTrue("results" in response1.json())
        self.assertTrue("results" in response2.json())
        self.assertEqual(len(original_results), 10)
        self.assertEqual(len(new_results), 10)
        self.assertNotEqual(original_results, new_results)
        self.assertEqual(original_results[5:], new_results[:5])
        for i in range(5):
            self.assertNotEqual(original_results[i], new_results[i+5])    

if __name__ == '__main__':
    unittest.main(failfast=True, testLoader=OrderedTestLoader())