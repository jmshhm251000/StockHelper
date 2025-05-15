import asyncio
from src.sec_loader import SECDataProcessor
from src.database import vectordb


async def main(company_ticker):
    processor = SECDataProcessor(company_ticker)
    processor.setup_embeddings()
    db = vectordb(processor.embed_model)

    debug = False
    
    if debug:
        await processor.fetch_filings()
        await processor.process_filings()

        processor.encode_texts()

        print("Storing Embeddings to db...")
        db.store_embeddings(processor.chunk_df)
        print("Storing done")

    processor.table_df.to_csv('tables.csv')
    
    db.check_chroma_db()

    print("Generating Response...")
    prompt = "in thorough details. tell me the prospect of the company"
    #print(db.retrieved_query(prompt))
    print(db.query(prompt))

    # TODO - Need to remove chunks with low token


if __name__ == "__main__":
    company_ticker = "mstr"
    #asyncio.run(main(company_ticker))
    processor = SECDataProcessor(company_ticker)
    processor.setup_embeddings()
    db = vectordb(processor.embed_model)
    processor.table_df.to_csv('tables.csv')
    
    db.check_chroma_db()

    print("Generating Response...")
    prompt = "in thorough details. tell me the prospect of the company"
    #print(db.retrieved_query(prompt))
    print(db.query(prompt))