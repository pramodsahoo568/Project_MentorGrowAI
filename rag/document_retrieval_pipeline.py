'''
This is document retrieval pipeline
'''

from langchain_postgres import PGVector
from rag.rag_config import connection, collection_name,embeddings_model
import threading
## crate a global vector store and initialize it once
## This is Singleton vector store implementation
## implement thread lock mechanism to avoid simultaneous initialisation


_vector_store = None
_lock = threading.Lock()

def get_vector_store():
    global _vector_store

    if _vector_store is None:
        with _lock:  # ensure only one thread creates it
            if _vector_store is None:
                print("Initializing PGVector store...")
                _vector_store = PGVector(
                    connection=connection,
                    collection_name=collection_name,
                    embeddings=embeddings_model,
                )

    return _vector_store


def retrieve_results(query):
    print("Retrieving results...")
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(query, k=3)
    return results


if __name__ == '__main__':
    query = "What is Domain 1: Fundamentals of AI and ML?"
    results = retrieve_results(query);

    print(f"\nTotal retrieved chunks: {len(results)}")

    for idx, (doc, score) in enumerate(results, start=1):
        print("=" * 60)
        print(f"Chunk Rank: {idx}")
        print(f"Similarity Score: {score:.4f}")
        print(f"Page: {doc.metadata.get('page')}")
        print(f"Content Preview:\n{doc.page_content[:300]}")
        print("=" * 60)








