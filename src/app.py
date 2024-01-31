import gradio as gr
import pandas as pd
import logging
from scrapper.main import ArxivPaper
from config import *
from db.db_functions import get_correct_author_name, insert_papers_data, fetch_papers_data, get_unquine_authors
from utils import compare_paper_ids
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from config import OPENAI_API_KEY

emmbedding_model = "text-embedding-3-large"
openai_ef = embedding_functions.OpenAIEmbeddingFunction(model_name=emmbedding_model,api_key=OPENAI_API_KEY)
if deploy:
    chroma_client = chromadb.PersistentClient(path="./data/emeddeings")
else:
    chroma_client = chromadb.PersistentClient(path="/home/ubuntu/research/data/emeddeings")
    
collection_doc = chroma_client.get_or_create_collection(name="2024_document_lvl_test")

def plagiarism_checker(authors_name_fetch,number_of_results_fetch, progress=gr.Progress()):
    number_of_results_fetch = int(number_of_results_fetch)
    print(authors_name_fetch,number_of_results_fetch,type(number_of_results_fetch))
    progress(0.2, desc="Collecting Links")
    author_obj = ArxivPaper(authors_name_fetch)
    db_author_name = get_correct_author_name(authors_name_fetch)
    paper_links = author_obj.get_results_google(number_of_results=number_of_results_fetch)
    paper_ids = author_obj.get_paper_id(paper_links)
    progress(0.4, desc=f"Collecting Papers for {len(paper_ids)}")
    if db_author_name is None:
        data = fetch_papers_data(db_author_name)
        remaining_paper_ids = compare_paper_ids(data,paper_ids)
        print("No similar author found in the database")
        local_saved_papers = os.path.join(os.getcwd(), "data", "papers", authors_name_fetch.replace(" ", "_"))
        progress(0.6, desc="Making summary")
        data_to_save = []
        if remaining_paper_ids != []:
            author_obj.get_paper_details_batch(paper_ids=paper_ids, path="./data/papers")
            for paper in os.listdir(local_saved_papers):
                paper_path = os.path.join(local_saved_papers, paper)
                with open(paper_path, "r") as f:
                    data_to_save.append(f.read())
    else:
        print(f"Found similar author in the database: {db_author_name}")
        data = fetch_papers_data(db_author_name)
        remaining_paper_ids = compare_paper_ids(data,paper_ids)
        local_saved_papers = os.path.join(os.getcwd(), "data", "papers", authors_name_fetch.replace(" ", "_"))
        progress(0.6, desc="Making summary")
        data_to_save = []
        if remaining_paper_ids != []:
            author_obj.get_paper_details_batch(paper_ids=remaining_paper_ids, path="./data/papers")
            for paper in os.listdir(local_saved_papers):
                paper_path = os.path.join(local_saved_papers, paper)
                with open(paper_path, "r") as f:
                    data_to_save.append(f.read())
        else:
            print("All papers already present in the database")
        
    progress(0.8, desc="Saving to Database")
    insert_papers_data(data_to_save, authors_name_fetch)
    return f"Fetched Latest Papers for {len(remaining_paper_ids)}"

def fetch_papers_data_df(authors_name: str, progress=gr.Progress()):
    progress(0.2, desc="Fetching Papers")
    fetched_data = fetch_papers_data(authors_name,fields_to_query=['doi_no', 'author_name', 'title', 'authors', 'year', 'pdf_link',
    'references', 'categories', 'comment', 'journal_ref', 'source',
    'summary', 'published'])
    progress(0.8, desc="Making DataFrame")
    return pd.DataFrame(fetched_data)

def embedding_searcher(embbed_text_search, top_k=4, progress=gr.Progress()):
    
    data = collection_doc.query(query_embeddings = openai_ef([embbed_text_search]), n_results=top_k)
    result = pd.DataFrame(data['ids'][0], columns=['ID'])
    result['Distance'] = data['distances'][0]

    # Extracting information from metadatas
    metadata_list = data['metadatas'][0]
    titles = [metadata['title'] for metadata in metadata_list]
    authors = [metadata['authors'] for metadata in metadata_list]
    sources = [metadata['source'] for metadata in metadata_list]

    # Adding metadata columns to the dataframe
    result['Title'] = titles
    result['Authors'] = authors
    result['Source'] = sources
    return result

with gr.Blocks() as demo:
    
    with gr.Tab("Get Papers Data"):
        with gr.Row():
            authors_name_paper = gr.Textbox(label="Enter Author's Name")
            submit_button_tab_2 = gr.Button("Start")
        with gr.Row():
            dataframe_output = gr.Dataframe(headers=['doi_no', 'author_name', 'title', 'authors', 'year', 'pdf_link',
    'references', 'categories', 'comment', 'journal_ref', 'source',
    'summary', 'published'])
        with gr.Row():
            unquine_authors_output = gr.Dataframe(headers=["author_name"],value=get_unquine_authors(), label=" Authors Currently in our DB")
        
        
    with gr.Tab("Arxiv Plagiarism Fetcher & Save to DB"):
        with gr.Row():
            authors_name_fetch = gr.Textbox(label="Enter Author's Name")
            number_of_results_fetch = gr.Textbox(label="Number of results - Min - 5")
            submit_button_tab_1 = gr.Button("Start")
        with gr.Row():
            completed = gr.Textbox(label="Completed")
            
    with gr.Tab("Arxiv Plagiarism Checker"):
        with gr.Row():
            authors_name = gr.Textbox(label="Enter Author's Name")
            number_of_results = gr.Number(label="Number of results - Min - 5")
            submit_button = gr.Button("Start")
            
    with gr.Tab("Open Embeddings Search"):
        with gr.Row():
            embbed_text_search = gr.Textbox(label="Enter Text")
        with gr.Row():
            top_k = gr.Number(label="Number of results - Min 2")
        with gr.Row():
            submit_button_tab_4 = gr.Button("Start")
            dataframe_output_tab_4 = gr.Dataframe(headers=['ID', 'Distance', 'Title', 'Authors', 'Source'])

    submit_button_tab_1.click(fn=plagiarism_checker,inputs=[authors_name_fetch, number_of_results_fetch] ,outputs= completed)
    submit_button_tab_2.click(fn=fetch_papers_data_df,inputs=[authors_name_paper] ,outputs=dataframe_output)
    submit_button_tab_4.click(fn=embedding_searcher,inputs=[embbed_text_search, top_k] ,outputs= dataframe_output_tab_4)

demo.launch()