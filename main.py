from datascrap import sec_edgar
from analysis import preprocessor
import pandas as pd


if __name__ == "__main__":
    sec = sec_edgar.sec_edgar_api()
    cik = sec.findCIK('mstr')

    print(cik)

    sec.retrieve_company_filing_metadata(cik)
    print(sec.filing_metadata.head(10))
    accession_number = sec.get_accession_number_by_index(5)
    primary_document = sec.get_primary_document_by_index(5)

    #sec.download_document(cik, accession_number, primary_document)
    html = sec.get_filing_data(cik, accession_number, primary_document)

    chunk_df, text_df, table_df = preprocessor.clean_data(html)

    print(chunk_df.head(30))
    print(chunk_df.describe())
    print(chunk_df.info())