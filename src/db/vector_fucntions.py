from config import *
import chromadb
from chromadb.utils import embedding_functions
from config import OPENAI_API_KEY
from utils import generate_uuid

emmbedding_model = "text-embedding-3-large"
openai_ef = embedding_functions.OpenAIEmbeddingFunction(model_name=emmbedding_model,api_key=OPENAI_API_KEY)
if deploy:
    chroma_client = chromadb.PersistentClient(path="./data/emeddeings")
else:
    chroma_client = chromadb.PersistentClient(path="/home/ubuntu/research/data/emeddeings")
    
collection_doc = chroma_client.get_or_create_collection(name="2024_main_document_lvl")
collection_para = chroma_client.get_or_create_collection(name="2024_main_paragraph_lvl")

def add_document_chroma_collection(collection_object, document_list, embedding_list, metadata):
    
    metadata_list = [metadata for i in range(len(document_list))]
    ids_gen = [generate_uuid() for i in range(len(document_list))]
    collection_object.add(embeddings = embedding_list,documents = document_list,metadatas = metadata_list,ids = ids_gen)
    if collection_object:
        return True
    