import os
import json
import logging
from typing import Optional
import re
import requests
from requests.adapters import HTTPAdapter, Retry
import arxiv
import PyPDF2
import requests
from tqdm.auto import tqdm
from decouple import config

"""
Usage : get_paper_id("8-bit matrix multiplication for transformers at scale") -> 2106.09680
"""

paper_id_re = re.compile(r'https://arxiv.org/abs/(\d+\.\d+)')

def retry_request_session(retries: Optional[int] = 5):
    # we setup retry strategy to retry on common errors
    retries = Retry(
        total=retries,
        backoff_factor=0.1,
        status_forcelist=[
            408,  # request timeout
            500,  # internal server error
            502,  # bad gateway
            503,  # service unavailable
            504   # gateway timeout
        ]
    )
    # we setup a session with the retry strategy
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def get_paper_id(query: str, handle_not_found: bool = True):
    """Get the paper ID from a query.

    :param query: The query to search with
    :type query: str
    :param handle_not_found: Whether to return None if no paper is found,
                             defaults to True
    :type handle_not_found: bool, optional
    :return: The paper ID
    :rtype: str
    """
    special_chars = {
        ":": "%3A",
        "|": "%7C",
        ",": "%2C",
        " ": "+"
    }
    # create a translation table from the special_chars dictionary
    translation_table = query.maketrans(special_chars)
    # use the translate method to replace the special characters
    search_term = query.translate(translation_table)
    # init requests search session
    session = retry_request_session()
    # get the search results
    res = session.get(f"https://www.google.com/search?q={search_term}&sclient=gws-wiz-serp")
    try:
        # extract the paper id
        paper_id = paper_id_re.findall(res.text)[0]
    except IndexError:
        if handle_not_found:
            # if no paper is found, return None
            return None
        else:
            # if no paper is found, raise an error
            raise Exception(f'No paper found for query: {query}')
    return paper_id


