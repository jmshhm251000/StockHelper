from bs4 import BeautifulSoup
from requests import Response
import pandas as pd
import re
from llama_index.core.node_parser import TokenTextSplitter


def clean_text(text: str) -> str:
    cleaned_text = text.replace("\n", " ").strip()

    return cleaned_text


def clean_data(html: Response, chunk_size=256, chunk_overlap=20) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    structured_tables = []

    for i, table in enumerate(tables):
        for x, tr in enumerate(table.find_all("tr")):
            for y, data in enumerate(tr.find_all("td")):
                structured_tables.append({
                    "table_number": i,
                    "row": x,
                    "column": y,
                    "data": str(data.get_text().strip())
                })
                data.decompose()

    pages_and_texts = []
    page_number = 0
    current_page = []

    for element in soup.body.children:
        if element.name == "hr":
            if current_page:
                texts = " ".join(current_page).strip()
                pages_and_texts.append({
                    "page_number": page_number,
                    "page_char_count": len(texts),
                    "page_word_count": len(texts.split()),
                    "page_sentence_count_raw": len(texts.split(". ")),
                    "page_token_count": len(texts) / 4,
                    "content": re.sub(r"\s*\d+\s*$", "", texts.strip())
                })
                page_number += 1
                current_page = []
        else:
            current_page.append(clean_text(element.get_text(" ", strip=True)))

    # Add the last page (if any content remains)
    if current_page:
        texts = " ".join(current_page).strip()
        pages_and_texts.append({
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

    text_df['content'] = text_df['content'].replace("", None)
    text_df.dropna(subset=['content'], inplace=True)
    text_df.reset_index(drop=True, inplace=True)

    table_df.replace("", None, inplace=True)
    table_df.dropna(how='any', inplace=True)
    table_df.reset_index(drop=True, inplace=True)

    splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    split_content = []
    for _, row in text_df.iterrows():
        chunks = splitter.split_text(row["content"])
        for chunk in chunks:
            split_content.append({
                "page_number": row["page_number"],
                "chunk_char_count": len(chunk),
                "chunk_word_count": len(chunk.split()),
                "chunk_sentence_count_raw": len(chunk.split(". ")),
                "chunk_token_count": len(chunk) / 4,
                "content_chunk": chunk
            })

    chunk_text_df = pd.DataFrame(split_content)

    return chunk_text_df, text_df, table_df