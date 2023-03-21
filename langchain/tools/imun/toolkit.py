"""Tool for the Image Understanding API."""

from typing import List

from langchain.tools.base import BaseTool, BaseToolkit
from langchain.tools.imun.tool import ImunRun
from langchain.utilities.imun import ImunAPIWrapper


class ImunToolkit(BaseToolkit):
    """Tool that adds the capability to query the Image Understanding API."""

    imun_subscription_key: str
    imun_url: str

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        wrapper = ImunAPIWrapper(
            imun_subscription_key=self.imun_subscription_key,
            imun_url=self.imun_url,
        )
        return [
            ImunRun(
                api_wrapper=wrapper,
            )
        ]