class Arxiv:
    refs_re = re.compile(r'\n(References|REFERENCES)\n')
    references = []
    
    llm = None

    def __init__(self, paper_id: str):
        """Object to handle the extraction of an ArXiv paper and its
        relevant information.
        
        :param paper_id: The ID of the paper to extract
        :type paper_id: str
        """
        self.id = paper_id
        self.url = f"https://export.arxiv.org/pdf/{paper_id}.pdf"
        # initialize the requests session
        self.session = requests.Session()
    
    def load(self, save: bool = False):
        """Load the paper from the ArXiv API or from a local file
        if it already exists. Stores the paper's text content and
        meta data in self.content and other attributes.
        
        :param save: Whether to save the paper to a local file,
                     defaults to False
        :type save: bool, optional
        """
        # check if pdf already exists
        if os.path.exists(f'papers/{self.id}.json'):
            print(f'Loading papers/{self.id}.json from file')
            with open(f'papers/{self.id}.json', 'r') as fp:
                attributes = json.loads(fp.read())
            for key, value in attributes.items():
                setattr(self, key, value)
        else:
            res = self.session.get(self.url)
            with open(f'temp.pdf', 'wb') as fp:
                fp.write(res.content)
            # extract text content
            self._convert_pdf_to_text()
            # get meta for PDF
            self._download_meta()
            if save:
                self.save()

    def get_refs(self, extractor, text_splitter):
        """Get the references for the paper.

        :param extractor: The LLMChain extractor model
        :type extractor: LLMChain
        :param text_splitter: The text splitter to use
        :type text_splitter: TokenTextSplitter
        :return: The references for the paper
        :rtype: list
        """
        if len(self.references) == 0:
            self._download_refs(extractor, text_splitter)
        return self.references
        
    def _download_refs(self, extractor, text_splitter):
        """Download the references for the paper. Stores them in
        the self.references attribute.

        :param extractor: The LLMChain extractor model
        :type extractor: LLMChain
        :param text_splitter: The text splitter to use
        :type text_splitter: TokenTextSplitter
        """
        # get references section of paper
        refs = self.refs_re.split(self.content)[-1]
        # we don't need the full thing, just the first page
        refs_page = text_splitter.split_text(refs)[0]
        # use LLM extractor to extract references
        out = extractor.run(refs=refs_page)
        out = out.split('\n')
        out = [o for o in out if o != '']
        # with list of references, find the paper IDs
        ids = [get_paper_id(o) for o in out]
        # clean up into JSONL type format
        out = [o.split(' | ') for o in out]
        # in case we're missing some fields
        out = [o for o in out if len(o) == 3]
        meta = [{
            'id': _id,
            'title': o[0],
            'authors': o[1],
            'year': o[2]
        } for o, _id in zip(out, ids) if _id is not None]
        logging.debug(f"Extracted {len(meta)} references")
        self.references = meta
    
    def _convert_pdf_to_text(self):
        """Convert the PDF to text and store it in the self.content
        attribute.
        """
        text = []
        with open("temp.pdf", 'rb') as f:
            # create a PDF object
            pdf = PyPDF2.PdfReader(f)
            # iterate over every page in the PDF
            for page in range(len(pdf.pages)):
                # get the page object
                page_obj = pdf.pages[page]
                # extract text from the page
                text.append(page_obj.extract_text())
        text = "\n".join(text)
        self.content = text

    def _download_meta(self):
        """Download the meta information for the paper from the
        ArXiv API and store it in the self attributes.
        """
        search = arxiv.Search(
            query=f'id:{self.id}',
            max_results=1,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        result = list(search.results())
        if len(result) == 0:
            raise ValueError(f"No paper found for paper '{self.id}'")
        result = result[0]
        # remove 'v1', 'v2', etc. from the end of the pdf_url
        result.pdf_url = re.sub(r'v\d+$', '', result.pdf_url)
        self.authors = [author.name for author in result.authors]
        self.categories = result.categories
        self.comment = result.comment
        self.journal_ref = result.journal_ref
        self.source = result.pdf_url
        self.primary_category = result.primary_category
        self.published = result.published.strftime('%Y%m%d')
        self.summary = result.summary
        self.title = result.title
        self.updated = result.updated.strftime('%Y%m%d')
        logging.debug(f"Downloaded metadata for paper '{self.id}'")

    def save(self):
        """Save the paper to a local JSON file.
        """
        with open(f'papers/{self.id}.json', 'w') as fp:
            json.dump(self.__dict__(), fp, indent=4)

    def save_chunks(
        self,
        include_metadata: bool = True,
        path: str = "chunks"
        ):
        """Save the paper's chunks to a local JSONL file.
        
        :param include_metadata: Whether to include the paper's
                                 metadata in the chunks, defaults
                                 to True
        :type include_metadata: bool, optional
        :param path: The path to save the file to, defaults to "papers"
        :type path: str, optional
        """
        if not os.path.exists(path):
            os.makedirs(path)
        with open(f'{path}/{self.id}.jsonl', 'w') as fp:
            for chunk in self.dataset:
                if include_metadata:
                    chunk.update(self.get_meta())
                fp.write(json.dumps(chunk) + '\n')
            logging.debug(f"Saved paper to '{path}/{self.id}.jsonl'")
    
    def get_meta(self):
        """Returns the meta information for the paper.

        :return: The meta information for the paper
        :rtype: dict
        """
        fields = self.__dict__()
        # drop content field because it's big
        fields.pop('content')
        return fields
    
    def chunker(self, chunk_size=300):
        # Single Chunk is made for now
        clean_paper = self._clean_text(self.content)
        langchain_dataset = []
        langchain_dataset.append({
                'doi': self.id,
                'chunk-id': 1,
                'chunk': clean_paper
            })
        self.dataset = langchain_dataset

    def _clean_text(self, text):
        text = re.sub(r'-\n', '', text)
        return text

    def __dict__(self):
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'source': self.source,
            'authors': self.authors,
            'categories': self.categories,
            'comment': self.comment,
            'journal_ref': self.journal_ref,
            'primary_category': self.primary_category,
            'published': self.published,
            'updated': self.updated,
            'content': self.content,
            'references': self.references
        }
    
    def __repr__(self):
        return f"Arxiv(paper_id='{self.id}')"