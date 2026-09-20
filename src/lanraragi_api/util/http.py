from typing import Any

HeaderType = dict[str, Any]
ParamType = dict[str, Any]


def merge_headers(
    old_headers: HeaderType | None = None, new_headers: HeaderType | None = None
) -> HeaderType:
    """Merge the new headers into the old headers.

    New headers wine over old headers of the same name.

    Args:
        old_headers: default headers. Defaults to None, which will be an empty dict.
        new_headers: new headers. Defaults to None, which will be an empty dict.

    Returns:
        dict: Headers merged, defaults included.
    """
    if old_headers is None:
        old_headers = {}
    if new_headers is None:
        new_headers = {}
    merged: HeaderType = dict(new_headers)
    for k in old_headers:
        if k in merged:
            continue
        merged[k] = old_headers[k]
    return merged


def merge_params(
    old_params: ParamType | None = None, new_params: ParamType | None = None
) -> ParamType:
    """Merge the new query parameters into the old query parameters.

    New query parameters wine over old query parameters of the same name.

    Args:
        old_params: default query parameters. Defaults to None, which will be an empty dict.
        new_params: new query parameters. Defaults to None, which will be an empty dict.

    Returns:
        dict: query parameters merged, defaults included.
    """
    if old_params is None:
        old_params = {}
    if new_params is None:
        new_params = {}
    merged: ParamType = dict(new_params)
    for k in old_params:
        if k in merged:
            continue
        merged[k] = old_params[k]
    return merged


def normalize_params(params: ParamType) -> ParamType:
    """Normalize query parameters by overriding the default marshalling of some
    types to fit the HTTP standard.
    """
    new_params: ParamType = {}
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, bool):
            # requests won't encoding bool value to lowercase string
            v = "true" if v else "false"
        new_params[k] = v

    return new_params
