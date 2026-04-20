from __future__ import annotations

import time

from .incidents import STATE
from .pii import summarize_text
from .tracing import langfuse_context, observe

CORPUS = {
    "refund": ["Refunds are available within 7 days with proof of purchase."],
    "monitoring": ["Metrics detect incidents, traces localize them, logs explain root cause."],
    "policy": ["Do not expose PII in logs. Use sanitized summaries only."],
}


@observe(capture_input=False, capture_output=False)
def retrieve(message: str) -> list[str]:
    langfuse_context.update_current_observation(
        name="retrieve_docs",
        input={"query_preview": summarize_text(message)}
    )
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)
    lowered = message.lower()
    for key, docs in CORPUS.items():
        if key in lowered:
            langfuse_context.update_current_observation(output={"doc_count": len(docs)})
            return docs
    fallback_docs = ["No domain document matched. Use general fallback answer."]
    langfuse_context.update_current_observation(output={"doc_count": len(fallback_docs)})
    return fallback_docs
