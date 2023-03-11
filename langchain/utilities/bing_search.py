"""Util that calls Bing Search.

In order to set this up, follow instructions at:
https://levelup.gitconnected.com/api-tutorial-how-to-use-bing-web-search-api-in-python-4165d5592a7e
"""
from typing import Dict, List

import os
import requests
from pydantic import BaseModel, Extra, root_validator

from langchain.utils import get_from_dict_or_env, download_image


class BingSearchAPIWrapper(BaseModel):
    """Wrapper for Bing Search API.

    In order to set this up, follow instructions at:
    https://levelup.gitconnected.com/api-tutorial-how-to-use-bing-web-search-api-in-python-4165d5592a7e
    """

    bing_subscription_key: str
    bing_subscription_key_vis: str
    bing_search_url: str
    k: int = 10

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
    
    @staticmethod
    def _get_image(search_term):
        search_term = search_term.strip()
        url_idx = search_term.rfind(" ")
        img_url = search_term[url_idx + 1:].strip()
        if not img_url.startswith(("http://", "https://", "/")):
            return
        try:
            return download_image(img_url)
        except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema, FileNotFoundError):
            return

    def _bing_search_results(self, search_term: str, count: int) -> List[dict]:
        data = self._get_image(search_term)
        if data:
            # if an image is being serached
            headers = {"Ocp-Apim-Subscription-Key": self.bing_subscription_key_vis}
            params = {
                "modules": "similarimages",
                "count": count,
                "textDecorations": True,
                "textFormat": "HTML",
            }
            response = requests.post("https://api.cognitive.microsoft.com/bing/v7.0/images/visualsearch", data=data, headers=headers, params=params)
            response.raise_for_status()
            search_results = response.json()
            return search_results
        headers = {"Ocp-Apim-Subscription-Key": self.bing_subscription_key}
        params = {
            "q": search_term,
            "count": count,
            "textDecorations": True,
            "textFormat": "HTML",
        }
        response = requests.get(
            self.bing_search_url, headers=headers, params=params  # type: ignore
        )
        response.raise_for_status()
        search_results = response.json()
        return search_results["webPages"]["value"]

    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and endpoint exists in environment."""
        bing_subscription_key = get_from_dict_or_env(
            values, "bing_subscription_key", "BING_SUBSCRIPTION_KEY"
        )
        values["bing_subscription_key"] = values.get("BING_SUBSCRIPTION_KEY_VIS") or os.environ.get("BING_SUBSCRIPTION_KEY_VIS") or bing_subscription_key
        bing_subscription_key_vis = bing_subscription_key
        values["bing_subscription_key_vis"] = bing_subscription_key_vis

        bing_search_url = get_from_dict_or_env(
            values,
            "bing_search_url",
            "BING_SEARCH_URL",
            # default="https://api.bing.microsoft.com/v7.0/search",
        )

        values["bing_search_url"] = bing_search_url

        return values

    def run(self, query: str) -> str:
        """Run query through BingSearch and parse result."""
        snippets = []
        results = self._bing_search_results(query, count=self.k)
        return results
        if len(results) == 0:
            return "No good Bing Search Result was found"
        for result in results:
            snippet = result["snippet"]
            snippet = snippet.replace("<b>", "").replace("</b>", "")  # remove bold
            snippets.append(snippet)

        return "\n".join(snippets)

    def results(self, query: str, num_results: int) -> List[Dict]:
        """Run query through BingSearch and return metadata.

        Args:
            query: The query to search for.
            num_results: The number of results to return.

        Returns:
            A list of dictionaries with the following keys:
                snippet - The description of the result.
                title - The title of the result.
                link - The link to the result.
        """
        metadata_results = []
        results = self._bing_search_results(query, count=num_results)
        if len(results) == 0:
            return [{"Result": "No good Bing Search Result was found"}]
        for result in results:
            metadata_result = {
                "snippet": result["snippet"],
                "title": result["name"],
                "link": result["url"],
            }
            metadata_results.append(metadata_result)

        return metadata_results
