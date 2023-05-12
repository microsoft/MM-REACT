"""Util that Image Understanding.

In order to set this up, follow instructions at:
https://azure.microsoft.com/en-us/products/cognitive-services/computer-vision
"""
import time
from typing import Dict, List, Tuple, Optional
import io
import imagesize

import requests
from pydantic import BaseModel, Extra, root_validator

from langchain.utils import get_from_dict_or_env, download_image, im_downscale, im_upscale

IMUN_PROMPT_DESCRIPTION = "Image description is: {description}.\n"

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
List of OCR texts (words) seen in this image:
{words}
"""

IMUN_PROMPT_LANGUAGES="""
The above texts are in these languages:
{languages}
"""

IMUN_PROMPT_LANGUAGE="""
The above texts are in this language:
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
        assert w > 0 and h > 0
    except:
        return data, (None, None)
    img_url = img_url.lower()
    if img_url.endswith((".webp")):
        # just convert few formats that we do not support otherwise
        data, (w, h) = im_downscale(data, None)
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
            return "a young woman"
        if gender == "male":
            return "a young man"
        return "a young person"
    if gender == "female":
        return "a woman"
    if gender == "male":
        return "a man"
    return "a person"

def _is_handwritten(styles):
    handwritten = False
    for style in styles:
        if not style["isHandwritten"]:
            return False
        handwritten = True
    return handwritten

def _isascii(s):
    return len(s) == len(s.encode())
                         
def _parse_lines(analyzeResult:Dict)->Tuple[List[str],List[str]]:
    lines = []
    for _, page in enumerate(analyzeResult["pages"]):
        lines += [o["content"] for o in page["lines"]]
    text = "\n".join(lines)
    languages = []
    for l in analyzeResult.get("languages") or []:
        locale = l['locale']
        if locale == "en":
            languages.append(locale)
            continue
        if (l.get("confidence") or 0) < 0.9:
            continue
        # check if it is really not English
        for span in l.get("spans") or []:
            offset, length = span["offset"], span["length"]
            line = text[offset:offset + length]
            if not _isascii(line):
                languages.append(locale)
                break
    return lines, languages

def _parse_document(analyzeResult:Dict)->List[str]:
    content:str = analyzeResult["content"]
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

def _parse_table(analyzeResult:Dict)->List[str]:
    raw_content = list(analyzeResult["content"])
    for table in analyzeResult["tables"]:
        row_count = table["rowCount"]
        col_count = table["columnCount"]
        table_content = "\n"
        for row in range(row_count):
            cols = [""] * col_count
            is_header = False
            for cell in table.get("cells") or []:
                if cell.get("rowIndex") != row:
                    continue
                text = cell["content"]
                col = cell["columnIndex"]
                cols[col] = text
                is_header = cell.get("kind") == "columnHeader"
            line = "|" + "|".join(cols) + "|"
            table_content += line + "\n"
            if is_header:
                line = "|" + "|".join(["---"] * col_count) + "|"
                table_content += line  + "\n"
        for span in table["spans"]:
            offset, length = span["offset"], span["length"]
            for idx in range(offset, offset + length):
                raw_content[idx] = ""
            if table_content:
                raw_content[offset] = table_content
                table_content = ""
    raw_content = "".join(raw_content)
    return raw_content.split("\n")

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

