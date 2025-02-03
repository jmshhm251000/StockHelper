import asyncio
import pandas as pd
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

        for index, filing_html in enumerate(self.filings):
            if not filing_html.strip():
                print(f"⚠️ Warning: Filing {index + 1} is empty. Skipping processing.")
                continue
            else:
                print(f"Filing {index + 1} is NOT empty. Proceeding...")
            accession_number, primary_document, form_type, report_date = self.sec_api.get_metadata(index)

            chunk_df, text_df, table_df = await preprocessor.clean_data(
                filing_html, self.company_ticker, form_type, report_date
            )

            all_chunk_dfs.append(chunk_df)
            all_text_dfs.append(text_df)
            all_table_dfs.append(table_df)

            print(f"✅ Filing {index + 1} is cleaned")

        # Combine all processed data into single DataFrames
        self.chunk_df = pd.concat(all_chunk_dfs, ignore_index=True)
        self.text_df = pd.concat(all_text_dfs, ignore_index=True)
        self.table_df = pd.concat(all_table_dfs, ignore_index=True)


    def save_to_file(self):
        self.chunk_df.to_json("chunk_text.json", orient="records", indent=4, force_ascii=False)
        print(self.chunk_df.describe())


    def setup_embeddings(self):
        """Set up embedding model."""
        embedding.Settings.embed_model = embedding.BAAIEmbeddings()
        self.embed_model = embedding.Settings.embed_model


    def encode_texts(self):
        # TO DO - encode texts
        pass


async def main(company_ticker):
    """Main function to manage the SEC data retrieval and processing pipeline."""
    processor = SECDataProcessor(company_ticker)
    
    await processor.fetch_filings()
    await processor.process_filings()

    processor.setup_embeddings()