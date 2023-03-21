"""Tool for the Image Understanding search API."""

from langchain.tools.base import BaseTool
from langchain.utilities.imun import ImunAPIWrapper


class ImunRun(BaseTool):
    """Tool that adds the capability to query the Image Understanding API."""

    name = "Image Understanding"
    description = (
        "A wrapper around Image Understanding. "
        "Useful for when you need to understand what is inside an image (objects, texts, people)."
        "Input should be an image url, or path to an image file (e.g. .jpg, .png)."
    )
    api_wrapper: ImunAPIWrapper

    def _run(self, query: str) -> str:
        """Use the tool."""
        return self.api_wrapper.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("Image Understanding does not support async")
