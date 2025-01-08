from datascrap import sec_edgar

if __name__ == "__main__":
    sec = sec_edgar.sec_edgar_api()
    cik = sec.findCIK('aapl')


    print(cik)


    sec.retrieve_company_filing_metadata(cik)
    accession_number = sec.get_accession_number_by_index(0)
    primary_document = sec.get_primary_document_by_index(0)


    sec.download_document(cik, accession_number, primary_document)