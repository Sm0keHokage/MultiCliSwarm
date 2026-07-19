import logging

logger = logging.getLogger("multicliswarm.web_search")

def search_web_docs(query: str, max_results: int = 3) -> str:
    """
    Performs a web search using duckduckgo-search to pull in latest API docs/context.
    """
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        results = ddgs.text(query, max_results=max_results)
        
        if not results:
            return ""
            
        context_blocks = []
        for r in results:
            title = r.get('title', 'Unknown')
            body = r.get('body', '')
            link = r.get('href', '')
            context_blocks.append(f"[{title}]({link}):\n{body}")
            
        return "Web Search Context:\n" + "\n\n".join(context_blocks)
    except Exception as e:
        logger.warning(f"Web search failed (is duckduckgo-search installed?): {e}")
        return ""
