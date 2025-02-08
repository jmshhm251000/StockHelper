import os
import pandas as pd
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio
from datascrap.sec_edgar import sec_edgar_api
from analysis import preprocessor, embedding

class SECDataProcessor:
    def __init__(self, company_ticker):
        self.company_ticker = company_ticker
        self.sec_api = sec_edgar_api(company_ticker)
        self.filings = []
        self.chunk_df = pd.DataFrame()
        self.text_df = pd.DataFrame()
        self.table_df = pd.DataFrame()


    async def fetch_filings(self):
        """Retrieve company filings asynchronously and store them."""
        self.sec_api.retrieve_company_filing_metadata()
        await self.sec_api.get_filings()
        self.filings = self.sec_api.filings


    async def process_filings(self):
        """Processes all filings using preprocessor."""
        all_chunk_dfs, all_text_dfs, all_table_dfs = [], [], []

        for index, filing_html in enumerate(tqdm(self.filings, desc="Processing Filings")):
            if not filing_html.strip():
                print(f"⚠️ Warning: Filing {index + 1} is empty. Skipping processing.")
                continue

            accession_number, primary_document, form_type, report_date = self.sec_api.get_metadata(index)

            chunk_df, text_df, table_df = await preprocessor.clean_data(
                filing_html, self.company_ticker, form_type, report_date
            )

            all_chunk_dfs.append(chunk_df)
            all_text_dfs.append(text_df)
            all_table_dfs.append(table_df)

        # Combine all processed data into single DataFrames
        self.chunk_df = pd.concat(all_chunk_dfs, ignore_index=True)
        self.text_df = pd.concat(all_text_dfs, ignore_index=True)
        self.table_df = pd.concat(all_table_dfs, ignore_index=True)


    def setup_embeddings(self):
        self.embed_model = embedding.BAAIEmbeddings()
        embedding.Settings.embed_model = self.embed_model


    def encode_texts(self):
        temp_dict = [item["content_chunk"] for item in self.chunk_df.to_dict("records")]
        self.embed_texts = pd.DataFrame(self.embed_model._get_text_embeddings(temp_dict))
        self.chunk_df["embedding"] = self.embed_texts.apply(lambda row: row.tolist(), axis=1)
        print(self.chunk_df.head())