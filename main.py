import streamlit as st
import urllib.request
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from groq import Groq
from scraping import scrape_url

import os
from dotenv import load_dotenv


# Load the .env file
load_dotenv()

# Access the API key
api_key = os.getenv("api_key")

# Initialize Streamlit app settings
st.set_page_config(page_title="Chat with Any Website", page_icon="🧭", layout="wide")

# Initialize Groq client
client_groq = Groq(api_key=api_key)

# Initialize Chroma vector database client
client_db = chromadb.Client()

# Collection name
collection_name = "website_embeddings"

global collection
existing_collections = client_db.list_collections()
if collection_name  in [col.name for col in existing_collections]:
    collection = client_db.get_collection(name=collection_name)
else:
    collection = client_db.create_collection(name=collection_name)

# Load the pre-trained SentenceTransformer model for generating embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Set to store visited URLs
visited_urls = set()

# Streamlit UI Components
st.title("Chat with Any Website 🧭💬")
st.sidebar.title("Settings")
website_url = st.sidebar.text_input("Enter a URL...")

# Function to chunk text content into smaller pieces
def chunk_text(text, max_words=100):
    words = text.split()
    chunks = [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]
    return chunks

# Function to embed and store text chunks in Chroma database
def embed_and_store_chunks(page_title, page_url, text_chunks):
    embeddings = model.encode(text_chunks)
    metadata = [{"page_title": page_title, "url": page_url, "chunk_index": idx} for idx in range(len(text_chunks))]
    collection.add(
        embeddings=embeddings,
        metadatas=metadata,
        documents=text_chunks,
        ids=[f"{page_title}_chunk_{idx}" for idx in range(len(text_chunks))]
    )

# Recursive scraping function to get all pages linked from a given URL
def scrape_website_recursively(base_url, url, link_text='Home', max_depth=1, current_depth=0):
    if current_depth > max_depth or url in visited_urls:
        return
    visited_urls.add(url)
    st.write(f"Scraping: {url} (Depth: {current_depth})")
    text_content,soup = scrape_url(url)
    if not soup or not text_content.strip():
        return
    text_chunks = chunk_text(text_content)
    embed_and_store_chunks(link_text, url, text_chunks)
    for link in soup.find_all('a', href=True):
        link_url = link.get('href')
        link_text = link.get_text(strip=True) or 'No Title'
        if link_url.startswith('http'):
            scrape_website_recursively("", link_url, link_text, max_depth, current_depth + 1)
        else:
            full_url = urljoin(base_url, link_url)
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                scrape_website_recursively(base_url, full_url, link_text, max_depth, current_depth + 1)

# Function to retrieve relevant chunks based on user query
def retrieve_relevant_chunks(query, top_k=5):
    query_embedding = model.encode([query])
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)
    retrieved_text = " ".join([doc for doc in results['documents'][0]])
    return retrieved_text

# Function to chat with Groq using the retrieved context
from groq import Groq
client = Groq(api_key= api_key)

def chat_with_groq(question:str, context:str):
    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": 
            f""" you are a helpful assistant that answers questions strictly from the given context passage below and if no relevant information is present in the given passage respond with 'I don't Know'
            
            ### Context:
            {context}
            
            """
        },
        # Set a user message for the assistant to respond to.
        {
            "role": "user",
            "content": question,
        }
    ],

    # The language model which will generate the completion.
    model="llama-3.1-70b-versatile",
    temperature=0.3,
    max_tokens=2048,
    top_p=1,
    stop=None,
    stream=False,
)
    return chat_completion.choices[0].message.content

# Trigger scraping and embedding when a URL is provided
if st.sidebar.button("Start Scraping") and website_url:
    st.write(f"Starting to scrape the website: {website_url}")
    existing_collections = client_db.list_collections()
    if collection_name  in [col.name for col in existing_collections]:
        collection = client_db.delete_collection(name=collection_name)
    
    collection = client_db.create_collection(name=collection_name)
    scrape_website_recursively(website_url, website_url, link_text='Home')
    st.write("Scraping and embedding completed.")

# Retrieve and answer queries based on scraped content
question = st.text_input("Ask a question about the website content...")
if st.button("Get Answer") and question:
    st.write(f"Question: {question}")
    context = retrieve_relevant_chunks(question)
    if context:
        response = chat_with_groq(question, context)
        st.write(f"Answer: {response}")
    else:
        st.write("No relevant information found in the scraped content.")