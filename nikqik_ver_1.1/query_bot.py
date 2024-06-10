#!/usr/bin/env python3
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from langchain.llms import Ollama
import chromadb
import os
import argparse
import time
import pandas as pd
import glob

# Make sure the results directory exist
RESULTS_FOLDER = 'results'
QUERY_FOLDER = 'query_documents'

if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

model = os.environ.get("MODEL", "mistral")
# For embeddings model, the example uses a sentence-transformers model
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
persist_directory = os.environ.get("PERSIST_DIRECTORY", "db")
target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS', 4))

from constants import CHROMA_SETTINGS


def main():
    # Parse the command line arguments
    args = parse_arguments()
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

    db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
    # activate/deactivate the streaming StdOut callback for LLMs
    callbacks = [] if args.mute_stream else [StreamingStdOutCallbackHandler()]

    llm = Ollama(model=model, callbacks=callbacks)

    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever,
                                    return_source_documents= not args.hide_source)

    # Read questions from all files in the 'query_documents' directory
    for filepath in glob.glob(os.path.join(QUERY_FOLDER, '*')):
        with open(filepath, 'r') as file:
            questions = file.readlines()

        for query in questions:
            if query.strip() == "":
                continue

            # Get the answer from the chain
            start = time.time()
            res = qa(query)
            answer, docs = res['result'], [] if args.hide_source else res['source_documents']
            end = time.time()

            # Save the question and answer into an Excel file
            df = pd.DataFrame({'Question': [query], 'Response': [answer]})
            df.to_csv(os.path.join(RESULTS_FOLDER, 'results.csv'), mode='a', index=False)


def parse_arguments():
    parser = argparse.ArgumentParser(description='privateGPT: Ask questions to your documents without an internet connection, '
                                                'using the power of LLMs.')
    parser.add_argument("--hide-source", "-S", action='store_true',
                        help='Use this flag to disable printing of source documents used for answers.')

    parser.add_argument("--mute-stream", "-M",
                        action='store_true',
                        help='Use this flag to disable the streaming StdOut callback for LLMs.')

    return parser.parse_args()


if __name__ == "__main__":
    main()