import logging
from pathlib import Path
from langchain.tools import tool

from core.utils import timeit

logger = logging.getLogger(__name__)

def write_file(text: str, file_name: str, encoding: str = "utf-8") -> None:
    """
    Create a file inside data/tmp and write text into it.

    Args:
        text: Content to write into the file
        file_name: Name of the file
        encoding: File encoding (default: utf-8)
    """

    path = Path("data/tmp") / file_name

    # Create directories if they do not exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write text to file
    path.write_text(text, encoding=encoding)

@tool
@timeit
def write_file_tool(content: str, file_name: str) -> dict:
    """Write a file to disk with the specified content and filename."""
    try:
        create_file(content, file_name)
        return {"status": True, "message": None, "result": f"File `{file_name}` written successfully."}
    except Exception as e:
        logger.warning(f"error at write file: {e}")
        return {"status": False, "message": str(e), "result": None}


if __name__ == "__main__":
    # Example
    # create_file("Hello World", "test.txt")
    write_file_tool.invoke({"content": "Hello World", "file_name": "test.txt"})
