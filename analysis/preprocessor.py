from bs4 import BeautifulSoup
from requests import Response
import pandas as pd
import re
from llama_index.core.node_parser import TokenTextSplitter
import asyncio


async def clean_text(text: str) -> str:
    return text.replace("\n", " ").strip()


async def clean_data(html: str, company_name: str, form_type: str, report_date: str, chunk_size=256, chunk_overlap=20) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    structured_tables = [
        {
            "company_name": company_name,
            "form_type": form_type,
            "date": report_date,
            "table_number": i,
            "row": x,
            "column": y,
            "data": str(data.get_text().strip())
        }
        for i, table in enumerate(tables)
        for x, tr in enumerate(table.find_all("tr"))
        for y, data in enumerate(tr.find_all("td"))
    ]

    for table in tables:
        for tr in table.find_all("tr"):
            for data in tr.find_all("td"):
                data.decompose()

    pages_and_texts = []
    page_number = 0
    current_page = []
    text_cleaning_tasks = []
    
    for element in soup.body.children:
        if element.name == "hr":
            if text_cleaning_tasks:  # Ensure we have tasks to process
                texts_list = await asyncio.gather(*text_cleaning_tasks)  # Await tasks
                texts = " ".join(texts_list).strip()
                if texts:  # Ensure texts are not empty
                    pages_and_texts.append({
                        "company_name": company_name,
                        "form_type": form_type,
                        "date": report_date,
                        "page_number": page_number,
                        "page_char_count": len(texts),
                        "page_word_count": len(texts.split()),
                        "page_sentence_count_raw": len(texts.split(". ")),
                        "page_token_count": len(texts) / 4,
                        "content": re.sub(r"\s*\d+\s*$", "", texts.strip())
                    })
                    page_number += 1

            # Reset lists after an HR tag
            current_page = []
            text_cleaning_tasks = []

        else:
            text_content = element.get_text(" ", strip=True)
            if text_content.strip():  # Only process non-empty text
                text_cleaning_tasks.append(asyncio.create_task(clean_text(text_content)))  # ✅ Ensure async execution
                current_page.append(text_content)  # Ensure text is tracked

    # Add the last page if there's remaining content
    if current_page:
        texts = " ".join(await asyncio.gather(*text_cleaning_tasks)).strip()
        pages_and_texts.append({
            "company_name": company_name,
            "form_type": form_type,
            "date": report_date,
            "page_number": page_number,
            "page_char_count": len(texts),
            "page_word_count": len(texts.split()),
            "page_sentence_count_raw": len(texts.split(". ")),
            "page_token_count": len(texts) / 4,
            "content": re.sub(r"\s*\d+\s*$", "", texts.strip())
        })

    text_df = pd.DataFrame(pages_and_texts)
    table_df = pd.DataFrame(structured_tables)

    text_df = text_df.iloc[1:].reset_index(drop=True)
    text_df["content"] = text_df["content"].replace("", None)
    text_df.dropna(subset=["content"], inplace=True)
    text_df.reset_index(drop=True, inplace=True)

    table_df.replace("", None, inplace=True)
    table_df.dropna(how="any", inplace=True)
    table_df.reset_index(drop=True, inplace=True)

    splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    split_content = []
    chunk_processing_tasks = []

    for _, row in text_df.iterrows():
        chunk_processing_tasks.append(asyncio.to_thread(splitter.split_text, row["content"]))

    chunk_results = await asyncio.gather(*chunk_processing_tasks)

    for row, chunks in zip(text_df.iterrows(), chunk_results):
        for chunk in chunks:
            split_content.append({
                "company_name": company_name,
                "form_type": form_type,
                "date": report_date,
                "page_number": row[1]["page_number"],
                "chunk_char_count": len(chunk),
                "chunk_word_count": len(chunk.split()),
                "chunk_sentence_count_raw": len(chunk.split(". ")),
                "chunk_token_count": len(chunk) / 4,
                "content_chunk": chunk
            })

    chunk_text_df = pd.DataFrame(split_content)

    return chunk_text_df, text_df, table_df