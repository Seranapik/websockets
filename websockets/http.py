"""
HTTP parsing utilities, adequate for the WebSocket handshake.
"""

import email.parser
import io

import tulip


MAX_HEADERS = 256
MAX_LINE = 4096


@tulip.coroutine
def read_request(stream):
    """
    Read an HTTP/1.1 request that doesn't have a body from `stream`.

    Return `(uri, headers)` where `uri` is a `str` and `headers` an
    `email.message.Message`.

    `uri` is transmitted as-is; it isn't URL-decoded.
    """
    request_line, headers = yield from read_message(stream)
    method, uri, version = request_line[:-2].decode().split(None, 2)
    if method != 'GET':
        raise ValueError("Unsupported method")
    if version != 'HTTP/1.1':
        raise ValueError("Unsupported HTTP version")
    return uri, headers


@tulip.coroutine
def read_response(stream):
    """
    Read an HTTP/1.1 response that doesn't have a body from `stream`.

    Return `(status, headers)` where `status` is an `int` and `headers` an
    `email.message.Message`.
    """
    status_line, headers = yield from read_message(stream)
    version, status, reason = status_line[:-2].decode().split(None, 2)
    if version != 'HTTP/1.1':
        raise ValueError("Unsupported HTTP version")
    return int(status), headers


@tulip.coroutine
def read_message(stream):
    """
    Read an HTTP message that doesn't have a body from `stream`.

    Return `(start line, headers)` where `start_line` is `bytes` and `headers`
    an `email.message.Message`.
    """
    start_line = yield from read_line(stream)
    header_lines = io.BytesIO()
    for num in range(MAX_HEADERS):
        header_line = yield from read_line(stream)
        header_lines.write(header_line)
        if header_line == b'\r\n':
            break
    else:
        raise ValueError("Too many headers")
    header_lines.seek(0)
    headers = email.parser.BytesHeaderParser().parse(header_lines)
    return start_line, headers


@tulip.coroutine
def read_line(stream):
    """
    Read a single line from `stream`.
    """
    line = yield from stream.readline()
    if len(line) > MAX_LINE:
        raise ValueError("Line too long")
    if not line.endswith(b'\r\n'):
        raise ValueError("Line without CRLF")
    return line
