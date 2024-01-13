from decouple import config
import os

OPENAI_API_KEY = config('OPENAI_API_KEY', default="")
SERP_API_KEY = config('SERP_API_KEY', default="")

SUPABASE_URL = config('SUPABASE_URL', default="")
SUPABASE_KEY = config('SUPABASE_KEY', default="")

COPY_LEAKS_EMAIL_ADDRESS = config('COPY_LEAKS_EMAIL_ADDRESS', default="")
COPY_LEAKS_EMAIL_KEY = config('COPY_LEAKS_EMAIL_KEY', default="")
WEBHOOK_SECRET = config('WEBHOOK_SECRET', default="*asd9s")

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
