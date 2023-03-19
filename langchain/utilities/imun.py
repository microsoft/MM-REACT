"""Util that Image Understanding.

In order to set this up, follow instructions at:
https://azure.microsoft.com/en-us/products/cognitive-services/computer-vision
"""
import time
from typing import Dict, List, Tuple
import io
import imagesize

import requests
from pydantic import BaseModel, Extra, root_validator

from langchain.utils import get_from_dict_or_env, download_image, im_downscale, im_upscale

IMUN_PROMPT_PREFIX = "This is an image ({width} x {height})"

IMUN_PROMPT_DESCRIPTION = " with description {description}.\n"

IMUN_PROMPT_CAPTIONS_PEFIX = " objects and their descriptions"

IMUN_PROMPT_TAGS_PEFIX = " object tags"

IMUN_PROMPT_OCR_PEFIX = " {style}text"

IMUN_PROMPT_FACES_PEFIX = " faces"

IMUN_PROMPT_CELEB_PEFIX = " celebrities"

IMUN_PROMPT_CAPTIONS = """
List of object descriptions, and their locations in this image:
{captions}
"""

IMUN_PROMPT_TAGS="""
List of object tags seen in this image:
{tags}
"""

IMUN_PROMPT_WORDS="""
List of texts (words) seen in this image:
{words}
"""

IMUN_PROMPT_LANGUAGES="""
The above words are in these languages:
{languages}
"""

IMUN_PROMPT_LANGUAGE="""
The above words are in this language:
{language}
"""

IMUN_PROMPT_FACES="""
Detected faces, and their location in this image:
{faces}
"""

IMUN_PROMPT_CELEBS="""
List of celebrities, and their location in this image:
{celebs}
"""


def resize_image(data, img_url):
    """resize if h < 60 or w < 60 or data_len > 1024 * 1024 * 4"""
    try:
        # Using imagesize to avoid decoding when not needed
        w, h = imagesize.get(io.BytesIO(data))
    except:
        return data, (None, None)
    data_len = len(data)
    if data_len > 1024 * 1024 * 4:
        if not img_url.endswith((".jpg", ".jpeg")):
            # first try just compression
            data, (w, h) = im_downscale(data, None)
            data_len = len(data)
            if data_len <= 1024 * 1024 * 4:
                return data, (w, h)
        # too large
        data, (w, h) = im_downscale(data, 2048)
    if w < 60 or h < 60:
        # too small
        data, (w, h) = im_upscale(data, 60)
    return data, (w, h)


def _get_box(rect):
    rect = rect.get("boundingBox") or rect.get("faceRectangle") or rect["rectangle"]
    x, y = rect['x'] if 'x' in rect else rect['left'], rect['y'] if 'y' in rect else rect['top']
    w, h = rect['w'] if 'w' in rect else rect['width'], rect['h'] if 'h' in rect else rect['height']
    return [x, y, x+w, y+h]

def _get_person(o):
    age = o.get("age") or 25
    gender = (o.get("gender") or "").lower()
    if age < 20:
        if gender == "female":
            return "young woman"
        if gender == "male":
            return "young man"
        return "young person"
    if gender == "female":
        return "woman"
    if gender == "male":
        return "man"
    return "person"

def _is_handwritten(styles):
    handwritten = False
    for style in styles:
        if not style["isHandwritten"]:
            return False
        handwritten = True
    return handwritten

def _parse_document(analyzeResult):
    content = analyzeResult["content"]
    new_total = False
    total = 0.0
    # remove extra newlines in the items
    for doc in analyzeResult["documents"]:
        fields = doc.get("fields") or {}
        for item in (fields.get("Items") or {}).get("valueArray") or []:
            subitem = item.get("content") or ""
            if "\n" in subitem:
                content = content.replace(subitem, subitem.replace("\n", " "))
            price = ((item.get("valueObject") or {}).get("TotalPrice") or {}).get("valueNumber")
            if price:
                new_total = True
                total += price
    if new_total:
        content += f"\nTotal amount {total}" 
    return content.split("\n")    

