from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stdout)


def log_event(event: str, **fields: Any) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    logging.getLogger("vibefinder").info(json.dumps(payload, ensure_ascii=False))

