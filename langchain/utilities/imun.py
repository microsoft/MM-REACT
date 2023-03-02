"""Util that Image Understanding.

In order to set this up, follow instructions at:
https://azure.microsoft.com/en-us/products/cognitive-services/computer-vision
"""
import os
from typing import Dict, List

import requests
from pydantic import BaseModel, Extra, root_validator

from langchain.utils import get_from_dict_or_env

IMUN_PROMPT_PREFIX = "This is an image (of size width: {width} height: {height})"

IMUN_PROMPT_DESCRIPTION = " with description {description}.\n"

IMUN_PROMPT_CAPTIONS_PEFIX = " objects and their descriptions"

IMUN_PROMPT_TAGS_PEFIX = " object tags"

IMUN_PROMPT_OCR_PEFIX = " text"

IMUN_PROMPT_CAPTIONS = """
List of object descriptions, and their locations in this image:
{captions}
"""

IMUN_PROMPT_TAGS="""
List of object tags seen in this image:
{tags}
"""

IMUN_PROMPT_WORDS="""
List of text (words) seen in this image:
{words}
"""


def download_image(url):
    """Download raw image from url
    """
    try:
        headers = {'User-Agent': 'langchain imun'}
        r = requests.get(url, stream=True, headers=headers, timeout=2)
        assert r.status_code == 200, "Invalid URL"
        return r.content
    except requests.exceptions.MissingSchema:
        # This should be configured because of security
        ext = os.path.splitext(url)[1].lower()
        if ext in [".jpg", ".png", ".bmp", ".jpeg"]:
            with open(url, "rb") as fp:
                return fp.read()
        raise

def resize_image(data):
    # TODO: resize if h < 60 or w < 60 or data_len > 1024 * 1024 * 4
    return data

def _get_box(rect):
    rect = rect.get("boundingBox") or rect["rectangle"]
    x, y = rect['x'] if 'x' in rect else rect['left'], rect['y'] if 'y' in rect else rect['top']
    w, h = rect['w'] if 'w' in rect else rect['width'], rect['h'] if 'h' in rect else rect['height']
    return f"x: {x} y: {y} width: {w} height: {h}"

class InvalidRequest(requests.HTTPError):
    pass

class InvalidImageSize(InvalidRequest):
    pass

class InvalidImageFormat(InvalidRequest):
    pass

def _handle_error(response):
    if response.status_code == 200:
        return
    try:
        # Handle error messages from various versions
        err = response.json()
        error = err.get("error") or {}
        innererror = error.get("innererror") or {}
        err_code = err.get("code") or error.get("code") or innererror.get('code')
        err_msg = err.get("message") or error.get("message") or innererror.get('message')
        if response.status_code == 400 and err_code == "InvalidImageSize":
            raise InvalidImageSize(f"{err_code}({err_msg})")
        if response.status_code == 400 and err_code == "InvalidImageFormat":
            raise InvalidImageFormat(f"{err_code}({err_msg})")
        if response.status_code == 400 and err_code == "InvalidRequest":
            raise InvalidRequest(f"{err_code}({err_msg})")
    except ValueError:
        pass
    response.raise_for_status()

class ImunAPIWrapper(BaseModel):
    """Wrapper for Image Understanding API.

    In order to set this up, follow instructions at:
    https://azure.microsoft.com/en-us/products/cognitive-services/computer-vision
    """

    imun_subscription_key: str
    imun_url: str
    params: dict  # "api-version=2023-02-01-preview&features=denseCaptions,Tags"

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def _imun_results(self, img_url: str) -> List[dict]:
        headers = {"Ocp-Apim-Subscription-Key": self.imun_subscription_key, "Content-Type": "application/octet-stream"}
        response = requests.post(
            self.imun_url, data=resize_image(download_image(img_url)), headers=headers, params=self.params  # type: ignore
        )
        _handle_error(response)
        
        api_results = response.json()
        results = {"size": api_results["metadata"]}

        if "description" in api_results:
            results["tags"] = api_results["description"]["tags"]
            for o in api_results["description"]["captions"]:
                results["description"] = o["text"]
                break
        if "tags" in api_results:
            results["tags"] = [o["name"] for o in api_results["tags"]]
        if "objects" in api_results:
            results["objects"] = [f'{o.get("object") or o["name"]} at location {_get_box(o)}' for o in api_results["objects"]]
        if "denseCaptionsResult" in api_results:
            results["captions"] = []
            for idx, o in enumerate(api_results["denseCaptionsResult"]["values"]):
                if idx == 0:
                    results["description"] = o['text']
                    continue
                results["captions"].append(f'{o["text"]} at location {_get_box(o)}')
        if "captionResult" in api_results:
            results["description"] = api_results["captionResult"]['text']
        if "tagsResult" in api_results:
            results["tags"] = [o["name"] for o in api_results["tagsResult"]["values"]]
        if "readResult" in api_results:
            words = api_results["readResult"]["pages"][0]["words"]
            words = [f'{o["content"]}' for o in words]
            if words:
                results["words"] = words
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
            # default="https://westus.api.cognitive.microsoft.com/computervision/imageanalysis:analyze",
        )

        values["imun_url"] = imun_url

        params = get_from_dict_or_env(values, "params", "IMUN_PARAMS")
        if isinstance(params, str):
            params = dict([[v.strip() for v in p.split("=")] for p in params.split("&")])
        values["params"] = params

        return values

    def run(self, query: str) -> str:
        """Run query through Image Understanding and parse result."""
        results = self._imun_results(query)
        width, height = results["size"]["width"], results["size"]["height"]
        answer = IMUN_PROMPT_PREFIX.format(width=width, height=height)

        description = results.get("description") or ""
        captions = results.get("captions") or ""
        tags = results.get("tags") or ""
        objects = results.get("objects") or ""
        words = results.get("words") or ""

        if description:
            answer += IMUN_PROMPT_DESCRIPTION.format(description=description) if description else ""

        found = False
        if captions:
            answer += "\nThis image contains"
            answer += IMUN_PROMPT_CAPTIONS_PEFIX
            found = True
        if objects:
            answer += "," if found else "\nThis image contains"
            answer += IMUN_PROMPT_CAPTIONS_PEFIX
            found = True
        if tags:
            answer += "," if found else "\nThis image contains"
            answer += IMUN_PROMPT_TAGS_PEFIX
            found = True
        if words:
            answer += "," if found else "\nThis image contains"
            answer += IMUN_PROMPT_OCR_PEFIX
            found = True

        if not found and not description:
            # did not find anything
            return answer + "\nThis image is too blurry"
        
        if captions:
            captions = "\n".join(captions)
            answer += IMUN_PROMPT_CAPTIONS.format(captions=captions)
        if objects:
            objects = "\n".join(objects)
            answer += IMUN_PROMPT_CAPTIONS.format(captions=objects)
        if tags:
            tags = "\n".join(tags)
            answer += IMUN_PROMPT_TAGS.format(tags=tags)
        if words:
            tags = "\n".join(tags)
            answer += IMUN_PROMPT_WORDS.format(words=words)
        return answer

    def results(self, query: str) -> List[Dict]:
        """Run query through Image Understanding and return metadata.

        Args:
            query: The query to search for.
            num_results: The number of results to return.

        Returns:
            A dictionary of lists, with dictionaries with the following keys:
                size - width and height of the image
                description - Top level image description.
                captions - The description of the object.
                tags - The tags seen in the image.
        """
        results = self._imun_results(query)
        return results
