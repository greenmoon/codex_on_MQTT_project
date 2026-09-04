#!/usr/bin/env python3
"""Read-only MQTT 3.1.1 logger and local dashboard server (stdlib only)."""
from __future__ import annotations

import argparse
import json
import socket
import struct
import threading
import time
import uuid
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LOCK = threading.Lock()
STATE = {"broker_connected": False, "started_at": datetime.now().astimezone().isoformat(), "projects": {}}


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def write_jsonl(name, record):
    DATA.mkdir(exist_ok=True)
    with (DATA / name).open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def mqtt_text(value):
    raw = value.encode()
    return struct.pack("!H", len(raw)) + raw


def remaining_length(value):
    out = bytearray()
    while True:
        digit = value % 128
        value //= 128
        if value:
            digit |= 128
        out.append(digit)
        if not value:
            return bytes(out)


def packet(kind, body):
    return bytes([kind]) + remaining_length(len(body)) + body


def recv_exact(sock, count):
    out = bytearray()
    while len(out) < count:
        chunk = sock.recv(count - len(out))
        if not chunk:
            raise ConnectionError("broker closed connection")
        out.extend(chunk)
    return bytes(out)


def recv_packet(sock):
    first = recv_exact(sock, 1)[0]
    multiplier = 1
    length = 0
    while True:
        digit = recv_exact(sock, 1)[0]
        length += (digit & 127) * multiplier
        if not digit & 128:
            break
        multiplier *= 128
        if multiplier > 128**3:
            raise ValueError("invalid MQTT remaining length")
    return first, recv_exact(sock, length)


def initial_project(spec):
    return {
        "topic": spec["topic"], "expected_period_s": spec["expected_period_s"],
        "timeout_s": spec["timeout_s"], "frame_key": spec["frame_key"],
        "received": 0, "valid": 0,
        "invalid": 0, "gaps": 0, "last_received": None, "last_epoch": 0,
        "last_frame": None, "frame_delta": None, "interval_ms": None,
        "frame_checks": 0, "frame_advanced": 0, "stalls": 0,
        "rollbacks": 0, "consecutive_stalls": 0, "stall_active": False,
        "last_payload": None, "raw_payload": "等待第一筆真實 MQTT payload",
        "health": 0, "status": "WAITING", "history": [], "events": []
    }


def health(project, current=None):
    current = current or time.time()
    if not project["received"]:
        return 0
    age = current - project["last_epoch"]
    continuity = max(0, 100 - max(0, age - project["expected_period_s"] * 2) * 25)
    validity = project["valid"] / project["received"] * 100
    frame_score = project["frame_advanced"] / project["frame_checks"] * 100 if project["frame_checks"] else 100
    gap_score = max(0, 100 - project["gaps"] * 5 - project["rollbacks"] * 20)
    return round(continuity * .35 + validity * .25 + frame_score * .30 + gap_score * .10)


