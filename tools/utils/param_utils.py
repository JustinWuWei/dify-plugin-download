import json
from typing import Mapping


def parse_json_string_dict(json_str: str) -> Mapping[str, str]:
    if not json_str:
        return {}
    try:
        data = json.loads(json_str)
    except:
        raise ValueError("invalid json")
    if not isinstance(data, dict):
        raise ValueError("Input JSON string must represent a dictionary.")
    str_dict: Mapping[str, str] = {key: str(value) for key, value in data.items()}
    return str_dict
