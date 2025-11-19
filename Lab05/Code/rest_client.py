import time
from dataclasses import dataclass
from typing import Dict, Optional, Any

import requests


@dataclass
class RestResult:
    label: str
    url: str
    status_code: int
    latency_ms: float
    payload_bytes: int
    timestamp_start: float
    timestamp_end: float
    error: Optional[str] = None


class RestClient:
    def __init__(self, base_url: str, default_headers: Optional[Dict[str, str]] = None, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.timeout = timeout

    def fetch(self, path: str, label: str, params: Optional[Dict[str, Any]] = None) -> RestResult:
        url = f"{self.base_url}{path}" if path.startswith('/') else f"{self.base_url}/{path}"
        t0 = time.perf_counter()
        timestamp_start = time.time()
        try:
            resp = requests.get(url, headers=self.default_headers, params=params, timeout=self.timeout)
            content = resp.content or b''
            status_code = resp.status_code
            error = None
        except Exception as exc:
            timestamp_end = time.time()
            t1 = time.perf_counter()
            return RestResult(
                label=label,
                url=url,
                status_code=-1,
                latency_ms=(t1 - t0) * 1000.0,
                payload_bytes=0,
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                error=str(exc)
            )
        timestamp_end = time.time()
        t1 = time.perf_counter()
        return RestResult(
            label=label,
            url=url,
            status_code=status_code,
            latency_ms=(t1 - t0) * 1000.0,
            payload_bytes=len(content),
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            error=error,
        )
