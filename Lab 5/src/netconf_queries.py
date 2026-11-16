import sys

from ncclient import NCClientError, manager

from lab5_utils import RAW_DIR, configure_logging, get_credentials, get_port


TIMEOUT_SECONDS = 10
SYSTEM_FILTER = """\
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <hostname/>
    <version/>
  </native>
</filter>"""
INTERFACES_FILTER = """\
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name/>
      <type/>
      <enabled/>
    </interface>
  </interfaces>
</filter>"""


def main() -> int:
    logger = configure_logging()
    try:
        host, username, password = get_credentials()
        port = get_port("DEVICE_NETCONF_PORT", 830)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    try:
        connection = manager.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            hostkey_verify=False,
            timeout=TIMEOUT_SECONDS,
        )
    except (NCClientError, OSError) as exc:
        print(f"NETCONF connection failed: {exc}", file=sys.stderr)
        return 1

    logger.info("CONNECT_OK: NETCONF")
    failures = 0
    requests_to_run = (
        ("system", lambda: connection.get_config(source="running", filter=SYSTEM_FILTER),
         "netconf_system.xml"),
        ("interfaces", lambda: connection.get(filter=INTERFACES_FILTER),
         "netconf_interfaces.xml"),
    )

    try:
        for rpc_name, rpc_call, filename in requests_to_run:
            try:
                result = rpc_call()
            except (NCClientError, OSError) as exc:
                logger.info(f"NETCONF_RPC_FAIL:{rpc_name}")
                print(f"NETCONF RPC {rpc_name!r} failed: {exc}", file=sys.stderr)
                failures += 1
                continue

            logger.info(f"NETCONF_RPC_OK:{rpc_name}")
            try:
                output_path = RAW_DIR / filename
                output_path.write_text(result.xml, encoding="utf-8")
            except OSError as exc:
                print(f"Could not save {filename}: {exc}", file=sys.stderr)
                failures += 1
                continue

            logger.info(f"RAW_SAVED={filename}")
    finally:
        try:
            connection.close_session()
        except (NCClientError, OSError) as exc:
            print(f"Could not close the NETCONF session cleanly: {exc}", file=sys.stderr)
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
