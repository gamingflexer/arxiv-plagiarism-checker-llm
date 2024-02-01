import os
import arxiv
from plagiarism.preprocessing import get_pdf_info
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import OPENAI_API_KEY
from scrapper.extractor import get_google_scrape
from utils import extract_json_from_text, check_id_extis_in_json, generate_uuid,text_splitter
from db.vector_fucntions import add_document_chroma_collection
from prompts.templates import prompt_unquiness_para, google_search_titles
from scrapper.main import ArxivPaper
from config import *
from db.db_functions import get_correct_author_name
from db.vector_fucntions import collection_doc, collection_para, openai_ef


"""
author_check = ArxivPaperAuthorPlagiarismCheck("Abney, Steven F", 3)
author_check.process_papers()
similar_paper_ids = author_check.find_similar_papers()
author_check.add_embeddings_to_db(similar_paper_ids)
"""

class ArxivPaperAuthorPlagiarismCheck:
    
    def __init__(self, author_name, num_results):
        self.author_name = author_name
        self.num_results = num_results
        self.author_obj = ArxivPaper(self.author_name)
        self.db_author_name = get_correct_author_name(self.author_name)
        self.paper_links = self.author_obj.get_results_google(number_of_results=self.num_results)
        self.paper_ids = self.author_obj.get_paper_id(self.paper_links)
        self.data_papers = self.author_obj.get_paper_details_batch(self.paper_ids)

    def process_papers(self):
        
        prompt_unquiness = ChatPromptTemplate.from_template(prompt_unquiness_para)

        output_parser_1 = StrOutputParser()
        model = ChatOpenAI(model="gpt-4", api_key=OPENAI_API_KEY)
        chain_unquine = (
            {"title": RunnablePassthrough(), "summary": RunnablePassthrough(), "text": RunnablePassthrough()}
            | prompt_unquiness
            | model
            | output_parser_1
        )

        for single_paper in self.data_papers:
            paper = next(arxiv.Client().results(arxiv.Search(id_list=[single_paper['id']])))
            file_name = single_paper['id'] + ".pdf"
            to_save_path = os.path.join("./data_temp/")
            paper.download_pdf(dirpath=to_save_path, filename=file_name)
            only_text, paragraphs = get_pdf_info(to_save_path + file_name)
            response = chain_unquine.invoke({"title": single_paper['title'], "summary": single_paper['summary'], "text": str(paragraphs)})
            response_list = extract_json_from_text(response)
            single_paper['unique_paragraphs'] = response_list

    def find_similar_papers(self):
        prompt_relavent_title = ChatPromptTemplate.from_template(google_search_titles)
        output_parser_2 = StrOutputParser()
        model = ChatOpenAI(model="gpt-4", api_key=OPENAI_API_KEY)
        chain = (
            {"title": RunnablePassthrough(), "summary": RunnablePassthrough()}
            | prompt_relavent_title
            | model
            | output_parser_2
        )

        for single_paper in self.data_papers:
            title = single_paper['title']
            summary = single_paper['summary']
            response = chain.invoke({"title": title, "summary": summary})
            search_list = extract_json_from_text(response)
            if search_list is not None:
                search_list = search_list[:3]
            paper_links_similar = []
            for search in search_list:
                result_dict = get_google_scrape(search)
                for i in result_dict['organic_results']:
                    if "arxiv.org" in i['link']:
                        paper_links_similar.append(i['link'])

        similar_paper_ids = []
        for paper_link in paper_links_similar:
            paper_id = paper_link.split("/")[-1]
            similar_paper_ids.append(paper_id)

        return similar_paper_ids

    def add_embeddings_to_db(self, similar_paper_ids):
        meta_data_similar_papers = self.author_obj.get_paper_details_batch(similar_paper_ids)

        to_save_path = os.path.join(f"./data_temp/{str(generate_uuid())}/")
        if not os.path.exists(to_save_path):
            os.makedirs(to_save_path)

        for single_paper in meta_data_similar_papers:
            if not check_id_extis_in_json(single_paper['id']):
                paper = next(arxiv.Client().results(arxiv.Search(id_list=[single_paper['id']])))
                file_name = single_paper['id'] + ".pdf"
                paper.download_pdf(dirpath=to_save_path, filename=file_name)
                texts_data, paragraphs = get_pdf_info(to_save_path + file_name)
                texts_list = text_splitter.split_text(texts_data)
                single_paper['text'] = texts_list
                single_paper['paragraphs'] = paragraphs

                metadata = {
                    "title": single_paper['title'],
                    "summary": single_paper['summary'],
                    "authors": " ".join(single_paper['authors']),
                    "categories": " ".join(single_paper['categories']),
                    "id": single_paper['id']
                }

                if len(texts_list) > 0:
                    doc_embed = openai_ef(texts_list)
                    add_document_chroma_collection(collection_doc, texts_list, doc_embed, metadata)
                if len(paragraphs) > 0:
                    paragraphs_embed = openai_ef(paragraphs)
                    add_document_chroma_collection(collection_para, paragraphs, paragraphs_embed, metadata)
