from langchain_community.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
from typing import Union
from config import OPENAI_API_KEY, SERP_API_KEY
import os
from serpapi import GoogleSearch

def get_google_scrape(query, api_key = SERP_API_KEY, num = 25):
    search = GoogleSearch({
        "q": query,
        "api_key": api_key,
        "start": "1",
        "end": "10",
        "num": num,
    })
    result = search.get_dict()
    return result

def init_extractor(
    template: str,
    openai_api_key: Union[str, None] = None,
    max_tokens: int = 1000,
    chunk_size: int = 300,
    chunk_overlap: int = 40
):
    if openai_api_key is None and 'OPENAI_API_KEY' not in os.environ:
        raise Exception('No OpenAI API key provided')
    openai_api_key = openai_api_key or os.environ['OPENAI_API_KEY']
    # instantiate the OpenAI API wrapper
    llm = ChatOpenAI(
        model_name='gpt-3.5-turbo-16k',
        openai_api_key=OPENAI_API_KEY,
        max_tokens=max_tokens,
        temperature=0.0
    )
    # initialize prompt template
    prompt = PromptTemplate(
        template=template,
        input_variables=['refs']
    )
    # instantiate the LLMChain extractor model
    extractor = LLMChain(
        prompt=prompt,
        llm=llm
    )
    
    text_splitter = tiktoken_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return extractor, text_splitter

def tiktoken_splitter(chunk_size=300, chunk_overlap=40):
    tokenizer = tiktoken.get_encoding('p50k_base')
    # create length function
    def len_fn(text):
        tokens = tokenizer.encode(
            text, disallowed_special=()
        )
        return len(tokens)
    # initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len_fn,
        separators=["\n\n", "\n", " ", ""]
    )
    return text_splitter