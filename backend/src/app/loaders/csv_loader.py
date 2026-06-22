from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from dateutil import parser as date_parser

from app.models.ticket import Ticket


def _strip(s: str | None) -> str | None:
    if s is None:
        return None
    t = str(s).strip()
    return t or None


def normalize_priority(raw: str | None) -> str | None:
    if not raw:
        return None
    s = str(raw).strip().lower()
    if s in ("low", "p4", "4", "l"):
        return "low"
    if s in ("medium", "med", "p2", "p3", "2", "3", "mid", "m"):
        return "medium"
    if s in ("high", "p1", "1", "h"):
        return "high"
    if s in ("critical", "urgent", "p0", "0", "crit", "c"):
        return "critical"
    if s.isdigit():
        n = int(s)
        if n <= 1:
            return "high"
        if n == 2:
            return "medium"
        return "low"
    return "medium"


def normalize_status(raw: str | None) -> str | None:
    t = _strip(raw)
    if not t:
        return None
    # Homogeneiza espacios y capitalización simple
    t = re.sub(r"\s+", " ", t)
    return t


def parse_purchase_date(raw: str | None):
    t = _strip(raw)
    if not t:
        return None
    try:
        dt = date_parser.parse(t, dayfirst=True, yearfirst=True)
        return dt.date()
    except (ValueError, TypeError, OverflowError):
        return None


def parse_int_safe(raw: str | None) -> int | None:
    t = _strip(raw)
    if not t:
        return None
    try:
        return int(float(t))
    except ValueError:
        return None


def parse_float_safe(raw: str | None) -> float | None:
    t = _strip(raw)
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def row_to_ticket(row: dict[str, str]) -> Ticket:
    tid = int(row["Ticket ID"])
    email = _strip(row.get("Customer Email"))
    if email is not None:
        email = email.lower()

    return Ticket(
        id=tid,
        customer_name=_strip(row.get("Customer Name")),
        customer_email=email,
        customer_age=parse_int_safe(row.get("Customer Age")),
        customer_gender=_strip(row.get("Customer Gender")),
        product_purchased=_strip(row.get("Product Purchased")),
        date_of_purchase_raw=_strip(row.get("Date of Purchase")),
        purchase_date=parse_purchase_date(row.get("Date of Purchase")),
        ticket_type=_strip(row.get("Ticket Type")),
        ticket_subject=_strip(row.get("Ticket Subject")),
        ticket_description=_strip(row.get("Ticket Description")),
        ticket_status=normalize_status(row.get("Ticket Status")),
        ticket_priority_raw=_strip(row.get("Ticket Priority")),
        priority_normalized=normalize_priority(row.get("Ticket Priority")),
        ticket_channel=_strip(row.get("Ticket Channel")),
        first_response_time_raw=_strip(row.get("First Response Time")),
        time_to_resolution_raw=_strip(row.get("Time to Resolution")),
        customer_satisfaction_rating=parse_float_safe(row.get("Customer Satisfaction Rating")),
    )


def load_tickets_from_fileobj(fileobj: io.TextIOBase) -> list[Ticket]:
    reader = csv.DictReader(fileobj)
    if reader.fieldnames is None or "Ticket ID" not in reader.fieldnames:
        msg = "El CSV debe incluir la columna 'Ticket ID' y cabeceras compatibles con el dataset."
        raise ValueError(msg)
    by_id: dict[int, Ticket] = {}
    for row in reader:
        ticket = row_to_ticket(row)
        by_id[ticket.id] = ticket
    return list(by_id.values())


def load_tickets_from_bytes(data: bytes, encoding: str = "utf-8") -> list[Ticket]:
    try:
        text = data.decode(encoding)
    except UnicodeDecodeError as e:
        msg = "El archivo debe estar codificado en UTF-8."
        raise ValueError(msg) from e
    return load_tickets_from_fileobj(io.StringIO(text))


def load_tickets_from_csv(path: Path) -> list[Ticket]:
    if not path.is_file():
        msg = f"No se encontró el dataset: {path}"
        raise FileNotFoundError(msg)

    with path.open(encoding="utf-8", newline="") as f:
        return load_tickets_from_fileobj(f)