def _cartesian_center(v:List[int], size=None) -> List[int]:
    if size:
        image_width, image_height = size["width"], size["height"]
    else:
        image_width = image_height = max(v)

    width = v[2] - v[0]
    height = v[3] - v[1]
    # Use center of the box
    x = v[0] + width // 2
    y = v[1] + height // 2
    y = image_height - v[1]
    return [(100 * x) // image_width, (100 * y) // image_height]

def _concat_objects(objects: List, size=None) -> str:
    # normalize if size given, cartesian 
    objects = [(n, _cartesian_center(v, size)) for (n, v) in objects]
    objects = [f'{n} {v[0]} {v[1]}' for (n, v) in objects]
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
    img_url = results.get("img_url") or ""
    description = results.get("description") or ""
    captions: List = results.get("captions") or []
    tags = results.get("tags") or ""
    objects: List = results.get("objects") or []
    words = results.get("words") or ""
    words_style = results.get("words_style") or ""
    languages = results.get("languages") or ""
    faces: List = results.get("faces") or []
    celebrities: List = results.get("celebrities") or []

    answer = img_url + "\n" if img_url else ""
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
        task = results.get("task") or []
        task_done = False
        if "OCR" in task:
            answer += "This image is too blurry for OCR text extraction"
            task_done = True 
        if "celebrities" in task:
            if task_done:
                answer += "\n"
            answer += "Did not find any celebrities in this image"
            task_done = True
        if not task_done:
            answer += "This image is too blurry"
        return answer
    
    size = results.get("size")
    if objects and captions:
        answer += IMUN_PROMPT_CAPTIONS.format(captions=_concat_objects(_merge_objects(objects, captions), size=size))
    else:
        if captions:
            answer += IMUN_PROMPT_CAPTIONS.format(captions=_concat_objects(captions, size=size))
        if objects:
            answer += IMUN_PROMPT_CAPTIONS.format(captions=_concat_objects(objects, size=size))
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
        answer += IMUN_PROMPT_FACES.format(faces=_concat_objects(faces, size=size))
    if celebrities:
        answer += IMUN_PROMPT_CELEBS.format(celebs=_concat_objects(celebrities, size=size))
    return answer

class ImunCache(BaseModel):
    cache: Optional[dict] = {}  #: :meta private:
    class Config:
        copy_on_model_validation = 'none'
    
    def get(self, key:str)->dict:
        return self.cache.get(key)

    def set(self, key:str, value:dict):
        self.cache[key] = value

class ImunAPIWrapper(BaseModel):
    """Wrapper for Image Understanding API.

    In order to set this up, follow instructions at:
    https://azure.microsoft.com/en-us/products/cognitive-services/computer-vision
    """

    cache: Optional[ImunCache]  #: :meta private:
    imun_subscription_key: str
    imun_url: str
    params: dict  # "api-version=2023-02-01-preview&features=denseCaptions,Tags"

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def _imun_results(self, img_url: str) -> dict:
        param_str = '&'.join([f'{k}={v}' for k,v in self.params.items()])
        key = f"{self.imun_url}?{param_str}"
        img_cache = self.cache.get(img_url) or {}
        results = img_cache.get(key) or {}
        if results:
            results["img_url"] = img_url
            return results
        self.cache.set(img_url, img_cache)
        results = {"task": [], "img_url": img_url}
        if "celebrities" in self.imun_url:
            results["task"].append("celebrities")
        elif "Read" in "param_str":
            results["task"].append("OCR")
        else:
            for task in ['prebuilt-read', 'prebuilt-receipt', 'prebuilt-businessCard', 'prebuilt-layout']:
                if task in self.imun_url:
                    results["task"].append("OCR")
                    break
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
            values = api_results["denseCaptionsResult"]["values"]
            values = sorted(values, key=lambda x: x['boundingBox']['w'] * x['boundingBox']['h'], reverse=True)
            for idx, o in enumerate(values):
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
            analyzeResult = api_results["analyzeResult"]
            if "size" not in results:
                for idx, page in enumerate(analyzeResult["pages"]):
                    results["size"] = {"width": page["width"], "height": page["height"]}
                    break
            for doc in analyzeResult.get("documents") or []:
                if doc.get("fields"):
                    is_document = True
                    break
            for doc in analyzeResult.get("tables") or []:
                if doc.get("cells") and doc.get("rowCount"):
                    is_table = True
                    break
            if is_table:
                results["words"] = _parse_table(analyzeResult)
            elif is_document:
                results["words"] = _parse_document(analyzeResult)
            else:
                lines, languages = _parse_lines(analyzeResult)
                if lines:
                    results["words"] = lines
                if languages:
                    results["languages"] = languages
                if _is_handwritten(analyzeResult["styles"]):
                    results["words_style"] = "handwritten "
        img_cache[key] = results
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
        values["cache"] = values.get("cache") or {}

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
