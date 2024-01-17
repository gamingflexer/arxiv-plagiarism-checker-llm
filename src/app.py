import gradio as gr
import pandas as pd
import logging
from scrapper.main import ArxivPaper
from config import *
from db.db_functions import get_correct_author_name, insert_papers_data, fetch_papers_data
from utils import compare_paper_ids

"""
author_obj = ArxivPaper("Andrew Ng")
paper_links = author_obj.get_results_google(number_of_results=25)
paper_ids = author_obj.get_paper_id(paper_links)
author_obj.get_paper_details_batch(paper_ids=paper_ids, path="./data/papers")
"""

def plagiarism_checker(authors_name: str,number_of_results=5, progress=gr.Progress()):
    progress(0.2, desc="Collecting Links")
    author_obj = ArxivPaper(authors_name)
    db_author_name = get_correct_author_name(authors_name)
    paper_links = author_obj.get_results_google(number_of_results=number_of_results)
    paper_ids = author_obj.get_paper_id(paper_links)
    progress(0.4, desc="Collecting Papers")
    if db_author_name is None:
        print("No similar author found in the database")
        author_obj.get_paper_details_batch(paper_ids=paper_ids, path="./data/papers")
        local_saved_papers = os.path.join(os.getcwd(), "data", "papers", authors_name.replace(" ", "_"))
        progress(0.6, desc="Making summary")
        data_to_save = []
        for paper in os.listdir(local_saved_papers):
            paper_path = os.path.join(local_saved_papers, paper)
            with open(paper_path, "r") as f:
                data_to_save.append(f.read())
    else:
        print(f"Found similar author in the database: {db_author_name}")
        data = fetch_papers_data(db_author_name)
        reamining_paper_ids = compare_paper_ids(data,paper_ids)
        progress(0.6, desc="Making summary")
        data_to_save = []
        if reamining_paper_ids != []:
            author_obj.get_paper_details_batch(paper_ids=reamining_paper_ids, path="./data/papers")
            local_saved_papers = os.path.join(os.getcwd(), "data", "papers", authors_name.replace(" ", "_"))
            for paper in os.listdir(local_saved_papers):
                paper_path = os.path.join(local_saved_papers, paper)
                with open(paper_path, "r") as f:
                    data_to_save.append(f.read())
        else:
            print("All papers already present in the database")
        
    progress(0.8, desc="Saving to Database")
    insert_papers_data(data_to_save, authors_name)
    return "Fetched Latest Papers"

def fetch_papers_data_df(authors_name: str, progress=gr.Progress()):
    progress(0.2, desc="Fetching Papers")
    fetched_data = fetch_papers_data(authors_name,all=True)
    progress(0.8, desc="Making DataFrame")
    return pd.DataFrame(fetched_data[1])

with gr.Blocks() as demo:
    
    with gr.Tab("Get Papers Data"):
        with gr.Row():
            authors_name_paper = gr.Textbox(label="Enter Author's Name")
            submit_button_tab_2 = gr.Button("Start")
        with gr.Row():
            dataframe_output = gr.Dataframe(headers=['doi_no', 'title', 'summary', 'authors', 'year', 'pdf_link',
    'references', 'categories', 'comment', 'journal_ref', 'source',
    'primary_category', 'published','author_name'])
        
    with gr.Tab("Arxiv Plagiarism Fetcher & Save to DB"):
        with gr.Row():
            authors_name = gr.Textbox(label="Enter Author's Name")
            number_of_results = gr.Number(label="Number of results - Min - 5")
            submit_button_tab_1 = gr.Button("Start")
        with gr.Row():
            completed = gr.Textbox(label="Completed")

            
    with gr.Tab("Arxiv Plagiarism Checker"):
        with gr.Row():
            authors_name = gr.Textbox(label="Enter Author's Name")
            number_of_results = gr.Number(label="Number of results - Min - 5")
            submit_button = gr.Button("Start")


    submit_button_tab_1.click(fn=plagiarism_checker,inputs=[authors_name, number_of_results] ,outputs= completed)
    submit_button_tab_2.click(fn=fetch_papers_data_df,inputs=[authors_name_paper] ,outputs=dataframe_output)

demo.launch()