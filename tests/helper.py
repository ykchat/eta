import io
import zipfile

import httpx

def mock(status: int = 200, body: object = None, urls: list[httpx.URL] | None = None) -> httpx.MockTransport:

    def respond(request: httpx.Request) -> httpx.Response:
        if urls is not None:
            urls.append(request.url)
        if isinstance(body, bytes):
            return httpx.Response(status, content=body)
        return httpx.Response(status, json=body)

    return httpx.MockTransport(respond)

def make_zip(files: dict[str, str]) -> bytes:

    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as zip_file:
        for name, text in files.items():
            zip_file.writestr(name, text)

    return content.getvalue()