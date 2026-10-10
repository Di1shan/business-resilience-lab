from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from datetime import datetime, timezone
import json

HOST = "0.0.0.0"
PORT = 8001

BASE_DIR = Path(__file__).parent
EVENTS_FILE = BASE_DIR / "events.jsonl"

MAX_REQUEST_BYTES = 4096

REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "sequence",
    "module",
    "state",
    "timestamp_utc",
    "summary"
}

VALID_STATES = {
    "started",
    "running",
    "completed",
    "failed",
    "heartbeat"
}

SEEN_EVENTS = set()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_existing_event_keys():
    if not EVENTS_FILE.exists():
        return

    try:
        with EVENTS_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:
                line = line.strip()

                if not line:
                    continue

                try:
                    event = json.loads(line)

                    key = (
                        str(event.get("run_id")),
                        int(event.get("sequence"))
                    )

                    SEEN_EVENTS.add(key)

                except (
                    json.JSONDecodeError,
                    TypeError,
                    ValueError
                ):
                    continue

    except OSError:
        pass


def validate_event(event):
    if not isinstance(event, dict):
        return False, "JSON body must be an object."

    missing = REQUIRED_FIELDS - event.keys()

    if missing:
        return (
            False,
            "Missing required fields: "
            + ", ".join(sorted(missing))
        )

    if event["schema_version"] != 1:
        return False, "Unsupported schema_version."

    if not isinstance(
        event["run_id"],
        str
    ) or not event["run_id"].strip():
        return False, "run_id must be a non-empty string."

    if not isinstance(
        event["sequence"],
        int
    ) or event["sequence"] < 1:
        return False, "sequence must be a positive integer."

    if not isinstance(
        event["module"],
        str
    ) or not event["module"].strip():
        return False, "module must be a non-empty string."

    if event["state"] not in VALID_STATES:
        return False, "Invalid state value."

    if not isinstance(
        event["timestamp_utc"],
        str
    ) or not event["timestamp_utc"].strip():
        return False, "timestamp_utc must be a non-empty string."

    if not isinstance(
        event["summary"],
        str
    ):
        return False, "summary must be a string."

    if len(event["summary"]) > 500:
        return False, "summary is too long."

    return True, "valid"


def append_event(event):
    with EVENTS_FILE.open(
        "a",
        encoding="utf-8"
    ) as file:
        file.write(
            json.dumps(event)
            + "\n"
        )


class EventHandler(
    BaseHTTPRequestHandler
):
    def send_json_response(
        self,
        status_code,
        payload
    ):
        body = json.dumps(
            payload
        ).encode("utf-8")

        self.send_response(
            status_code
        )

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/events":
            self.send_json_response(
                404,
                {
                    "status": "error",
                    "message": "Unknown endpoint."
                }
            )
            return

        content_length = (
            self.headers.get(
                "Content-Length"
            )
        )

        if content_length is None:
            self.send_json_response(
                411,
                {
                    "status": "error",
                    "message": (
                        "Content-Length required."
                    )
                }
            )
            return

        try:
            content_length = int(
                content_length
            )

        except ValueError:
            self.send_json_response(
                400,
                {
                    "status": "error",
                    "message": (
                        "Invalid Content-Length."
                    )
                }
            )
            return

        if content_length > MAX_REQUEST_BYTES:
            self.send_json_response(
                413,
                {
                    "status": "error",
                    "message": (
                        "Request too large."
                    )
                }
            )
            return

        raw_body = self.rfile.read(
            content_length
        )

        try:
            event = json.loads(
                raw_body.decode("utf-8")
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError
        ):
            self.send_json_response(
                400,
                {
                    "status": "error",
                    "message": (
                        "Malformed JSON."
                    )
                }
            )
            return

        valid, message = validate_event(
            event
        )

        if not valid:
            self.send_json_response(
                400,
                {
                    "status": "error",
                    "message": message
                }
            )
            return

        event_key = (
            event["run_id"],
            event["sequence"]
        )

        if event_key in SEEN_EVENTS:
            self.send_json_response(
                200,
                {
                    "status": "duplicate",
                    "message": (
                        "Event already recorded."
                    )
                }
            )
            return

        event["received_utc"] = utc_now()

        append_event(event)
        SEEN_EVENTS.add(event_key)

        print(
            f"Accepted event: "
            f"{event['run_id']} "
            f"seq={event['sequence']} "
            f"state={event['state']}"
        )

        self.send_json_response(
            200,
            {
                "status": "accepted",
                "message": (
                    "Event recorded."
                )
            }
        )

    def log_message(
        self,
        format,
        *args
    ):
        return


def main():
    BASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    load_existing_event_keys()

    server = HTTPServer(
        (HOST, PORT),
        EventHandler
    )

    print(
        "=== Business Resilience Lab "
        "M5 Receiver ==="
    )

    print(
        f"Listening on port {PORT}"
    )

    print(
        f"Events file: {EVENTS_FILE}"
    )

    print(
        "Endpoint: POST /events"
    )

    print(
        "Press Ctrl+C to stop."
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print()
        print(
            "Receiver stopped."
        )

    finally:
        server.server_close()


if __name__ == "__main__":
    main()
