import requests
import pandas as pd
import os
from xhtml2pdf import pisa


headers = {
    'User-Agent': "qhdxbqm123@gmail.com"
}

class sec_edgar_api:
    def __init__(self):
        self.company_data = self.load_company_tickers()
        self.filing_metadata = pd.DataFrame()
    

    def load_company_tickers(self):
        try:
            #get all companyTickers
            companyTickers = requests.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=headers
            )
            companyTickers.raise_for_status()

            #dictionary to dataframe
            company_data = pd.DataFrame.from_dict(companyTickers.json(), orient='index')

            #add leading zeros to CIK
            company_data['cik_str'] = company_data['cik_str'].astype(str).str.zfill(10)

            return company_data
        
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch company tickers: {e}")
            return pd.DataFrame()


    def findCIK(self, ticker: str) -> int:
        if self.company_data.empty:
            print('company_data is empty')
            return 0
        
        try:
            # Find cik in the dataframe
            result = self.company_data[self.company_data['ticker'] == ticker.upper()]['cik_str']

            if not result.empty:
                return result.iloc[0]
            else:
                return f"Ticker '{ticker}' not found in the data."

        except KeyError:
            return "The 'ticker' or 'cik_str' column is missing in the DataFrame."
        
    
    def retrieve_company_filing_metadata(self, cik):
        try:
            filing_metadata = requests.get(
                f'https://data.sec.gov/submissions/CIK{cik}.json',
                headers=headers
            )
            # Create dataframe from a dictionary
            df = pd.DataFrame.from_dict(filing_metadata.json()['filings']['recent'])

            # Filter recent 5 "10-K", "10-Q", "8-K" forms
            df = df[df['form'].isin(["10-K", "10-Q", "8-K"])]
            df = df.sort_values(by=['form', 'filingDate'], ascending=[True, False])
            df = df.groupby('form').head(5)
            df = df.reset_index(drop=True)

            self.filing_metadata = df
        
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch filings metadata for CIK {cik}: {e}")


    def get_accession_number_by_index(self, index: int) -> str:
        # Retrieve accession_number from the dataframe
        if not self.filing_metadata.empty:
            try:
                return self.filing_metadata.iloc[index]['accessionNumber'].replace('-', '')
            except IndexError:
                raise IndexError("Index out of range. Please provide a valid index.")
        else:
            raise ValueError("filing_metadata is empty. Cannot retrieve accession number.")
    

    def get_primary_document_by_index(self, index: int) -> str:
        # Retrieve primary_document from the dataframe
        if not self.filing_metadata.empty:
            try:
                return self.filing_metadata.iloc[index]['primaryDocument']
            except IndexError:
                raise IndexError("Index out of range. Please provide a valid index.")
        else:
            raise ValueError("filing_metadata is empty. Cannot retrieve accession number.")
    

    def download_document(self, cik:str, accession_number:str, primary_document:str):
        if self.filing_metadata.empty:
            print('company_data is empty')
            return 0

        try:
            sec_document = requests.get(
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_number}/{primary_document}",
                headers=headers
            )
            sec_document.raise_for_status()

            # Retrieve ticker_id and form type from the dataframe
            ticker_id = self.company_data[self.company_data['cik_str'] == cik]['ticker'].iloc[0]
            form_type = self.filing_metadata[self.filing_metadata['primaryDocument'] == primary_document]['form'].iloc[0]

            # Set filename and path
            pdf_filename = f"{ticker_id}_{cik}_{form_type}.pdf"
            file_path = os.path.join("./reports/sources/", pdf_filename)

            # Write the file in bytes
            with open(file_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(sec_document.text, dest=pdf_file)

            if pisa_status.err:
                print("❌ Error occurred while converting HTML to PDF")
            else:
                print(f"✅ Document saved as {pdf_filename}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching the document: {e}")
        except ValueError as e:
            print(e)
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")