# StockHelper

## Overview

StockHelper is a Python-based financial document analysis tool focused on SEC filings. It fetches, processes, and embeds large financial documents using Large Language Models (LLMs) and vector databases to enable advanced natural language querying about company prospects.

---

## Features

- Asynchronously retrieves SEC filings for specified companies using official SEC APIs and web scraping  
- Extracts structured data including tables and textual chunks from filings  
- Processes and cleans raw HTML filings into chunks optimized for LLM embeddings  
- Stores embeddings in a local persistent vector database (ChromaDB) integrated with `llama_index` and `Ollama` LLMs  
- Supports natural language querying on financial data with contextual responses  
- Modular, asynchronous design for efficient data processing

---

## Design Details

### SEC Data Processing

- Uses `sec_edgar_api` to fetch filings asynchronously from SEC EDGAR  
- Loads company tickers and maps to SEC CIK for accurate filing retrieval  
- Supports both REST API and Selenium-driven scraping for complex filings

### Data Preprocessing

- Cleans and parses HTML filings with BeautifulSoup  
- Extracts tables into structured pandas DataFrames with positional metadata  
- Separates raw text and chunkifies it for embedding using `llama_index`’s TokenTextSplitter  
- Fully async text cleaning pipeline for performance

### Vector Database & Querying

- Uses ChromaDB as a persistent vector store  
- Wraps ChromaDB with `llama_index` abstractions for LLM retrieval integration  
- Embeddings powered by `Ollama` LLM and custom embed models  
- Enables natural language queries with detailed context-aware responses

---