def _parse_table(analyzeResult):
    found_table = False
    raw_content:str = analyzeResult["content"]
    content = []
    for table in analyzeResult["tables"]:
        row_count = table["rowCount"]
        col_count = table["columnCount"]
        if found_table:
            # more than one table
            content.append("")
        found_table = True
        for row in range(row_count):
            cols = [""] * col_count
            is_header = False
            for cell in table.get("cells") or []:
                if cell.get("rowIndex") != row:
                    continue
                text = cell["content"]
                raw_content = raw_content.replace(text, "", 1)
                cols[cell["columnIndex"]] = text
                is_header = cell.get("kind") == "columnHeader"
            line = "|" + "|".join(cols) + "|"
            content.append(line)
            if is_header:
                line = "|" + "|".join(["---"] * col_count) + "|"
                content.append(line)

    # TODO: keep out of table words before/after the table based on their coordinates
    # keep words not in the table
    raw_content = "\n".join([t.strip() for t in raw_content.split("\n")]).strip()
    if raw_content:
        content = [raw_content, ""] + content
    return content

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
        err_code = innererror.get('code') or error.get("code") or err.get("code")
        err_msg = innererror.get('message') or error.get("message") or err.get("message")
        if response.status_code == 400 and err_code == "InvalidImageSize":
            raise InvalidImageSize(f"{err_code}({err_msg})")
        if response.status_code == 400 and err_code == "InvalidImageFormat":
            raise InvalidImageFormat(f"{err_code}({err_msg})")
        if response.status_code == 400 and err_code == "InvalidRequest":
            raise InvalidRequest(f"{err_code}({err_msg})")
    except ValueError:
        pass
    response.raise_for_status()

def _concat_objects(objects: List) -> str:
    objects = [f'{n} {v[0]} {v[1]} {v[2]} {v[3]}' for (n, v) in objects]
    return "\n".join(objects)

def intersection(o:List[float], c:List[float]) -> Tuple[float]:
    ox1, oy1, ox2, oy2 = o
    cx1, cy1, cx2, cy2 = c

    # height and width
    o_h = oy2 - oy1
    o_w = ox2 - ox1
    c_h = cy2 - cy1
    c_w = cx2 - cx1

    o_area = o_w * o_h
    c_area = c_w * c_h
  
    max_x1 = max(ox1, cx1)
    max_y1 = max(oy1, cy1)
    min_x2 = min(ox2, cx2)
    min_y2 = min(oy2, cy2)
    inter = (min_x2 > max_x1) * (min_y2 > max_y1)
    inter = inter * (min_x2 - max_x1) * (min_y2 - max_y1)

    return inter, o_area, c_area

def _merge_objects(objects: List, captions: List) -> List:
    """Merge objects into captions
    If no overallping this would be equivalent to objects + captions
    """
    if not captions:
        return objects
    new_objects = []
    for ob in objects:
        o = ob[1]
        max_ioa = 0
        for ca in captions:
            c = ca[1]
            inter, o_area, c_area = intersection(o, c)
            ioa = inter / c_area
            if ioa > max_ioa:
                max_ioa = ioa
        if max_ioa < 0.3:
            new_objects.append(ob)

    return captions + new_objects

