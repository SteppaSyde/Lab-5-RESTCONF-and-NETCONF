import json
import sys

import requests

from lab5_utils import RAW_DIR, configure_logging, get_credentials, get_port


TIMEOUT_SECONDS = 10
HEADERS = {"Accept": "application/yang-data+json"}
ENDPOINTS = (
    ("hostname", "Cisco-IOS-XE-native:native/hostname", "restconf_hostname.json"),
    ("interfaces", "ietf-interfaces:interfaces", "restconf_interfaces.json"),
)


def main() -> int:
    logger = configure_logging()
    try:
        host, username, password = get_credentials()
        port = get_port("DEVICE_RESTCONF_PORT", 443)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    base_url = f"https://{host}:{port}/restconf/data"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    connected = False
    failures = 0

    with requests.Session() as session:
        for endpoint_name, resource_path, filename in ENDPOINTS:
            url = f"{base_url}/{resource_path}"
            try:
                response = session.get(
                    url,
                    auth=(username, password),
                    headers=HEADERS,
                    timeout=TIMEOUT_SECONDS,
                    verify=False,
                )
                response.raise_for_status()
                _ = response.json()
            except (requests.RequestException, ValueError) as exc:
                logger.info(f"RESTCONF_REQ_FAIL:{endpoint_name}")
                print(
                    f"RESTCONF request {endpoint_name!r} failed: {exc}",
                    file=sys.stderr,
                )
                failures += 1
                continue

            if not connected:
                logger.info("CONNECT_OK: RESTCONF")
                connected = True
            logger.info(f"RESTCONF_REQ_OK:{endpoint_name}")

            try:
                output_path = RAW_DIR / filename
                output_path.write_text(response.text, encoding="utf-8")
            except OSError as exc:
                print(f"Could not save {filename}: {exc}", file=sys.stderr)
                failures += 1
                continue

            logger.info(f"RAW_SAVED={filename}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
