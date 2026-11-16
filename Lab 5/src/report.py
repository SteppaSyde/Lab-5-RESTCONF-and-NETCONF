import json
import sys
from xml.parsers.expat import ExpatError

import xmltodict

from lab5_utils import RAW_DIR, REPORT_DIR, configure_logging


MISSING = object()


def normalized_key(key: str) -> str:
    return key.rsplit(":", 1)[-1].lstrip("@").lower().replace("_", "-")


def find_value(data: object, aliases: set[str]) -> object:
    if isinstance(data, dict):
        for key, value in data.items():
            if normalized_key(str(key)) in aliases:
                return value
        for value in data.values():
            found = find_value(value, aliases)
            if found is not MISSING:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_value(value, aliases)
            if found is not MISSING:
                return found
    return MISSING


def display(value: object) -> str:
    if value is MISSING or value is None or value == "":
        return "Not returned in the saved response."
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return str(value)


def comparable(value: object) -> str | None:
    if value is MISSING or value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value).strip()


def compare_values(label: str, restconf: object, netconf: object) -> str:
    rest_value = comparable(restconf)
    net_value = comparable(netconf)
    if rest_value is None or net_value is None:
        return f"{label}: comparison unavailable because one response did not include this field."
    if rest_value == net_value:
        return f"{label}: both protocols returned the same value."
    return f"{label}: the responses differ."


def main() -> int:
    logger = configure_logging()
    try:
        restconf_hostname = json.loads(
            (RAW_DIR / "restconf_hostname.json").read_text(encoding="utf-8")
        )
        logger.info("PARSE_JSON_OK:hostname")
        restconf_interfaces = json.loads(
            (RAW_DIR / "restconf_interfaces.json").read_text(encoding="utf-8")
        )
        logger.info("PARSE_JSON_OK:interfaces")
        logger.info("PARSE_JSON_OK")

        netconf_system = xmltodict.parse(
            (RAW_DIR / "netconf_system.xml").read_text(encoding="utf-8")
        )
        logger.info("PARSE_XML_OK:system")
        netconf_interfaces = xmltodict.parse(
            (RAW_DIR / "netconf_interfaces.xml").read_text(encoding="utf-8")
        )
        logger.info("PARSE_XML_OK:interfaces")
        logger.info("PARSE_XML_OK")
    except (OSError, json.JSONDecodeError, ExpatError) as exc:
        print(f"Could not load or parse the collected device data: {exc}", file=sys.stderr)
        return 1

    hostname_keys = {"hostname", "host-name"}
    model_keys = {"model", "platform", "product-id", "product-name", "chassis"}
    version_keys = {"software-version", "ios-version", "version", "image-version"}
    interface_keys = {"interfaces", "interface", "interfaces-state"}

    restconf_values = {
        "hostname": find_value(restconf_hostname, hostname_keys),
        "model": find_value(restconf_hostname, model_keys),
        "version": find_value(restconf_hostname, version_keys),
        "interfaces": find_value(restconf_interfaces, interface_keys),
    }
    netconf_values = {
        "hostname": find_value(netconf_system, hostname_keys),
        "model": find_value(netconf_system, model_keys),
        "version": find_value(netconf_system, version_keys),
        "interfaces": find_value(netconf_interfaces, interface_keys),
    }

    similar = []
    differences = []
    for key in ("hostname", "model", "version", "interfaces"):
        result = compare_values(key.title(), restconf_values[key], netconf_values[key])
        if "same value" in result:
            similar.append(result)
        else:
            differences.append(result)

    report = f"""LAB 5: RESTCONF VS NETCONF REPORT

Device Information
------------------
Hostname:
RESTCONF: {display(restconf_values["hostname"])}
NETCONF: {display(netconf_values["hostname"])}

Platform / Model
----------------
RESTCONF: {display(restconf_values["model"])}
NETCONF: {display(netconf_values["model"])}

Software Version
----------------
RESTCONF: {display(restconf_values["version"])}
NETCONF: {display(netconf_values["version"])}

Interface Information
---------------------
RESTCONF:
{display(restconf_values["interfaces"])}

NETCONF:
{display(netconf_values["interfaces"])}

Comparison
----------
Similarities:
{chr(10).join(f"- {item}" for item in similar) if similar else "- No matching values could be confirmed from the collected data."}

Differences or unavailable comparisons:
{chr(10).join(f"- {item}" for item in differences) if differences else "- No differences were found in the compared fields."}

Conclusion
----------
RESTCONF retrieves device information through HTTP and JSON.
NETCONF retrieves device information through RPCs and XML.
Only information present in the saved device responses is reported.
"""

    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / "lab5_report.txt"
        report_path.write_text(report, encoding="utf-8")
    except OSError as exc:
        print(f"Could not save the report: {exc}", file=sys.stderr)
        return 1

    logger.info("REPORT_SAVED=lab5_report.txt")
    print(f"Report saved to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
