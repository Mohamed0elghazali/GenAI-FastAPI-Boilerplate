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

def list_dir(dir_name: str = "") -> list[str]:
    """
    List files and folders inside data/tmp/<dir_name>

    Args:
        dir_name: Subdirectory inside data/tmp

    Returns:
        List of file and folder names
    """

    path = Path("data/tmp") / dir_name

    # Create directory if it does not exist
    # path.mkdir(parents=True, exist_ok=True)

    return [item.name for item in path.iterdir()]

@tool
@timeit
def write_file_tool(content: str, file_name: str) -> dict:
    """
    Write a file to disk with the specified content and filename.
    """

    try:
        write_file(content, file_name)

        return {"status": True, "message": None, "result": f"File `{file_name}` written successfully."}

    except Exception as e:
        logger.warning(f"error at write file: {e}")

        return {"status": False, "message": str(e), "result": None}


@tool
@timeit
def ls_dir_tool(dir_name: str = "") -> dict:
    """
    List files and folders inside a directory.
    """

    try:
        files = list_dir(dir_name)

        return {"status": True, "message": None, "result": files}

    except Exception as e:
        logger.warning(f"error at listing directory: {e}")

        return {"status": False, "message": str(e), "result": None}


if __name__ == "__main__":
    # Example
    # create_file("Hello World", "test.txt")
    write_file_tool.invoke({"content": "Hello World", "file_name": "test.txt"})
