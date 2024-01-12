from decouple import config
import os

OPENAI_API_KEY = config('OPENAI_API_KEY', default="")
SERP_API_KEY = config('SERP_API_KEY', default="")

dense_models = {
    'text-embedding-ada-002': {
        'source': 'openai',
        'dimension': 1536,
        'api_key': True,
        'metric': 'dotproduct'
    },
    'multilingual-22-12': {
        'source': 'cohere',
        'dimension': 768,
        'api_key': True,
        'metric': 'dotproduct'
    }
}
