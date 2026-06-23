'''
This is document ingestion pipeline
Steps===
->load_documents
->process_document_chunking
->add_metadata
->store_in_vector_db
Use langchain document_loader to load PDF documents for simplicity and auto matic metadata embeddings into chunks
'''

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from rag_config import connection, collection_name,embeddings_model



'''
Use langchain document_loader to load PDF documents for simplicity and auto matic metadata embeddings into chunks
'''

def load_documents():
    print("Loading documents...")
    pdf_path = "documents/AWS-Certified-AI-Practitioner_Exam-Guide.pdf"
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    '''
    ## Each page becomes a Document object.
    returns documents = [
        Document(page_content="Page 1 text...", metadata={"page": 0}),
        Document(page_content="Page 2 text...", metadata={"page": 1}),
        ...
    ]
    '''
    print("Total pages:", len(documents))
    return  documents


import re

def clean_text(text):
    text = re.sub(r"\(cid:\d+\)", "•", text)
    return text

def process_document_chunking(documents):
    print("Processing document chunking...")
    '''
    perform cleaning the texts
    '''
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " "],
    )

    chunks = splitter.split_documents(documents) ## we are using split_documents and not split_text
    print("Total chunks:", len(chunks))
    return chunks

import hashlib

def compute_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def add_metadata(chunks):
    print("Adding metadata to cunks...")
    '''
    function to add metadata to each chunk
    '''
    for chunk in chunks:
        chunk.metadata["exam"] = "AWS Certified AI Practitioner"
        chunk.metadata["source"] = "AWS-Certified-AI-Practitioner_Exam-Guide.pdf"
        chunk.metadata["doc_hash"]  = compute_hash(chunk.page_content)
        chunk.metadata["page"] = chunk.metadata.get("page")
    return chunks



def store_in_vector_db(chunks):
    print("Storing chunks in vector database...")
    vectorstore = PGVector.from_documents(
        documents=chunks,
        embedding=embeddings_model,
        collection_name=collection_name,
        connection=connection,
        pre_delete_collection=True  # reset collection during development
    )
    print("Documents stored in PGVector successfully.")
    return vectorstore

def print_chunk_metadata(chunks):
    ## display chunk content and metadata
    print("DISPLAY CHUNKS")
    print("===" * 20)
    i = 0;
    for chunk in chunks:
        i = i + 1
        print(f"chunk No: {i}")
        print(chunk.metadata)
        print(chunk.page_content)
        print("*" * 20)

def process_data_ingestion():
    print("processing data ingestion...")
    documents = load_documents()
    chunks = process_document_chunking(documents)
    chunks = add_metadata(chunks)
    print_chunk_metadata(chunks)

    vectorstore = store_in_vector_db(chunks)
    print("data ingestion completed...")
    return chunks, vectorstore

if __name__ == '__main__':
    process_data_ingestion();









