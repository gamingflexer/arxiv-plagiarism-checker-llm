
import logging
import os
from supabase import create_client, Client
from fuzzywuzzy import fuzz
from config import SUPABASE_URL, SUPABASE_KEY
import json
import logging
import pandas as pd 

url: str = SUPABASE_URL
key: str = SUPABASE_KEY
supabase: Client = create_client(url, key)

def insert_papers_data(data,author_name ,table_name: str = 'papers'):
    if data == []:
        print("No data to insert")
        return
    formatted_data = []
    for entry in data:
        entry = json.loads(entry)
        data_db = {
            'doi_no': entry.get('doi'),
            'title': entry.get('title'),
            'summary': entry.get('summary'),
            'authors': ", ".join(entry.get('authors',[])),
            'year': entry.get('year'),
            'pdf_link': entry.get('pdf_link'),
            'references': ", ".join(entry.get('references')),
            'categories': ", ".join(entry.get('categories')),
            'comment': entry.get('comment'),
            'journal_ref': entry.get('journal_ref'),
            'source': entry.get('source'),
            'primary_category': entry.get('primary_category'),
            'published': entry.get('published'),
            'author_name' : author_name,
        }
        formatted_data.append(data_db)
    data, count = supabase.table(table_name).insert(formatted_data).execute()


def get_correct_author_name(user_input_author):
    authors_name_data = supabase.table('papers').select('author_name').execute()
    unique_authors = set(author_dict['author_name'] for author_dict in authors_name_data.data)
    unique_authors_list = list(unique_authors)
    similar_authors = [author for author in unique_authors_list if fuzz.ratio(user_input_author, author) > 60]
    if similar_authors:
        return similar_authors[0]
    else:
        print(f"No similar author found for '{user_input_author}'")
        return None
    

def fetch_papers_data(author_name, fields_to_query = ["doi_no"],table_name: str = 'papers', all=False):
    author_name = get_correct_author_name(author_name)
    if all:
        data, count = supabase.table(table_name).select("*").execute()
        return data
    data, count = supabase.table(table_name).select(",".join(fields_to_query)).eq('author_name', author_name).execute()
    return data[1]

def get_unquine_authors():
    authors_name_data = supabase.table('papers').select('author_name').execute()
    unique_authors = set(author_dict['author_name'] for author_dict in authors_name_data.data)
    unique_authors_df = pd.DataFrame(unique_authors, columns=['author_name'])
    return unique_authors_df