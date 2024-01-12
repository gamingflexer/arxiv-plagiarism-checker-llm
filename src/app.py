import gradio as gr
import pandas as pd
import logging
from scrapper.main import ArxivPaper

"""
author_obj = ArxivPaper("Andrew Ng")
paper_links = author_obj.get_results_google(number_of_results=25)
paper_ids = author_obj.get_paper_id(paper_links)
author_obj.get_paper_details_batch(paper_ids=paper_ids, path="./data/papers")
"""

def plagiarism_checker(authors_name):
    print(authors_name)
    data = {
        "paper": ["Collective annotation of wikipedia entities in web text",
                    "Glister: Generalization based data subset selection for efficient and robust learning",
                    "Grad-match: Gradient matching based data subset selection for efficient deep model training"],
        "paper_id": [2303.13798, 2303.13798, 2303.13798],
        "paper_link": ["https://arxiv.org/pdf/2303.13798", "https://arxiv.org/pdf/2303.13798", "https://arxiv.org/pdf/2303.13798"],
        "report_link" : ["", "", ""]
    }
    df = pd.DataFrame(data)
    return df

iface = gr.Interface(
    fn=plagiarism_checker,
    inputs=gr.Textbox(show_copy_button=True, label="Enter Authors Name"),
    outputs=gr.Dataframe(headers=["Paper Name", "Paper id", "Paper Link", "Report link"]),
    title="Arxiv author's plagiarism check just by entering the arxiv author",
    description="Arxiv Plagiarism Checker LLM - Enter Authors Name",
)

iface.launch()
