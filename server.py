import base64
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


ROOT = Path(__file__).resolve().parent
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_IMAGE_BYTES = 6 * 1024 * 1024


def json_response(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_limited(response):
    chunks = []
    size = 0
    while True:
        chunk = response.read(min(64 * 1024, MAX_IMAGE_BYTES - size + 1))
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_IMAGE_BYTES:
            raise ValueError("The image is larger than the 6 MB limit.")
        chunks.append(chunk)
    return b"".join(chunks)


def image_data_url(image_url):
    parsed = urlparse(image_url)
    if parsed.scheme in ("http", "https"):
        request = Request(
            image_url,
            headers={"User-Agent": "VanillaGallery/1.0"},
        )
        with urlopen(request, timeout=15) as response:
            content_type = response.headers.get_content_type()
            if not content_type.startswith("image/"):
                raise ValueError("The image URL did not return an image.")
            content = read_limited(response)
    elif parsed.scheme == "" and image_url.startswith("/"):
        relative_path = unquote(parsed.path.lstrip("/"))
        local_path = (ROOT / relative_path).resolve()
        if ROOT not in local_path.parents:
            raise ValueError("Invalid local image path.")
        if not local_path.is_file():
            raise ValueError("The local image could not be found.")
        content = local_path.read_bytes()
        if len(content) > MAX_IMAGE_BYTES:
            raise ValueError("The image is larger than the 6 MB limit.")
        content_type = mimetypes.guess_type(local_path.name)[0] or "application/octet-stream"
    else:
        raise ValueError("Use an http, https, or local image URL.")

    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def describe_image(image_url, title):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    prompt = (
        "Describe this image for a photo gallery in 2 or 3 clear sentences. "
        "Be factual and describe only what is visibly present. Do not guess a "
        "person's identity, exact location, date, or unseen context. Do not "
        "mention that you are an AI. The gallery title is: "
        f"{title or 'Untitled image'}."
    )
    payload = {
        "model": os.environ.get("GROQ_MODEL", DEFAULT_MODEL),
        "temperature": 0.2,
        "max_completion_tokens": 180,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url(image_url)},
                    },
                ],
            }
        ],
    }
    request = Request(
        GROQ_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        if hasattr(error, "read"):
            try:
                details = json.loads(error.read().decode("utf-8"))
                message = details.get("error", {}).get("message")
                if message:
                    raise RuntimeError(message) from error
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        raise RuntimeError("Groq could not generate a description.") from error

    try:
        description = result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError) as error:
        raise RuntimeError("Groq returned an unexpected response.") from error
    if not description:
        raise RuntimeError("Groq returned an empty description.")
    return description


class GalleryHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/describe":
            json_response(self, 404, {"error": "Not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length > 20_000:
                raise ValueError("Request is too large.")
            request_body = json.loads(self.rfile.read(content_length).decode("utf-8"))
            image_url = request_body.get("imageUrl", "")
            title = request_body.get("title", "")
            if not isinstance(image_url, str) or not image_url:
                raise ValueError("An image URL is required.")
            if not isinstance(title, str):
                title = ""
            description = describe_image(image_url, title[:120])
            json_response(self, 200, {"description": description})
        except (ValueError, json.JSONDecodeError) as error:
            json_response(self, 400, {"error": str(error)})
        except RuntimeError as error:
            json_response(self, 502, {"error": str(error)})
        except Exception:
            json_response(self, 500, {"error": "Unable to generate a description."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), GalleryHandler)
    print(f"Serving vanilla gallery on http://0.0.0.0:{port}/")
    server.serve_forever()