def create_prompt(results: Dict) -> str:
    """Create the final prompt output"""
    if "size" in results:
        width, height = results["size"]["width"], results["size"]["height"]
        answer = IMUN_PROMPT_PREFIX.format(width=width, height=height)
    else:
        answer = "This is an image"

    description = results.get("description") or ""
    captions: List = results.get("captions") or []
    tags = results.get("tags") or ""
    objects: List = results.get("objects") or []
    words = results.get("words") or ""
    words_style = results.get("words_style") or ""
    languages = results.get("languages") or ""
    faces: List = results.get("faces") or []
    celebrities: List = results.get("celebrities") or []

    if description:
        answer += IMUN_PROMPT_DESCRIPTION.format(description=description) if description else ""

    found = False
    if captions or objects:
        answer += "\nThis image contains"
        answer += IMUN_PROMPT_CAPTIONS_PEFIX
        found = True
    if tags:
        answer += "," if found else "\nThis image contains"
        answer += IMUN_PROMPT_TAGS_PEFIX
        found = True
    if words:
        answer += "," if found else "\nThis image contains"
        answer += IMUN_PROMPT_OCR_PEFIX.format(style=words_style)
        found = True
    if faces:
        answer += "," if found else "\nThis image contains"
        answer += IMUN_PROMPT_FACES_PEFIX
        found = True
    if celebrities:
        answer += "," if found else "\nThis image contains"
        answer += IMUN_PROMPT_CELEB_PEFIX
        found = True

    answer += "\n"

    if not found and not description:
        # did not find anything
        task = results.get("task") or ""
        if task == "OCR":
            return answer + "This image is too blurry for OCR text extraction"
        if task == "celebrities":
            return answer + "Did not find any celebrities in this image"
        return answer + "This image is too blurry"
    
    if objects and captions:
        answer += IMUN_PROMPT_CAPTIONS.format(captions=_concat_objects(_merge_objects(objects, captions)))
    else:
        if captions:
            answer += IMUN_PROMPT_CAPTIONS.format(captions=_concat_objects(captions))
        if objects:
            answer += IMUN_PROMPT_CAPTIONS.format(captions=_concat_objects(objects))
    if tags:
        answer += IMUN_PROMPT_TAGS.format(tags="\n".join(tags))
    if words:
        answer += IMUN_PROMPT_WORDS.format(words="\n".join(words))
        if languages:
            langs = set(languages)
            if len(langs) == 1 and languages[0] != "en":
                answer += IMUN_PROMPT_LANGUAGE.format(language=languages[0])
            elif len(langs) > 1 or languages[0] != "en":
                answer += IMUN_PROMPT_LANGUAGES.format(languages="\n".join(languages))
    if faces:
        answer += IMUN_PROMPT_FACES.format(faces=_concat_objects(faces))
    if celebrities:
        answer += IMUN_PROMPT_CELEBS.format(celebs=_concat_objects(celebrities))
    return answer


