"""Generic utility functions."""
import os
from typing import Any, Dict, Optional
import requests


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
