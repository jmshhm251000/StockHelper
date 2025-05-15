import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.indices.query.schema import QueryBundle
from llama_index.core.settings import Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores.types import MetadataInfo, VectorStoreInfo
import os
import uuid


class vectordb:
    def __init__(self, embed_model):
        self.chroma_client = chromadb.PersistentClient(path=os.path.join(os.getcwd(), "chroma_db"))
        self.collection = self.chroma_client.get_or_create_collection(name="sec_filings", metadata={"hnsw:space": "ip"})
        print(self.collection.count())

        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store, embed_model=embed_model)

        self.vector_store_info = VectorStoreInfo(
            content_info="Segments of SEC filings, including various forms such as 10-K, 10-Q, and S-1, divided into manageable chunks for analysis.",
            metadata_info=[
                MetadataInfo(
                    name="company_name",
                    type="str",
                    description="The name of the company that submitted the SEC filing."
                ),
                MetadataInfo(
                    name="form_type",
                    type="str",
                    description="The type of SEC form filed, e.g., 10-K, 10-Q, S-1."
                ),
                MetadataInfo(
                    name="date",
                    type="str",
                    description="The date when the report was filed."
                ),
                MetadataInfo(
                    name="page_number",
                    type="int",
                    description="The page number in the original document where this chunk is located."
                ),
                MetadataInfo(
                    name="chunk_char_count",
                    type="int",
                    description="The number of characters in this chunk of text."
                ),
                MetadataInfo(
                    name="chunk_word_count",
                    type="int",
                    description="The number of words in this chunk of text."
                ),
                MetadataInfo(
                    name="chunk_sentence_count_raw",
                    type="int",
                    description="The raw count of sentences in this chunk."
                ),
                MetadataInfo(
                    name="chunk_token_count",
                    type="int",
                    description="The number of tokens in this chunk, useful for NLP processing."
                ),
            ],
        )

        self.system_prompt =self.system_prompt = """You are an AI financial analyst specializing in SEC filings analysis.

### Instructions:
- Summarize the company's **financial performance**, including revenue, profit margins, cash flow, and expenses.
- Identify and assess **risk factors** mentioned in the SEC filings.
- Compare the current filing with **previous filings**, highlighting significant changes.
- Analyze **market trends** affecting the company's future.
- Provide a **forecast** on potential stock price movements based on the filing.
- Deliver a final investment recommendation: **Buy, Hold, or Sell**, with justifications.

### Response Format (JSON Output):
{
    "summary": {
        "financial_performance": "<Key financial metrics and trends>",
        "risk_factors": "<Major risks impacting the company>",
        "market_trends": "<Broader market trends affecting the company>",
        "comparison": "<Changes compared to previous filings>"
    },
    "analysis": {
        "forecast": "<Predicted stock performance based on filings and trends>",
        "recommendation": "<Decision: Buy, Hold, or Sell, with reasoning>"
    }
}

### Guidelines:
- Base responses strictly on retrieved SEC filings, avoiding speculation.
- Ensure factual accuracy by cross-referencing retrieved information.
- If a required data point is **not found in the retrieved documents**, **omit** it instead of making assumptions.
"""

        self._llm = Ollama(model="llama3.2", request_timeout=60.0, system_prompt=self.system_prompt)
        Settings.llm = self._llm
        self.retriever = VectorIndexAutoRetriever(index=self.index, llm=self._llm, prompt_template_str=self.system_prompt, vector_store_info=self.vector_store_info, similarity_top_k=20)
        self.query_engine = RetrieverQueryEngine(retriever=self.retriever)

    
    def store_embeddings(self, df):
        for _, row in df.iterrows():
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, row["content_chunk"]))  # Unique ID

            # Check if ID already exists
            existing_docs = self.collection.get(ids=[doc_id])
            
            if not existing_docs["ids"]:  # If the ID doesn't exist, insert it
                self.collection.add(
                    ids=[doc_id],
                    embeddings=[row["embedding"]],
                    metadatas=[{
                        "company_name": row["company_name"],
                        "form_type": row["form_type"],
                        "date": row["date"],
                        "page_number": row["page_number"],
                    }],
                    documents=[row["content_chunk"]],
                )
    

    def query(self, query_text: str):
        query_bundle = QueryBundle(query_text)
        response = self.query_engine.query(query_bundle)
        return response
    

    def retrieved_query(self, query_text: str):
        query_bundle = QueryBundle(query_text)
        response = self.query_engine.query(query_bundle)
        
        for node in response.source_nodes:
            print(node.metadata, node.text)
    

    def check_chroma_db(self):
        if self.collection.count() == 0:
            print("⚠️ WARNING: No embeddings found in ChromaDB. Ensure data is stored first.")
        else:
            print(f"✅ ChromaDB contains {self.collection.count()} documents.")