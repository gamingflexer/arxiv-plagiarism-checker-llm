import json
import logging
from typing import Optional
import re
import requests
from requests.adapters import HTTPAdapter, Retry
import arxiv
import PyPDF2
import requests
import time
from operator import itemgetter
import fitz
from tqdm import tqdm
from langchain.text_splitter import CharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions
import os
import asyncio
import uuid 
from langchain.text_splitter import CharacterTextSplitter

emmbedding_model = "text-embedding-3-large"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

dir = "arxiv-data/2023"
chunk_size = 20

openai_ef = embedding_functions.OpenAIEmbeddingFunction(model_name=emmbedding_model,api_key=OPENAI_API_KEY)
# chroma_client = chromadb.HttpClient(host='localhost', port=8000) # use this if you are using chroma server Docker
chroma_client = chromadb.PersistentClient(path="/home/ubuntu/research/data/emeddeings")

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=3000, chunk_overlap=0
)

collection_doc = chroma_client.get_or_create_collection(name="2024_main_document_lvl")
collection_para = chroma_client.get_or_create_collection(name="2024_main_paragraph_lvl")


def background(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, **kwargs)

    return wrapped

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
        try:
            self._download_meta()
            if save:
                self.save()
        except Exception as e:
            print(f"Error while downloading paper {self.id}: {e}")
            raise e

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
        self.authors = " ".join([author.name for author in result.authors])
        self.journal_ref = result.journal_ref
        self.source = result.pdf_url
        self.summary = result.summary
        self.title = result.title
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
        # fields.pop('content')
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
            'references': " ".join(self.references)
        }
    
    def __repr__(self):
        return f"Arxiv(paper_id='{self.id}')"

def fonts(doc, granularity=False):
    """Extracts fonts and their usage in PDF documents.

    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param granularity: also use 'font', 'flags' and 'color' to discriminate text
    :type granularity: bool

    :rtype: [(font_size, count), (font_size, count}], dict
    :return: most used fonts sorted by count, font style information
    """
    styles = {}
    font_counts = {}

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # block contains text
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if granularity:
                            identifier = "{0}_{1}_{2}_{3}".format(s['size'], s['flags'], s['font'], s['color'])
                            styles[identifier] = {'size': s['size'], 'flags': s['flags'], 'font': s['font'],
                                                  'color': s['color']}
                        else:
                            identifier = "{0}".format(s['size'])
                            styles[identifier] = {'size': s['size'], 'font': s['font']}

                        font_counts[identifier] = font_counts.get(identifier, 0) + 1  # count the fonts usage

    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)

    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")

    return font_counts, styles


def font_tags(font_counts, styles):
    """Returns dictionary with font sizes as keys and tags as value.

    :param font_counts: (font_size, count) for all fonts occuring in document
    :type font_counts: list
    :param styles: all styles found in the document
    :type styles: dict

    :rtype: dict
    :return: all element tags based on font-sizes
    """
    p_style = styles[font_counts[0][0]]  # get style for most used font by count (paragraph)
    p_size = p_style['size']  # get the paragraph's size

    # sorting the font sizes high to low, so that we can append the right integer to each tag
    font_sizes = []
    for (font_size, count) in font_counts:
        font_sizes.append(float(font_size))
    font_sizes.sort(reverse=True)

    # aggregating the tags for each font size
    idx = 0
    size_tag = {}
    for size in font_sizes:
        idx += 1
        if size == p_size:
            idx = 0
            size_tag[size] = '<p>'
        if size > p_size:
            size_tag[size] = '<h{0}>'.format(idx)
        elif size < p_size:
            size_tag[size] = '<s{0}>'.format(idx)

    return size_tag


def headers_para(doc, size_tag):
    """Scrapes headers & paragraphs from PDF and return texts with element tags.

    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param size_tag: textual element tags for each size
    :type size_tag: dict

    :rtype: list
    :return: texts with pre-prended element tags
    """
    paragraphs = []  # list with paragraphs
    first = True  # boolean operator for first header
    previous_s = {}  # previous span

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # this block contains text

                # REMEMBER: multiple fonts and sizes are possible IN one block

                block_string = ""  # text found in block
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if s['text'].strip():  # removing whitespaces:
                            if first:
                                previous_s = s
                                first = False
                                block_string = s['text'] if size_tag[s['size']] == '<p>' else ''
                            else:
                                if s['size'] == previous_s['size']:
                                    if block_string:  # in the same block, so concatenate strings
                                        block_string += " " + s['text']
                                else:
                                    if block_string:  # new block has started, so append the paragraph
                                        paragraphs.append(block_string)
                                    block_string = s['text'] if size_tag[s['size']] == '<p>' else ''

                                previous_s = s

                if block_string:  # append the last paragraph in the block
                    if len(block_string) > 80:
                        # print(len(block_string), block_string,'\n')
                        paragraphs.append(block_string)

    return paragraphs

def get_pdf_info(document_path):
    docs = fitz.open(document_path)
    only_text = ""
    for page in docs:
        only_text += page.get_text() + " "
    font_counts, styles = fonts(docs, granularity=False)
    size_tag = font_tags(font_counts, styles)
    elements = headers_para(docs, size_tag)
    paragraphs = []
    for element in elements:
        if len(element) > 100: 
            paragraphs.append(element.lower())
    pattern = r'\d+(\.\d+)?\n'
    cleaned_text = re.sub(pattern, '', only_text)
    return cleaned_text.lower(),paragraphs

def generate_uuid():
    return str(uuid.uuid4())

def add_document_chroma_collection(collection_object, document_list, embedding_list, metadata):
    
    metadata_list = [metadata for i in range(len(document_list))]
    ids_gen = [generate_uuid() for i in range(len(document_list))]
    collection_object.add(embeddings = embedding_list,documents = document_list,metadatas = metadata_list,ids = ids_gen)
    if collection_object:
        return True
    
def chunk_list(input_list, chunk_size):
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]

directories_2023 = [ os.path.join(dir, o) for o in os.listdir(dir) if os.path.isdir(os.path.join(dir,o)) ]


@background
def task(chunk):
    chunked_files = [os.path.join(single_dir, file) for file in chunk]
    # print("len of chunked_files", len(chunked_files))
    for file_path in (chunked_files):
        try:
            paper_id = file_path.split("/")[-1].split(".pdf")[0].replace("v1", "").replace("v2", "").replace("v3", "").replace("v4", "").replace("v5", "")
            # print("paper_id", paper_id)
            paper = Arxiv(paper_id)
            paper.load()
            metadata = paper.get_meta()
            only_text,paragraphs = get_pdf_info(file_path)
            texts_list = text_splitter.split_text(only_text)
            if len(texts_list) > 0:
                doc_embed = openai_ef(texts_list)
                add_document_chroma_collection(collection_doc, texts_list, doc_embed,metadata)
            if len(paragraphs) > 0:
                paragraphs_embed = openai_ef(paragraphs)
                add_document_chroma_collection(collection_para, paragraphs, paragraphs_embed,metadata)
            time.sleep(5)
        except Exception as e:
            print("Error", e)
            with open("error.txt", "a") as f:
                f.write(file_path)
            continue
        
for single_dir in directories_2023:
    print("len of files", len(os.listdir(single_dir)))
    chunked_list = chunk_list(os.listdir(single_dir), 20)
    print("len of chunked_list", len(chunked_list))
    for chunk in tqdm(chunked_list):
        task(chunk)
        time.sleep(5)