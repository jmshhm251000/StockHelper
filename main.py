import asyncio
from src.sec_loader import SECDataProcessor
from src.database import vectordb


async def main(company_ticker):
    processor = SECDataProcessor(company_ticker)
    
    await processor.fetch_filings()
    await processor.process_filings()

    processor.setup_embeddings()
    processor.encode_texts()

    db = vectordb(processor.embed_model)

    print("Storing Embeddings to db...")
    db.store_embeddings(processor.chunk_df)
    print("Storing done")

    print("Generating Response...")
    prompt = "in thorough details. summarise the content of the recent 10q report and give me a paragraph from the actual report"
    print(db.retrieved_query(prompt))
    #print(db.query(prompt))


if __name__ == "__main__":
    company_ticker = "mstr"
    asyncio.run(main(company_ticker))