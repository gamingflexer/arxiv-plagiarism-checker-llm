import gradio as gr
import pandas as pd
import logging
from scrapper.main import ArxivPaper
from config import *
from db.db_functions import get_correct_author_name, insert_papers_data, fetch_papers_data, get_unquine_authors
from utils import compare_paper_ids

unique_authors_df = get_unquine_authors()

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
            unquine_authors_output = gr.Dataframe(headers=["author_name"],value=unique_authors_df, label=" Authors Currently in our DB")
        
        
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

    submit_button_tab_1.click(fn=plagiarism_checker,inputs=[authors_name_fetch, number_of_results_fetch] ,outputs= completed)
    submit_button_tab_2.click(fn=fetch_papers_data_df,inputs=[authors_name_paper] ,outputs=dataframe_output)

demo.launch()