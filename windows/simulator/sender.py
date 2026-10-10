from datetime import datetime, timezone
from urllib import request, error
import json
import time
import uuid

KALI_IP = "172.16.204.130"
PORT = 8001

SERVER_URL = (
    f"http://{KALI_IP}:{PORT}/events"
)

TIMEOUT_SECONDS = 3
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def build_event(
    run_id,
    sequence,
    module,
    state,
    summary
):
    return {
        "schema_version": 1,
        "run_id": run_id,
        "sequence": sequence,
        "module": module,
        "state": state,
        "timestamp_utc": utc_now(),
        "summary": summary
    }


def send_event(event):
    body = json.dumps(
        event
    ).encode("utf-8")

    req = request.Request(
        SERVER_URL,
        data=body,
        method="POST"
    )

    req.add_header(
        "Content-Type",
        "application/json"
    )

    req.add_header(
        "Content-Length",
        str(len(body))
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):
        try:
            with request.urlopen(
                req,
                timeout=TIMEOUT_SECONDS
            ) as response:

                response_body = (
                    response.read()
                    .decode("utf-8")
                )

                result = json.loads(
                    response_body
                )

                print(
                    f"Attempt {attempt}: "
                    f"HTTP {response.status}"
                )

                print(
                    "Server response:",
                    result
                )

                return True

        except error.HTTPError as http_error:
            print(
                f"Attempt {attempt}: "
                f"HTTP error "
                f"{http_error.code}"
            )

            try:
                body = (
                    http_error.read()
                    .decode("utf-8")
                )

                print(
                    "Server response:",
                    body
                )

            except Exception:
                pass

            return False

        except (
            error.URLError,
            TimeoutError,
            OSError
        ) as network_error:

            print(
                f"Attempt {attempt}: "
                f"connection failed - "
                f"{network_error}"
            )

            if attempt < MAX_RETRIES:
                print(
                    f"Retrying in "
                    f"{RETRY_DELAY_SECONDS} "
                    f"second(s)..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

    print(
        "Event could not be delivered "
        "after all retry attempts."
    )

    return False


def send_single_test():
    run_id = str(
        uuid.uuid4()
    )

    event = build_event(
        run_id=run_id,
        sequence=1,
        module="m5_test",
        state="completed",
        summary=(
            "Single synthetic M5 "
            "communication test."
        )
    )

    print()
    print(
        "Sending single test event..."
    )

    print(
        f"Run ID: {run_id}"
    )

    send_event(event)


def send_duplicate_test():
    run_id = str(
        uuid.uuid4()
    )

    event = build_event(
        run_id=run_id,
        sequence=1,
        module="duplicate_test",
        state="completed",
        summary=(
            "Synthetic duplicate "
            "detection test."
        )
    )

    print()
    print(
        "Sending original event..."
    )

    send_event(event)

    print()
    print(
        "Sending same event again..."
    )

    send_event(event)


def send_heartbeat_test():
    run_id = str(
        uuid.uuid4()
    )

    heartbeat_count = 5
    interval_seconds = 2

    print()
    print(
        "Starting finite heartbeat test."
    )

    print(
        f"Run ID: {run_id}"
    )

    print(
        f"Heartbeats: {heartbeat_count}"
    )

    print(
        f"Interval: "
        f"{interval_seconds} seconds"
    )

    for sequence in range(
        1,
        heartbeat_count + 1
    ):
        event = build_event(
            run_id=run_id,
            sequence=sequence,
            module="heartbeat",
            state="heartbeat",
            summary=(
                f"Synthetic heartbeat "
                f"{sequence} of "
                f"{heartbeat_count}."
            )
        )

        print()
        print(
            f"Sending heartbeat "
            f"{sequence}/"
            f"{heartbeat_count}"
        )

        success = send_event(
            event
        )

        if not success:
            print(
                "Heartbeat delivery "
                "failed."
            )

        if sequence < heartbeat_count:
            time.sleep(
                interval_seconds
            )

    print()
    print(
        "Heartbeat test finished."
    )


def show_configuration():
    print()
    print(
        "=== Sender Configuration ==="
    )

    print(
        f"Kali IP: {KALI_IP}"
    )

    print(
        f"Port: {PORT}"
    )

    print(
        f"Endpoint: {SERVER_URL}"
    )

    print(
        f"Timeout: "
        f"{TIMEOUT_SECONDS} seconds"
    )

    print(
        f"Maximum retries: "
        f"{MAX_RETRIES}"
    )


def main():
    while True:
        print()
        print(
            "=== M5 Windows Event Sender ==="
        )

        print()
        print(
            "1. Send single test event"
        )

        print(
            "2. Send duplicate test"
        )

        print(
            "3. Send heartbeat test"
        )

        print(
            "4. Show configuration"
        )

        print(
            "0. Exit"
        )

        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":
            send_single_test()

        elif choice == "2":
            send_duplicate_test()

        elif choice == "3":
            send_heartbeat_test()

        elif choice == "4":
            show_configuration()

        elif choice == "0":
            print()
            print(
                "Exiting sender."
            )
            break

        else:
            print()
            print(
                "Invalid option."
            )


if __name__ == "__main__":
    main()