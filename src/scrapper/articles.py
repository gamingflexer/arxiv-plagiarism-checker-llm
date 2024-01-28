from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer

class GetSimilarArticles:
    
    def __init__(self, paper_title_name: str):
        self.paper_title_name = paper_title_name
        