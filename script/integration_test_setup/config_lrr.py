"""
config_lrr.py

Usage:
  uv run script/integration_test_setup/config_lrr.py --base-url http://localhost:33333 --lrr-container-name lrr

What it does:
  - Tries to log in via the web login form (POST to the login endpoint).
  - GETs the /config page, parses the config form and collects current values.
  - Sets the custom config to the provided value.
  - POSTs the form back to the server to save the config.
"""

import sys
from pathlib import Path

# Get the directory of the current script
script_dir = Path(__file__).resolve().parent
sys.path.append(str(script_dir))


import argparse
import json
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from docker import restart, wait_for_healthy

# endpoints to try (login & config)
LOGIN_ENDPOINTS = ["login"]
CONFIG_GET_ENDPOINTS = ["config"]
CONFIG_POST_ENDPOINTS = ["config"]

USER_AGENT = "lanraragi-config-script/1.0"


def norm_url(base, path):
    return urljoin(base.rstrip("/") + "/", path)


def try_login(session: requests.Session, base_url: str, password: str):
    if not password:
        print(
            "[*] No password provided, skipping login (server might have password disabled)."
        )
        return True

    session.headers.update({"User-Agent": USER_AGENT})
    data = {"password": password, "redirect": "index"}

    for p in LOGIN_ENDPOINTS:
        url = norm_url(base_url, p)
        try:
            print(f"[*] Trying login POST -> {url}")
            r = session.post(url, data=data, allow_redirects=True, timeout=10)
        except Exception as e:  # noqa: BLE001
            print(f"[!] Error connecting to {url}: {e}")
            continue

        # If server set a session cookie and didn't return the login page, it's probably success.
        # Heuristics: status_code 200/302 + response not containing "login" form
        if r.status_code in (200, 302):
            # If redirected to index or config, success
            final_url = r.url
            text = r.text.lower() if r.text else ""
            if (
                "login" not in final_url and "login" not in text
            ) or r.status_code == 302:
                print(
                    f"[+] Login likely successful via {url} (status {r.status_code}, final {final_url})"
                )
                return True
            # otherwise maybe failed login - check for "wrongpass" indicator from Login.pm: template renders wrongpass => 1
            if "wrongpass" in text or "failed login" in text or "incorrect" in text:
                print(f"[-] Login failed at {url} (bad password).")
                return False
            # If it's ambiguous, check cookies presence (Mojolicious session cookie name is usually 'mojolicious' or starts with 'mojolicious-')
            if session.cookies:
                print(f"[+] Cookies set after POST to {url}, assuming login succeeded.")
                return True

        # other status codes: continue trying other endpoints
        print(
            f"[-] POST to {url} returned {r.status_code}, trying next login endpoint..."
        )

    print("[!] All login endpoints tried and none confirmed success.")
    return False


def fetch_config_form(session: requests.Session, base_url: str):
    # Try several possible GET endpoints for config and return (url, soup) on success
    for p in CONFIG_GET_ENDPOINTS:
        url = norm_url(base_url, p)
        try:
            print(f"[*] GET {url}")
            r = session.get(url, allow_redirects=True, timeout=10)
        except Exception as e:  # noqa: BLE001
            print(f"[!] Error connecting to {url}: {e}")
            continue

        # If we are redirected to login page, it means not authenticated
        if "/login" in r.url and r.status_code == 200:
            print(f"[-] GET {url} redirected to login; need to authenticate first.")
            return None, r

        # Basic check: page contains a <form> with inputs
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form")
        if form:
            print(f"[+] Found config form at {r.url}")
            return form, r
        else:
            print(f"[-] No form found at {url} (status {r.status_code}), trying next.")
    return None, None


def form_to_dict(form):
    """
    Parse a BeautifulSoup form element into a dict suitable for form POST.
    - includes inputs (text/hidden/password), selects (current option), textareas.
    - For checkboxes/radios: include only those that are checked.
    """
    data = {}

    # inputs
    for inp in form.find_all("input"):
        name = inp.get("name")
        if not name:
            continue
        itype = (inp.get("type") or "text").lower()
        if itype in ("submit", "button", "image"):
            continue
        if itype in ("checkbox", "radio"):
            # include only if checked; if 'checked' attribute exists
            if inp.has_attr("checked") or inp.get("value") in ("1", "on"):
                # ensure some value present; default '1'
                data[name] = inp.get("value", "1")
            else:
                # do not include unchecked boxes (controller treats absence as 0)
                pass
        else:
            data[name] = inp.get("value", "")

    # textareas
    for ta in form.find_all("textarea"):
        name = ta.get("name")
        if not name:
            continue
        data[name] = ta.string if ta.string is not None else ta.get_text("")

    # selects: take selected option, or first option
    for sel in form.find_all("select"):
        name = sel.get("name")
        if not name:
            continue
        option = sel.find("option", selected=True)
        if not option:
            option = sel.find("option")
        data[name] = option.get("value", "") if option else ""

    return data


