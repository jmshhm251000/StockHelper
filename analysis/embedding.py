from typing import Any, List
from FlagEmbedding import FlagModel
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core import Settings


class BAAIEmbeddings(BaseEmbedding):
    def __init__(
        self,
        instructor_model_name: str = "BAAI/bge-base-en-v1.5",
        instruction: str = "Represent this SEC filing for investment analysis, risk assessment, and financial insights:",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._model = FlagModel('BAAI/bge-base-en',
                                query_instruction_for_retrieval= instruction,
                                query_instruction_format='{}{}',
        )
        self._instruction = instruction

    def _get_query_embedding(self, query: str) -> List[float]:
        embeddings = self._model.encode([[self._instruction, query]])
        return embeddings[0]

    def _get_text_embedding(self, text: str) -> List[float]:
        embeddings = self._model.encode([[self._instruction, text]])
        return embeddings[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._model.encode(
            [[self._instruction, text] for text in texts]
        )
        return embeddings

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
      return self._get_text_embedding(text)