import os

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from log import log
from models import TemplateLayout, TemplateObject

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You design a Canva-like layout as JSON. Canvas is 825x465. "
            "Always include at least two textboxes: a big title and a smaller subtitle. "
            "Use the prompt's colors (e.g. pink + gold). "
            "Optional similar notes may mention sizes or style — use them if they help. "
            "Do not leave objects empty.\n{format_instructions}",
        ),
        (
            "human",
            "Prompt: {prompt}\n\nSimilar notes:\n{notes}",
        ),
    ]
)


def _llm() -> ChatOpenAI:
    key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is missing")
    base = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip().rstrip("/")
    return ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL") or "deepseek-chat",
        api_key=key,
        base_url=base,
        temperature=0.3,
        timeout=45,
        max_retries=1,
    )


def _similar_notes(prompt: str) -> tuple[str, int]:
    try:
        from embeddings import embed_query
        from vector_store import query_vectors

        docs = query_vectors(embed_query(prompt), k=2)
        if not docs:
            return "(none)", 0
        text = "\n\n".join(
            f"[{i}] {doc.get('source') or 'note'}: {doc['text']}"
            for i, doc in enumerate(docs, start=1)
        )
        return text, len(docs)
    except Exception as e:
        log("template_rag_skip", error=str(e))
        return "(none)", 0


def _as_layout(layout) -> TemplateLayout:
    if isinstance(layout, TemplateLayout):
        return layout
    return TemplateLayout.model_validate(layout)


def _ensure_objects(layout: TemplateLayout) -> TemplateLayout:
    if layout.objects:
        return layout
    layout.objects = [
        TemplateObject(
            type="textbox",
            text=layout.title,
            left=60,
            top=90,
            fontSize=48,
            fill="#be185d",
            fontWeight="bold",
        ),
        TemplateObject(
            type="textbox",
            text=layout.subtitle or "You're invited",
            left=60,
            top=170,
            fontSize=22,
            fill="#a16207",
        ),
    ]
    return layout


def template_from_prompt(prompt: str) -> dict:
    notes, notes_used = _similar_notes(prompt)
    llm = _llm()
    try:
        structured = llm.with_structured_output(TemplateLayout)
        layout = structured.invoke(
            "Design a Canva-like layout. Canvas 825x465. "
            "Always include at least two textboxes (title + subtitle) using the prompt colors. "
            f"Prompt: {prompt}\nSimilar notes:\n{notes}"
        )
    except Exception as e:
        log("template_structured_fallback", error=str(e))
        parser = PydanticOutputParser(pydantic_object=TemplateLayout)
        chain = PROMPT | llm | parser
        layout = chain.invoke(
            {
                "prompt": prompt,
                "notes": notes,
                "format_instructions": parser.get_format_instructions(),
            }
        )
    layout = _ensure_objects(_as_layout(layout))
    log("template_ok", title=layout.title, objects=len(layout.objects), notes=notes_used)
    return {"layout": layout, "notesUsed": notes_used}
