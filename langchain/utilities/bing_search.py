"""Util that calls Bing Search.

In order to set this up, follow instructions at:
https://levelup.gitconnected.com/api-tutorial-how-to-use-bing-web-search-api-in-python-4165d5592a7e
"""
from typing import Dict, List, Tuple

import io
import json
import os
import requests
from pydantic import BaseModel, Extra, root_validator

from langchain.utils import get_from_dict_or_env, download_image, im_downscale, get_url_path
from datetime import datetime
from dateutil import parser


class BingSearchAPIWrapper(BaseModel):
    """Wrapper for Bing Search API.

    In order to set this up, follow instructions at:
    https://levelup.gitconnected.com/api-tutorial-how-to-use-bing-web-search-api-in-python-4165d5592a7e
    """

    bing_subscription_key: str
    bing_search_url: str
    k: int = 10
    bing_subscription_key_vis: str
    bing_vis_search_url: str

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
    
    @staticmethod
    def _get_image(img_url):
        if not img_url:
            return
        try:
            data = download_image(img_url)
            if len(data) > 1024 * 1024:
                if not img_url.endswith((".jpg", ".jpeg")):
                    # first try just compression
                    data, _ = im_downscale(data, None)
                    if len(data) <= 1024 * 1024:
                        return data
                data, _ = im_downscale(data, 1500)
            return data
        except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema, FileNotFoundError):
            return

    @staticmethod
    def _get_visual_results(response: dict) -> Tuple[List[Dict], str]:
        # with open("/mnt/output/gr/gg.json", "w") as fp:
        #     print(json.dumps(response, indent=2), file=fp)

        other_tags = []
        related = ""
        news = ""
        search_term = ""
        tags = response.get("tags") or []
        for tag in tags:
            for action in tag.get("actions") or []:
                values = (action.get("data") or {}).get("value") or []
                action_type = action.get("actionType") or ""
                if action_type == "PagesIncluding":
                    for v in values:
                        datePublished = v.get("datePublished") or ""
                        name = v.get("name") or ""
                        if datePublished and name:
                            date = parser.parse(datePublished)
                            now = datetime.now()
                            delta = now.year - date.year
                            if delta < 1:
                                datePublished = f"Published this year in {datePublished} with title "
                            elif 2 >= delta > 1:
                                datePublished = f"Published last year in {datePublished} with title "
                            elif 5 >= delta > 2:
                                datePublished = f"Published few years ago in {datePublished} with title"
                            else:
                                datePublished = f"Published in {datePublished} with title"
                            news = datePublished + name
                            break
                if action_type == "RelatedSearches":
                    related = ",".join([v["text"] for v in values[:4]])
                if action_type == "BestRepresentativeQuery":
                    search_term = action.get("displayName") or ""
                    if not search_term:
                        service_url = (action.get("serviceUrl") or "")
                        idx = service_url.find("q=")
                        if idx >= 0:
                            search_term = service_url[idx+2]
                if action_type == "TextResults":
                    names = tag.get("displayName") or ""
                    other_tags += [p.strip() for p in names.split("|")]
        result = search_term
        if news:
            result += f"\n{news}"
        other_tags = [t for t in other_tags if t]
        if other_tags:
            other_tags = ",".join(set(other_tags))
            result += f"\nRelated tags in the image: {other_tags}"
        if related and not result:
            result += f"\Related search terms: {related}"
        result = {
            "snippet": result
        }
        return [result], search_term

    def _bing_search_results(self, search_term: str, count: int) -> List[dict]:
        visual_results = []
        img_url = ""
        if self.bing_vis_search_url:
            search_term = search_term.strip()
            _, img_url = get_url_path(search_term)
            data = self._get_image(img_url)
            if data:
                # if an image is being serached
                headers = {"Ocp-Apim-Subscription-Key": self.bing_subscription_key_vis}
                formData = {
                    "knowledgeRequest": {
                        "invokedSkills":[
                            "DocumentLevelSuggestions",
                        ],
                        "invokedSkillsRequestData":{
                            "enableEntityData" : "true"
                        },
                    }
                }
                file = {
                    'image' : ('MY-IMAGE', io.BytesIO(data)),
                    'knowledgeRequest': (None, json.dumps(formData))
                }
                response = requests.post(self.bing_vis_search_url, headers=headers, files=file)
                response.raise_for_status()
                visual_results, new_search_term = self._get_visual_results(response.json())
                if visual_results and not new_search_term:
                    return visual_results
                if new_search_term:
                    search_term = new_search_term

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
        if img_url:
            img_url += "\n"
        return img_url, visual_results + search_results["webPages"]["value"]

    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and endpoint exists in environment."""
        bing_subscription_key = get_from_dict_or_env(
            values, "bing_subscription_key", "BING_SUBSCRIPTION_KEY"
        )
        values["bing_subscription_key"] = bing_subscription_key

        # default="https://api.bing.microsoft.com/v7.0/images/visualsearch"
        bing_vis_search_url = values.get("bing_vis_search_url") or os.environ.get("BING_VIS_SEARCH_URL") or ""
        values["bing_vis_search_url"] = bing_vis_search_url

        bing_subscription_key_vis = values.get("bing_subscription_key_vis") or os.environ.get("BING_SUBSCRIPTION_KEY_VIS") or bing_subscription_key
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
        img_url, results = self._bing_search_results(query, count=self.k)
        for result in results:
            snippet = result["snippet"]
            snippet = snippet.replace("<b>", "").replace("</b>", "")  # remove bold
            snippets.append(snippet)

        snippets = "\n".join(snippets)
        if snippets:
            return img_url + "results from internet search:\n" + snippets
        return img_url + "No good Bing Search Result was found"

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
        img_url, results = self._bing_search_results(query, count=num_results)
        if len(results) == 0:
            return [{"Result": img_url + "No good Bing Search Result was found"}]
        for result in results:
            metadata_result = {
                "snippet": result["snippet"],
                "title": result["name"],
                "link": result["url"],
            }
            metadata_results.append(metadata_result)

        return metadata_results
