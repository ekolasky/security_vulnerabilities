import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

with open("src/parameters.json", "r") as f:
    parameters = json.load(f)

# Create list of parameters to explain parameters to model
formatted_parameters_list = []
for parameter in parameters:

    formatted_datatype = ""
    if parameter["data_type"] == "string-options":
        formatted_datatype = "A string with possible values of: " + ", ".join(parameter["possible_values"])
    elif parameter["data_type"] == "string":
        formatted_datatype = f"A string, here's an example: {parameter['example']}"
    elif parameter["data_type"] == "iso8601":
        formatted_datatype = 'An ISO8601 date string, here is an example: 2024-06-27T16:39:42.511Z'
    elif parameter["data_type"] == "number":
        formatted_datatype = "A number from 0 to 10, does not have to be an integer necessarily."

    supported_filters = []
    if "filter-values" in parameter["accepted_operations"]:
        supported_filters.append("includes_values")
    if "filter-range" in parameter["accepted_operations"]:
        supported_filters.append("includes_range")

    formatted_parameters_list.append(
        f"Parameter: {parameter['parameter']}\n"
        f"Datatype: {parameter['data_type']}\n"
        f"Supports Sorting: {'sort' in parameter['accepted_operations']}\n"
        f"Supported Filter Types: {', '.join(supported_filters)}\n"
    )
    

initial_prompt_template = (
"Your job as a helpful AI assistant is to filter a database of CVEs in response to a user's search query. To do this you will make "+
"a function call to the function filter_cves. This function will then show the user a list of CVEs that match their query. "+
"The function call includes both filter_params and sort_params, which filter and sort the database based on parameters of the "+
"documents within the database. Here is a list of parameters you can filter by, along with information about what type of filter "+
"you can use, whether it supports sorting, and its datatype. Here's the list of parameters you can filter by:\n\n"+
"\n".join(formatted_parameters_list)+
"\n\n"+
"Here are some examples of what a user query and the correct function call would look like:\n\n"+
"""
Query: "What are some recent security vulnerabilities for Windows"
Function Call: 
{
    "filter_params": [
        {
            "parameter": "affectedProducts",
            "included_values": ["windows"]
        }
    ],
    "sort_params": [
        {
            "parameter": "date_public",
            "direction": "high"
        }
    ]
}

Query: "Show me high severity vulnerabilities from the last few months"
Function Call:
{
    "filter_params": [
        {
            "parameter": "severity",
            "included_values": ["high"]
        },
        {
            "parameter": "date_public",
            "included_range": {
                "min": "2022-01-01",
                "max": "2022-03-01"
            }
        }
    ],
    "sort_params": [
        {
            "parameter": "date_public",
            "direction": "high"
        }
    ]
}

I will now give you the user's query. Please return the function call to filter the database below. Here is the user's query:
"""
)

reprompt_template = """
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "filter_params",
            "description": "Filter database for results that match a user's search.",
            "parameters": {
                "type": "object",
                "required": ['filter_params', 'sort_params'],
                "properties": {
                    "filter_params": {
                        "type": "array",
                        "description": ('filter_params is an array of filters used to filter the CVEs in the database in response . '
                        'to the search query. Each filter should have the name of the parameter to filter by and either a '
                        '"included_values" or "included_range" parameter.'
                        ),
                        "items": {
                            "type": 'object',
                            "required": ['parameter'],
                            "properties": {
                                "parameter": {
                                    "type": "string",
                                    "description": "The parameter to filter the database with."
                                },
                                "included_values": {
                                    "type": "array",
                                    "description": "All documents returned by the filter will have one of the values in this list for the parameter."
                                },
                            }
                        }
                    },
                    "sort_params": {
                        "type": "array",
                        "description": ('sort_params is an array of sorting parameters used to prioritize results that best fit the '
                        'users search query. Each sorting parameter should have the name of the parameter to sort by and a direction '
                        'parameter that is either "low" or "high".'
                        ),
                        "items": {
                            "type": 'object',
                            "required": ['parameter'],
                            "properties": {
                                "parameter": {
                                    "type": "string",
                                    "description": "The parameter to sort the results by."
                                },
                                "direction": {
                                    "type": "string",
                                    "description": "The direction to sort the results in, either 'low' or 'high'."
                                },
                            }
                        }
                    }
                }
            }
        }
    }
]

def initial_request(query):
    
    prompt = initial_prompt_template + query

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        max_tokens=200,
        stop=None,
        temperature=0
    )
    print(chat_completion)
    print(chat_completion.choices[0].message.content)

    messages.append({
        "role": "assistant",
        "content": chat_completion.choices[0].message.content
    })
    return messages

def reprompt_with_errors(messages, errors):
    
    prompt = ("I just ran your previous function call through a validator and got the following errors: \n\n" +
        "\n".join(errors) +
        "\n\nPlease return a new function call that corrects these errors."
    )

    messages.append({
        "role": "user",
        "content": prompt
    })

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        max_tokens=200,
        stop=None,
        temperature=0
    )

    messages.append({
        "role": "assistant",
        "content": chat_completion.choices[0].message.content
    })

    return messages