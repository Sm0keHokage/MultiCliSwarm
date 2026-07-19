import logging
from typing import List
from pydantic import BaseModel, Field

logger = logging.getLogger("multicliswarm.patching")

class ReplaceBlock(BaseModel):
    search: str = Field(description="The exact literal string to search for in the file. Must match indentation and newlines exactly.")
    replace: str = Field(description="The new literal string to replace the searched block with.")

class FilePatch(BaseModel):
    filepath: str = Field(description="The relative path to the file to be patched.")
    blocks: List[ReplaceBlock] = Field(description="List of search/replace blocks to apply to this file.")

def apply_patch(original_content: str, blocks: List[ReplaceBlock]) -> str:
    """
    Applies a list of search/replace blocks to a string.
    Raises ValueError if a search block is not found or is ambiguous.
    """
    content = original_content
    for i, block in enumerate(blocks):
        search_str = block.search
        replace_str = block.replace
        
        # Handle exact match first
        count = content.count(search_str)
        if count == 1:
            content = content.replace(search_str, replace_str)
            continue
            
        # Try stripping leading/trailing whitespace to be a bit forgiving
        search_strip = search_str.strip()
        replace_strip = replace_str.strip()
        
        # Count again using stripped versions but only if search is not empty
        if not search_strip:
            raise ValueError(f"Patch block {i} search string is empty or only whitespace.")
            
        stripped_count = content.count(search_strip)
        if stripped_count == 1:
            content = content.replace(search_strip, replace_strip)
            logger.warning(f"Applied patch block {i} using stripped matching.")
            continue
            
        if count == 0 and stripped_count == 0:
            raise ValueError(f"Patch block {i} search string not found in the code.")
        else:
            raise ValueError(f"Patch block {i} search string is ambiguous (found {count} times). Context needs to be larger.")
            
    return content