class ImunAPIWrapper(BaseModel):
    """Wrapper for Image Understanding API.

    In order to set this up, follow instructions at:
    https://azure.microsoft.com/en-us/products/cognitive-services/computer-vision
    """

    cache: dict  #: :meta private:
    imun_subscription_key: str
    imun_url: str
    params: dict  # "api-version=2023-02-01-preview&features=denseCaptions,Tags"

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def _imun_results(self, img_url: str) -> dict:
        param_str = '&'.join([f'{k}={v}' for k,v in self.params.items()])
        key = f"{self.imun_url}?{param_str}&data={img_url}"
        if key in self.cache:
            return self.cache[key]
        results = {}
        if "celebrities" in self.imun_url:
            results["task"] = "celebrities"
        elif "Read" in "param_str":
            results["task"] = "OCR"
        else:
            for task in ['prebuilt-read', 'prebuilt-receipt', 'prebuilt-businessCard', 'prebuilt-layout']:
                if task in self.imun_url:
                    results["task"] = "OCR"
        w, h = None, None
        headers = {"Ocp-Apim-Subscription-Key": self.imun_subscription_key, "Content-Type": "application/octet-stream"}
        try:
            data, (w, h) = resize_image(download_image(img_url), img_url)
        except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema, FileNotFoundError):
            return
        if w is not None and h is not None:
            results["size"] = {"width": w, "height": h}
        response = requests.post(
            self.imun_url, data=data, headers=headers, params=self.params  # type: ignore
        )
        _handle_error(response)
        api_results = None
        delayed_job = response.headers.get("Operation-Location")
        if delayed_job:
            headers = {"Ocp-Apim-Subscription-Key": self.imun_subscription_key}
            running = True
            while running:
                time.sleep(0.1)
                response = requests.get(
                    delayed_job, headers=headers  # type: ignore
                )
                _handle_error(response)
                api_results = response.json()
                running = (api_results["status"] or "failed") == "running"
        
        if api_results is None:
            api_results = response.json()

        if "metadata" in api_results:
            results["size"] = api_results["metadata"]

        if "description" in api_results:
            results["tags"] = api_results["description"]["tags"]
            for o in api_results["description"]["captions"]:
                results["description"] = o["text"]
                break
        if "tags" in api_results:
            results["tags"] = [o["name"] for o in api_results["tags"]]
        if "objects" in api_results:
            results["objects"] = [(o.get("object") or o["name"], _get_box(o)) for o in api_results["objects"]]
        if "faces" in api_results:
            results["faces"] = [(_get_person(o), _get_box(o)) for o in api_results["faces"]]
        if "result" in api_results:
            results["celebrities"] = [(o["name"], _get_box(o)) for o in api_results["result"]["celebrities"]]

        if "denseCaptionsResult" in api_results:
            results["captions"] = []
            for idx, o in enumerate(api_results["denseCaptionsResult"]["values"]):
                if idx == 0:
                    # fist one is the image description
                    results["description"] = o['text']
                    continue
                results["captions"].append((o["text"], _get_box(o)))
        if "captionResult" in api_results:
            results["description"] = api_results["captionResult"]['text']
        if "tagsResult" in api_results:
            results["tags"] = [o["name"] for o in api_results["tagsResult"]["values"]]
        if "readResult" in api_results:
            words = api_results["readResult"]["pages"][0]["words"]
            words = [o["content"] for o in words]
            if words:
                results["words"] = words
            if _is_handwritten(api_results["readResult"]["styles"]):
                results["words_style"] = "handwritten "
        if "analyzeResult" in api_results:
            is_table = False
            is_document = False
            if "size" not in results:
                for idx, page in enumerate(api_results["analyzeResult"]["pages"]):
                    results["size"] = {"width": page["width"], "height": page["height"]}
                    break
            for doc in api_results["analyzeResult"].get("documents") or []:
                if doc.get("fields"):
                    is_document = True
                    break
            for doc in api_results["analyzeResult"].get("tables") or []:
                if doc.get("cells") and doc.get("rowCount"):
                    is_table = True
                    break
            if is_table:
                results["words"] = _parse_table(api_results["analyzeResult"])
            elif is_document:
                results["words"] = _parse_document(api_results["analyzeResult"])
            else:
                for idx, page in enumerate(api_results["analyzeResult"]["pages"]):
                    lines = [o["content"]  for o in page["lines"]]
                    if lines:
                        results["words"] = lines
                    break  # TODO: handle more pages
                if _is_handwritten(api_results["analyzeResult"]["styles"]):
                    results["words_style"] = "handwritten "
                languages = []
                for l in api_results["analyzeResult"].get("languages") or []:
                    locale = l['locale']
                    if locale == 'en' or (l.get("confidence") or 0) > 0.9:
                        languages.append(locale)
                if languages:
                    results["languages"] = languages
        self.cache[key] = results
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
        values["cache"] = {}

        params = get_from_dict_or_env(values, "params", "IMUN_PARAMS")
        if isinstance(params, str):
            params = dict([[v.strip() for v in p.split("=")] for p in params.split("&")])
        values["params"] = params

        return values

    def run(self, query: str) -> str:
        """Run query through Image Understanding and parse result."""
        results = self._imun_results(query)
        if results is None:
            return "This is an invalid url"
        return create_prompt(results)

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

class ImunMultiAPIWrapper(BaseModel):
    """Wrapper for Multi Image Understanding API.
    """
    imuns: List[ImunAPIWrapper]

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def run(self, query: str) -> str:
        """Run query through Multiple Image Understanding and parse the aggregate result."""
        results = self.results(query)
        if results is None:
            return "This is an invalid url"
        return create_prompt(results)
        
    def results(self, query: str) -> List[Dict]:
        """Run query through All Image Understanding tools and aggregate the metadata.

        Args:
            query: The query to search for.

        Returns:
            A dictionary of lists
        """
        results = {}
        for imun in self.imuns:
            result = imun.results(query)
            if result is None:
                return None
            for k,v in result.items():
                results[k] = v
        return results