def set_custom_config(data: dict) -> dict:
    data["nofunmode"] = "1"
    data["apikey"] = "123456"

    return data


def try_post_config(
    session: requests.Session, base_url, form, response_obj, data_override=None
):
    """
    Attempt to POST to the most likely config endpoints. If the original form has an action, prefer that.
    form: BeautifulSoup form or None
    response_obj: the GET response (to extract form action base)
    data_override: dict to POST instead of parsing form
    """

    # If data_override provided, use it; otherwise parse form
    if data_override is not None:
        form_data = dict(data_override)
    else:
        form_data = form_to_dict(form)

    # Keep form hidden fields like CSRF tokens already present in form_data
    for p in CONFIG_POST_ENDPOINTS:
        url = norm_url(base_url, p)
        try:
            print(f"[*] POST to {url} ...")
            r = session.post(url, data=form_data, allow_redirects=True, timeout=15)
        except Exception as e:  # noqa: BLE001
            print(f"[!] Error posting to {url}: {e}")
            continue

        # If server returns JSON with operation/success, attempt to parse it
        ctype = r.headers.get("Content-Type", "")
        if "application/json" in ctype or r.text.strip().startswith("{"):
            try:
                obj = r.json()
                print(f"[+] Response JSON: {json.dumps(obj)}")
                # Config.pm returns {"operation":"config","success":1,...}
                if isinstance(obj, dict) and obj.get("operation") == "config":
                    return obj
            except Exception:  # noqa: S110, BLE001
                pass

        # If a redirect or a success page returned, heuristics:
        if r.status_code in (200, 302):
            text = r.text.lower() if r.text else ""
            if "success" in text or ("operation" in text and "config" in text):
                print(f"[+] POST to {url} seems successful (status {r.status_code}).")
                # Try to parse JSON if present
                try:
                    return r.json()
                except Exception:  # noqa: BLE001
                    return {
                        "operation": "config",
                        "success": 1,
                        "message": "OK (no JSON)",
                    }

        print(
            f"[-] POST to {url} returned status {r.status_code}. Response length {len(r.text)}. Trying next."
        )

    return None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Apply custom config to LANraragi via web UI endpoints."
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL of LANraragi, e.g. http://localhost:3000",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--lrr-container-name",
        required=True,
        help="Name of the running LANraragi container",
    )
    args = parser.parse_args()
    return args


def main(args):
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})

    # 1) Try login if password provided
    logged_in = try_login(s, args.base_url, "kamimamita")
    if not logged_in:
        print("[!] Could not log in. Aborting.")
        sys.exit(1)

    # 2) GET config page and parse form
    form, get_response = fetch_config_form(s, args.base_url)
    if form is None:
        if get_response is not None and "/login" in get_response.url:
            print(
                "[!] Still redirected to login. Check password or whether server requires other auth. Aborting."
            )
            sys.exit(1)
        print(
            "[!] Could not find config page/form. Trying to POST even without form..."
        )
        # fallthrough to try posting without parsing form
    else:
        if args.verbose:
            print("[*] Parsed form inputs (sample):")
            data = form_to_dict(form)
            for k in sorted(data.keys())[:20]:
                print(f"   {k} = {data[k]}")

    # 3) Prepare data: parse existing or start from empty then set values
    if form is not None:
        base_data = form_to_dict(form)
    else:
        base_data = {}

    data_to_post = set_custom_config(base_data)

    # 4) POST config
    result = try_post_config(
        s, args.base_url, form, get_response, data_override=data_to_post
    )
    if result is None:
        print(
            "[!] Failed to POST config or got no usable response. Inspect server logs or try endpoints manually."
        )
        sys.exit(2)

    # 5) Report result
    if isinstance(result, dict):
        success = result.get("success")
        message = result.get("message", "")
        print(f"[+] Server responded: success={success}, message={message}")
        if success:
            print("[+] Configuration updated.")
        else:
            print("[-] Server reported failure.")
            sys.exit(3)
    else:
        print("[+] Unknown response type; output:")
        print(result)
        sys.exit(0)


if __name__ == "__main__":
    args = parse_args()
    wait_for_healthy(args.lrr_container_name, timeout=180)
    print("[+] pre main: lrr container is healthy")
    main(args)
    restart(args.lrr_container_name)
    print("[+] post main: lrr container restarted")
    wait_for_healthy(args.lrr_container_name, timeout=180)
    print("[+] post main: lrr container is healthy")
