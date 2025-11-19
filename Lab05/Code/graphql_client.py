import time
from dataclasses import dataclass
from typing import Dict, Optional, Any

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


@dataclass
class GraphQLResult:
    name: str
    url: str
    status_code: int
    latency_ms: float
    payload_bytes: int
    timestamp_start: float
    timestamp_end: float
    error: Optional[str] = None


class GraphQLClient:
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10):
        transport = RequestsHTTPTransport(url=url, headers=headers or {}, timeout=timeout, verify=True)
        self.client = Client(transport=transport, fetch_schema_from_transport=False)
        self.url = url

    def execute(self, name: str, query: str, variables: Optional[Dict[str, Any]] = None) -> GraphQLResult:
        t0 = time.perf_counter()
        timestamp_start = time.time()
        try:
            doc = gql(query)
            data = self.client.execute(doc, variable_values=variables)
            payload_bytes = len(str(data).encode('utf-8'))
            status_code = 200
            error = None
        except Exception as exc:
            timestamp_end = time.time()
            t1 = time.perf_counter()
            return GraphQLResult(
                name=name,
                url=self.url,
                status_code=-1,
                latency_ms=(t1 - t0) * 1000.0,
                payload_bytes=0,
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                error=str(exc)
            )
        timestamp_end = time.time()
        t1 = time.perf_counter()
        return GraphQLResult(
            name=name,
            url=self.url,
            status_code=status_code,
            latency_ms=(t1 - t0) * 1000.0,
            payload_bytes=payload_bytes,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            error=error,
        )
