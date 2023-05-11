"""Generic utility functions."""
import os
from typing import Any, Dict, Optional, Tuple
import requests
import io
import re
from PIL import Image


def get_from_dict_or_env(
    data: Dict[str, Any], key: str, env_key: str, default: Optional[str] = None
) -> str:
    """Get a value from a dictionary or an environment variable."""
    if key in data and data[key]:
        return data[key]
    elif env_key in os.environ and os.environ[env_key]:
        return os.environ[env_key]
    elif default is not None:
        return default
    else:
        raise ValueError(
            f"Did not find {key}, please add an environment variable"
            f" `{env_key}` which contains it, or pass"
            f"  `{key}` as a named parameter."
        )

def download_image(url:str):
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
        if ext in [".jpg", ".png", ".bmp", ".jpeg", ".pdf"]:
            with open(url, "rb") as fp:
                return fp.read()
        raise

def im_downscale(data, target_size):
    output = io.BytesIO()
    im = Image.open(io.BytesIO(data))
    w, h = im.size
    if target_size is None:
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        im.save(output, format="JPEG")
        return output.getvalue(), (w, h)
    im_size_max = max(w, h)
    im_scale = float(target_size) / float(im_size_max)
    w, h = int(w * im_scale), int(h * im_scale)
    im = im.resize((w, h))
    if im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    im.save(output, format="JPEG")
    return output.getvalue(), (w, h)


def im_upscale(data, target_size):
    im = Image.open(io.BytesIO(data))
    w, h = im.size
    im_size_min = min(w, h)
    im_scale = float(target_size) / float(im_size_min)
    w, h = int(w * im_scale), int(h * im_scale)
    im = im.resize((w, h))
    output = io.BytesIO()
    if im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    im.save(output, format="JPEG")
    return output.getvalue(), (w, h)

def get_url_path(query:str, return_end=False)->Tuple[int,str]:
    match = re.search(r"https?://.+\.(?:jpg|jpeg|png|bmp|pdf)", query, re.IGNORECASE)
    if match:
        if return_end:
            return match.start(), match.end(), match.group(0)
        return match.start(), match.group(0)
    match = re.search(r"https?://\S+", query, re.IGNORECASE)
    if match:
        url = match.group(0)
        if url.endswith((".", "?", '"')):
            url = url[:-1]
        if return_end:
            return match.start(), match.end(), url
        return match.start(), url
    match = re.search(r"/[\w/-]+\.(?:jpg|jpeg|png|bmp|pdf)", query, re.IGNORECASE)
    if match:
        if return_end:
            return match.start(), match.end(), match.group(0)
        return match.start(), match.group(0)
    if return_end:
        return -1, -1, ""
    return -1, ""
