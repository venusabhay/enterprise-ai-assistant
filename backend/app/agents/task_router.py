from langchain_core.prompts import PromptTemplate


router_prompt = PromptTemplate.from_template(
"""
You are a routing agent. Classify the user request into one of:
- RAG
- SUMMARIZE
- WORKFLOW
Return only the label.
Query: {query}
"""
)