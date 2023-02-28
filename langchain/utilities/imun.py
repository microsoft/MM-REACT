"""Util that Image Understanding.

In order to set this up, follow instructions at:
https://azure.microsoft.com/en-us/products/cognitive-services/computer-vision
"""
from typing import Dict, List

import requests
from pydantic import BaseModel, Extra, root_validator

from langchain.utils import get_from_dict_or_env

def download_image(url):
    """Download raw image from url
    """
    r = requests.get(url, stream=True, timeout=0.5)
    assert r.status_code == 200, "Invalid URL"
    return r.content

def resize_image(data):
    # TODO: resize if h < 60 or w < 60 or data_len > 1024 * 1024 * 4
    return data

def _get_box(box):
    return f"x: {box['x']} y: {box['y']} width: {box['w']} height: {box['h']}"

class ImunAPIWrapper(BaseModel):
    """Wrapper for Image Understanding API.

    In order to set this up, follow instructions at:
    https://azure.microsoft.com/en-us/products/cognitive-services/computer-vision
    """

    imun_subscription_key: str
    imun_url: str

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def _imun_results(self, img_url: str) -> List[dict]:
        headers = {"Ocp-Apim-Subscription-Key": self.imun_subscription_key}
        params = {
            "api-version": "2023-02-01-preview",
            "features": "denseCaptions,Tags,Read",
        }
        response = requests.post(
            self.imun_url, data=resize_image(download_image(img_url)), headers=headers, params=params  # type: ignore
        )
        response.raise_for_status()
        api_results = response.json()
        results = {"captions": [], "objects": [], "texts": []}
        for o in api_results["denseCaptionsResult"]["values"]:
            results["captions"].append(f'{o["text"]} at location {_get_box(o["boundingBox"])}')
        for o in api_results["tagsResult"]["values"]:
            results["tags"].append(f'{o["name"]}')
        return results

    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and endpoint exists in environment."""
        imun_subscription_key = get_from_dict_or_env(
            values, "imun_subscription_key", "IMUN_SUBSCRIPTION_KEY"
        )
        values["imun_subscription_key"] = imun_subscription_key

        imun_url = get_from_dict_or_env(
            values,
            "imun_url",
            "IMUN_URL",
            # default="https://api.bing.microsoft.com/v7.0/search",
        )

        values["imun_url"] = imun_url

        return values

    def run(self, query: str) -> str:
        """Run query through Image Understanding and parse result."""
        results = self._imun_results(query)
        captions = "\n".join(results["captions"])
        tags = "\n".join(results["tags"])
        if not captions and not tags:
            return "A blurry image"
        
        result = f"""An image containing some tags and objects
        tags seen in the image: {tags}
        objects and their location in the image: {captions}
        """
        return result

    def results(self, query: str) -> List[Dict]:
        """Run query through Image Understanding and return metadata.

        Args:
            query: The query to search for.
            num_results: The number of results to return.

        Returns:
            A dictionary of lists, with dictionaries with the following keys:
                caption - The description of the object.
                tag - The tag in image.
                text - The OCR result.
        """
        results = self._imun_results(query)
        return results
