import os
from typing import TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from embeddings import embed_query
from log import log
from vector_store import query_vectors

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Answer using ONLY the notes. If they do not contain the answer, "
            "say you do not know. Do not invent facts. Keep the answer short.",
        ),
        (
            "human",
            "Notes:\n{context}\n\nQuestion: {question}",
        ),
    ]
)


class RagState(TypedDict):
    query: str
    k: int
    docs: list
    answer: str
    sources: list


def _llm() -> ChatOpenAI:
    key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is missing")
    base = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip().rstrip("/")
    return ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL") or "deepseek-chat",
        api_key=key,
        base_url=base,
        temperature=0,
        timeout=45,
        max_retries=1,
    )


def retrieve(state: RagState) -> dict:
    vector = embed_query(state["query"])
    docs = query_vectors(vector, k=state.get("k") or 4)
    log("rag_retrieve", query=state["query"], hits=len(docs))
    return {"docs": docs}


def generate(state: RagState) -> dict:
    docs = state.get("docs") or []
    sources = [{"text": doc["text"], "source": doc.get("source")} for doc in docs]
    if not docs:
        return {
            "answer": "I do not have that in the ingested notes.",
            "sources": [],
        }

    context = "\n\n".join(
        f"[{i}] source={doc.get('source') or 'unknown'}\n{doc['text']}"
        for i, doc in enumerate(docs, start=1)
    )
    chain = PROMPT | _llm() | StrOutputParser()
    answer = chain.invoke({"context": context, "question": state["query"]})
    log("rag_generate", sources=len(sources))
    return {"answer": answer.strip(), "sources": sources}


def build_graph():
    graph = StateGraph(RagState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


_app = None


def rag_query(query: str, k: int = 4) -> dict:
    global _app
    if _app is None:
        _app = build_graph()
    result = _app.invoke({"query": query, "k": k, "docs": [], "answer": "", "sources": []})
    return {"answer": result["answer"], "sources": result["sources"]}
