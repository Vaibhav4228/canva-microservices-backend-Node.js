from langchain_text_splitters import RecursiveCharacterTextSplitter

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=80,
    add_start_index=True,
)


def split_text(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in _splitter.split_text(text) if chunk.strip()]
    return chunks