def record_message(project_name, topic, payload_bytes):
    received_at = now_iso()
    raw = payload_bytes.decode("utf-8", errors="replace")
    try:
        decoded = json.loads(raw)
        valid = isinstance(decoded, dict)
    except json.JSONDecodeError:
        decoded, valid = None, False
    event = None
    with LOCK:
        project = STATE["projects"][project_name]
        current = time.time()
        if project["last_epoch"]:
            delta = current - project["last_epoch"]
            project["interval_ms"] = round(delta * 1000)
            if delta > project["expected_period_s"] * 2.5:
                project["gaps"] += max(1, round(delta / project["expected_period_s"]) - 1)
        frame = decoded.get(project["frame_key"]) if valid else None
        frame_valid = isinstance(frame, int) and not isinstance(frame, bool) and frame >= 0
        valid = valid and frame_valid
        if frame_valid:
            previous = project["last_frame"]
            project["frame_delta"] = None if previous is None else frame - previous
            if previous is not None:
                project["frame_checks"] += 1
                if frame > previous:
                    project["frame_advanced"] += 1
                    project["consecutive_stalls"] = 0
                    project["stall_active"] = False
                elif frame == previous:
                    project["stalls"] += 1
                    project["consecutive_stalls"] += 1
                    if project["consecutive_stalls"] >= 3 and not project["stall_active"]:
                        project["stall_active"] = True
                        event = {"at": received_at, "project": project_name, "type": "frame_stalled",
                                 "severity": "critical", "frame_key": project["frame_key"], "frame": frame}
                else:
                    project["rollbacks"] += 1
                    project["consecutive_stalls"] = 0
                    event = {"at": received_at, "project": project_name, "type": "frame_rollback",
                             "severity": "critical", "frame_key": project["frame_key"],
                             "previous": previous, "frame": frame}
            project["last_frame"] = frame
        project["received"] += 1
        project["valid" if valid else "invalid"] += 1
        project["last_received"], project["last_epoch"] = received_at, current
        project["last_payload"], project["raw_payload"] = decoded, raw
        project["health"] = health(project, current)
        project["status"] = "HEALTHY" if project["health"] >= 90 else "WARNING" if project["health"] >= 75 else "UNHEALTHY"
        project["history"].append({"t": received_at, "health": project["health"],
                                   "frame_delta": project["frame_delta"], "interval_ms": project["interval_ms"]})
        project["history"] = project["history"][-300:]
    record = {"received_at": received_at, "project": project_name, "topic": topic,
              "payload_raw": raw, "payload": decoded, "valid": valid}
    write_jsonl("raw_messages.jsonl", record)
    if not valid and event is None:
        event = {"at": received_at, "project": project_name, "type": "invalid_payload", "severity": "critical", "raw": raw}
    if event:
        write_jsonl("failure_events.jsonl", event)
        with LOCK:
            events = STATE["projects"][project_name]["events"]
            events.append(event)
            del events[:-100]


def mqtt_worker(config):
    topics = {spec["topic"]: name for name, spec in config["projects"].items()}
    while True:
        try:
            with socket.create_connection((config["broker"], config["port"]), timeout=10) as sock:
                sock.settimeout(35)
                client_id = "MQTT-MON-" + uuid.uuid4().hex[:8]
                body = mqtt_text("MQTT") + bytes([4, 2, 0, 30]) + mqtt_text(client_id)
                sock.sendall(packet(0x10, body))
                kind, response = recv_packet(sock)
                if kind != 0x20 or response[-1] != 0:
                    raise ConnectionError("MQTT CONNACK rejected")
                subscribe = struct.pack("!H", 1) + b"".join(mqtt_text(topic) + b"\x00" for topic in topics)
                sock.sendall(packet(0x82, subscribe))
                with LOCK:
                    STATE["broker_connected"] = True
                    STATE["broker_error"] = None
                last_ping = time.time()
                while True:
                    if time.time() - last_ping > 20:
                        sock.sendall(b"\xc0\x00")
                        last_ping = time.time()
                    kind, body = recv_packet(sock)
                    if kind >> 4 == 3:
                        topic_len = struct.unpack("!H", body[:2])[0]
                        topic = body[2:2 + topic_len].decode(errors="replace")
                        offset = 2 + topic_len + (2 if ((kind >> 1) & 3) else 0)
                        if topic in topics:
                            record_message(topics[topic], topic, body[offset:])
        except Exception as exc:
            with LOCK:
                STATE["broker_connected"] = False
                STATE["broker_error"] = str(exc)
            time.sleep(5)


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path == "/api/state":
            with LOCK:
                snapshot = json.loads(json.dumps(STATE))
                current = time.time()
                for project in snapshot["projects"].values():
                    project["age_s"] = round(current - project["last_epoch"], 1) if project["last_epoch"] else None
                    project["health"] = health(project, current)
                    if project["last_epoch"] and project["age_s"] > project["timeout_s"]:
                        project["status"] = "OFFLINE"
            body = json.dumps(snapshot, ensure_ascii=False).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        return super().do_GET()

    def log_message(self, fmt, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    STATE["broker"] = f'{config["broker"]}:{config["port"]}'
    STATE["projects"] = {name: initial_project(spec) for name, spec in config["projects"].items()}
    threading.Thread(target=mqtt_worker, args=(config,), daemon=True).start()
    print(f"MQTT monitor: http://127.0.0.1:{args.port}/index.html", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
