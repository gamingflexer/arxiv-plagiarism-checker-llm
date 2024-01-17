from decouple import config
import os

deploy = True

if deploy:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    SERP_API_KEY = os.environ.get("SERP_API_KEY")
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    COPY_LEAKS_EMAIL_ADDRESS = os.environ.get("COPY_LEAKS_EMAIL_ADDRESS")
    COPY_LEAKS_EMAIL_KEY = os.environ.get("COPY_LEAKS_EMAIL_KEY")
    WEBHOOK_SECRET = "*asd9s"
else:
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
