from prompts.templates import reference_extraction
from scrapper.arxiv import get_paper_id,Arxiv
from scrapper.extractor import get_google_scrape,init_extractor
from tqdm import tqdm
import os

class ArxivPaper:

    def __init__(self, author_name: str):
        self.author_name = author_name
        self.extractor, self.text_splitter = init_extractor(template=reference_extraction['template'], openai_api_key=OPENAI_API_KEY)
    
    def get_results_google(self, number_of_results: int = 25):
        result_dict = get_google_scrape(self.author_name +" research papers arxiv.org",num=number_of_results)
        paper_links = []
        for i in result_dict['organic_results']:
            if "arxiv.org" in i['link']:
                paper_links.append(i['link'])
        print(f"Found {len(paper_links)} papers")
        return paper_links
    
    def get_paper_id(self, paper_link: list):
        paper_ids = []
        for i in paper_link:
            if "arxiv.org" in i:
                if "pdf" in i:
                    paper_ids.append(i.split("/")[-1].split(".pdf")[0])
                else:
                    paper_ids.append(i.split("/")[-1])
        if '' in paper_ids:
            paper_ids.remove('')
        return list((paper_ids))
    
    def get_paper_details_batch(self, paper_ids: list, path: str = "./data/papers"):
        path_author = os.path.join(path, self.author_name.replace(" ", "_"))
        for i in tqdm(paper_ids):
            paper = Arxiv(i)
            paper.load()
            paper.get_meta()
            refs = paper.get_refs(
            extractor=self.extractor,
            text_splitter=self.text_splitter,)
            paper.chunker()
            paper.save_chunks(include_metadata=True, path=path_author)