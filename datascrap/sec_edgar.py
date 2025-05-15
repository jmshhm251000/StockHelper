import requests
import pandas as pd
import os
import time
import asyncio
import json
from xhtml2pdf import pisa
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv


load_dotenv()
headers_str = os.getenv("HEADERS")  # This is still a string
headers = json.loads(headers_str)


class sec_edgar_api:
    def __init__(self, company_ticker):
        self.company_data = self.load_company_tickers()
        self.filing_metadata = pd.DataFrame()
        self.filings = []
        self.cik = self.findCIK(company_ticker)
    

    def load_company_tickers(self):
        """Load CIK json from SEC"""
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
        """Find CIK that matches the ticker"""
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
        
    
    def retrieve_company_filing_metadata(self):
        """Retrieve company filing from SEC EDGAR"""
        try:
            filing_metadata = requests.get(
                f'https://data.sec.gov/submissions/CIK{self.cik}.json',
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
            print(f"Failed to fetch filings metadata for CIK {self.cik}: {e}")


    def get_accession_number_by_index(self, index: int) -> str:
        """Retrieve accession_number from the dataframe"""
        if not self.filing_metadata.empty:
            try:
                return self.filing_metadata.iloc[index]['accessionNumber'].replace('-', '')
            except IndexError:
                raise IndexError("Index out of range. Please provide a valid index.")
        else:
            raise ValueError("filing_metadata is empty. Cannot retrieve accession number.")
    

    def get_primary_document_by_index(self, index: int) -> str:
        """Retrieve primary_document from the dataframe"""
        if not self.filing_metadata.empty:
            try:
                return self.filing_metadata.iloc[index]['primaryDocument']
            except IndexError:
                raise IndexError("Index out of range. Please provide a valid index.")
        else:
            raise ValueError("filing_metadata is empty. Cannot retrieve accession number.")
        
    
    def get_form_type(self, index: int) -> str:
        """Retrieve form type from the dataframe"""
        if not self.filing_metadata.empty:
            try:
                return self.filing_metadata.iloc[index]['form']
            except IndexError:
                raise IndexError("Index out of range. Please provide a valid index.")
        else:
            raise ValueError("filing_metadata is empty. Cannot retrieve accession number.")
        
    
    def get_report_date(self, index: int) -> str:
        """Retrieve data of the report"""
        if not self.filing_metadata.empty:
            try:
                return self.filing_metadata.iloc[index]['reportDate']
            except IndexError:
                raise IndexError("Index out of range. Please provide a valid index.")
        else:
            raise ValueError("filing_metadata is empty. Cannot retrieve accession number.")
    

    def get_metadata(self, index: int) -> str:
        """
        Returns:
            - accession_number (str)
            - primary_document (str)
            - form_type (str)
            - report_date (str)
        """
        return self.get_accession_number_by_index(index), self.get_primary_document_by_index(index), self.get_form_type(index), self.get_report_date(index)


    def get_filing_data(self, index) -> str:
        if self.filing_metadata.empty:
            print('company_data is empty')
            return 0
        
        accession_number, primary_document, _, _ = self.get_metadata(index)

        url = f"https://www.sec.gov/Archives/edgar/data/{int(self.cik)}/{accession_number}/{primary_document}"
        print(url)

        USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")  
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={USER_AGENT}")

        driver = webdriver.Chrome(options=options)
        driver.get(url)

        sec_document = driver.page_source

        driver.quit()

        return sec_document


    async def _get_filing_data(self) -> list[str]:
        """
        Asynchronously fetches HTML filing data for all filings in self.filing_metadata.
        Returns a list of HTML content.
        """
        if self.filing_metadata.empty:
            print("Filing metadata is empty")
            return []

        USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={USER_AGENT}")

        async def fetch_filing(index: int) -> str:
            """
            Fetches the SEC filing HTML document asynchronously for a given index.
            """
            accession_number, primary_document, _, _ = self.get_metadata(index)

            url = f"https://www.sec.gov/Archives/edgar/data/{int(self.cik)}/{accession_number}/{primary_document}"
            print(f"Fetching: {url}")

            # Function to run Selenium in a separate thread
            def fetch_html():
                driver = webdriver.Chrome(options=options)
                driver.get(url)
                time.sleep(5)
                page_source = driver.page_source
                driver.quit()
                return page_source

            return await asyncio.to_thread(fetch_html)  # Runs Selenium in a separate thread

        # Create a list of tasks for each filing
        tasks = [fetch_filing(index) for index in range(len(self.filing_metadata))]

        # Run all requests concurrently
        results = await asyncio.gather(*tasks)

        return results


    async def get_filings(self):
        self.filings =  await self._get_filing_data()

        missing_indices = [i for i, filing in enumerate(self.filings) if not filing]

        if missing_indices:
            print(f"⚠️ Warning: {len(missing_indices)} filings failed to retrieve.")
            await self._retry_missing_filings(missing_indices)


    async def _retry_missing_filings(self, missing_indices):
        """Reattempt downloading the missing filings asynchronously."""
        print(f"🔄 Retrying {len(missing_indices)} missing filings...")

        # Retry only the missing filings
        tasks = [self._fetch_filing(i) for i in missing_indices]
        results = await asyncio.gather(*tasks)

        # Update `self.filings` with the retried results
        for i, result in zip(missing_indices, results):
            self.filings[i] = result

        print(f"✅ Finished retrying. Missing filings recovered: {sum(bool(r) for r in results)}")


    def download_document(self, cik:str, accession_number:str, primary_document:str):
        if self.filing_metadata.empty:
            print('company_data is empty')
            return 0

        try:
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_number}/{primary_document}"
            print(url)

            USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")  
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"user-agent={USER_AGENT}")

            driver = webdriver.Chrome(options=options)
            driver.get(url)

            sec_document = driver.page_source

            driver.quit()

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
