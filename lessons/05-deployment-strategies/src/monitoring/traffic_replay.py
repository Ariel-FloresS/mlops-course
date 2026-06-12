import http.client
import json
import sys
from pathlib import Path

import pandas as pd

DEFAULT_TRAFFIC_CSV_PATH = Path("data/traffic_baseline.csv")
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
INVALID_REQUEST_INTERVAL = 25


def build_request_body(row: dict) -> dict:
    return {
        "tenure_months": int(row["tenure_months"]),
        "monthly_charges": float(row["monthly_charges"]),
        "total_charges": float(row["total_charges"]),
        "contract_type": str(row["contract_type"]),
        "payment_method": str(row["payment_method"]),
        "support_tickets": int(row["support_tickets"]),
    }


def send_predict_request(connection: http.client.HTTPConnection, body: dict) -> int:
    connection.request(
        "POST",
        "/predict",
        body=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    response.read()
    return response.status


def replay_traffic(traffic_csv_path: Path, server_host: str, server_port: int) -> None:
    if not traffic_csv_path.exists():
        raise ValueError(f"traffic file not found at {traffic_csv_path}")
    frame = pd.read_csv(traffic_csv_path)
    if frame.empty:
        raise ValueError(f"traffic file at {traffic_csv_path} is empty")
    connection = http.client.HTTPConnection(server_host, server_port)
    accepted_count = 0
    rejected_count = 0
    for row_index, row in enumerate(frame.to_dict(orient="records")):
        body = build_request_body(row)
        if (row_index + 1) % INVALID_REQUEST_INTERVAL == 0:
            body = body | {"contract_type": "invalid_plan"}
        status = send_predict_request(connection, body)
        if status == 200:
            accepted_count += 1
        elif status == 422:
            rejected_count += 1
        else:
            raise ValueError(f"unexpected status {status} for request {row_index + 1}")
    connection.close()
    print(f"sent {len(frame)} requests: {accepted_count} accepted, {rejected_count} rejected")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        replay_traffic(DEFAULT_TRAFFIC_CSV_PATH, SERVER_HOST, SERVER_PORT)
    elif len(sys.argv) == 2:
        replay_traffic(Path(sys.argv[1]), SERVER_HOST, SERVER_PORT)
    else:
        raise ValueError(
            "usage: uv run python -m src.monitoring.traffic_replay [<traffic_csv_path>]"
        )
