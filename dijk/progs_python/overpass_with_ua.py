"""Utilities for querying the Overpass API with a compliant HTTP User-Agent.

overpy's :class:`overpy.Overpass` uses :func:`urllib.request.urlopen` directly,
which does not expose a header-injection hook.  This module provides
:class:`OverpassWithUA`, a subclass that rebuilds the query method around
:class:`urllib.request.Request` so a descriptive ``User-Agent`` header is sent
on every call — satisfying the Overpass API fair-use policy for scripts.
"""


# ---------------------------------------------------------------------------
# Protocol — describes the subset of urllib response attributes we access.
# Both urllib.response.addinfourl and urllib.error.HTTPError satisfy this at
# runtime; the Protocol lets mypy reason about them without stubs.
#
# HTTPError.code is typed as int (never None); addinfourl.code can be None,
# but in practice urlopen only returns a response after a 200, so code is
# always set.  We type code as int here and cast the urlopen return value so
# both sides of the try/except share the same _HTTPResponse type.
# ---------------------------------------------------------------------------

from __future__ import annotations

import time
import urllib.error
import urllib.request
import typing

import overpy
import overpy.exception


class _HTTPResponse(typing.Protocol):
    """Structural type for urllib success / error responses."""

    code: int

    def read(self, amt: int = ...) -> bytes: ...

    def close(self) -> None: ...

    def getheader(self, name: str, default: typing.Optional[str] = None) -> typing.Optional[str]: ...


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class OverpassWithUA(overpy.Overpass):  # type: ignore[misc]  # overpy ships no stubs
    """Drop-in replacement for :class:`overpy.Overpass` that sends a custom
    ``User-Agent`` header required by the Overpass API fair-use policy.

    Parameters
    ----------
    user_agent:
        A descriptive string identifying your script and a contact point.
    **kwargs:
        Forwarded verbatim to :class:`overpy.Overpass` (``url``,
        ``read_chunk_size``, ``max_retry_count``, ``retry_timeout``, …).
    """

    def __init__(self, user_agent: str, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore
        self.user_agent: str = user_agent

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_request(self, query: bytes) -> urllib.request.Request:
        """Return a :class:`~urllib.request.Request` with the custom UA set."""
        return urllib.request.Request(
            self.url,
            data=query,
            headers={"User-Agent": self.user_agent},
        )

    def _read_response(self, f: _HTTPResponse) -> bytes:
        """Read the full response body in chunks."""
        response: bytes = f.read(self.read_chunk_size)
        while True:
            chunk: bytes = f.read(self.read_chunk_size)
            if not chunk:
                break
            response += chunk
        return response

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(self, query: typing.Union[bytes, str]) -> overpy.Result:
        """Send *query* to the Overpass API and return the parsed result.

        Mirrors the retry / error-handling logic of the upstream
        :meth:`overpy.Overpass.query` while injecting a custom
        ``User-Agent`` header on every request.

        Parameters
        ----------
        query:
            An Overpass QL query string (``str`` or ``bytes``).

        Returns
        -------
        overpy.Result
            The parsed API response.

        Raises
        ------
        overpy.exception.OverpassBadRequest
            The server rejected the query (HTTP 400).
        overpy.exception.OverpassTooManyRequests
            Rate-limit hit (HTTP 429).
        overpy.exception.OverpassGatewayTimeout
            Server timed out (HTTP 504).
        overpy.exception.OverpassUnknownHTTPStatusCode
            Any other non-200 status code.
        overpy.exception.OverpassUnknownContentType
            200 response with an unrecognised ``Content-Type``.
        overpy.exception.MaxRetriesReached
            All retry attempts exhausted (only when ``max_retry_count > 0``).
        """
        if not isinstance(query, bytes):
            query = query.encode("utf-8")

        retry_num: int = 0
        do_retry: bool = self.max_retry_count > 0
        retry_exceptions: list[overpy.exception.OverPyException] = []

        while retry_num <= self.max_retry_count:
            if retry_num > 0:
                time.sleep(self.retry_timeout)
            retry_num += 1

            req = self._build_request(query)
            f: _HTTPResponse
            try:
                # urlopen returns addinfourl; cast so mypy sees _HTTPResponse
                f = typing.cast(_HTTPResponse, urllib.request.urlopen(req))
            except urllib.error.HTTPError as exc:
                f = exc

            response: bytes = self._read_response(f)
            f.close()

            current_exc: overpy.exception.OverPyException

            if f.code == 200:
                content_type: typing.Optional[str] = f.getheader("Content-Type")
                if content_type == "application/json":
                    return self.parse_json(response)
                if content_type == "application/osm3s+xml":
                    return self.parse_xml(response)
                current_exc = overpy.exception.OverpassUnknownContentType(content_type)
                if not do_retry:
                    raise current_exc
                retry_exceptions.append(current_exc)
                continue

            if f.code == 400:
                msgs: list[str] = []
                for match in self._regex_extract_error_msg.finditer(response):
                    raw: bytes = self._regex_remove_tag.sub(b"", match.group("msg"))
                    try:
                        msgs.append(raw.decode("utf-8"))
                    except UnicodeDecodeError:
                        msgs.append(repr(raw))
                current_exc = overpy.exception.OverpassBadRequest(query, msgs=msgs)
                if not do_retry:
                    raise current_exc
                retry_exceptions.append(current_exc)
                continue

            if f.code == 429:
                current_exc = overpy.exception.OverpassTooManyRequests()
                if not do_retry:
                    raise current_exc
                retry_exceptions.append(current_exc)
                continue

            if f.code == 504:
                current_exc = overpy.exception.OverpassGatewayTimeout()
                if not do_retry:
                    raise current_exc
                retry_exceptions.append(current_exc)
                continue

            current_exc = overpy.exception.OverpassUnknownHTTPStatusCode(f.code)
            if not do_retry:
                raise current_exc
            retry_exceptions.append(current_exc)

        raise overpy.exception.MaxRetriesReached(
            retry_count=retry_num,
            exceptions=retry_exceptions,
        )
