# media-inspector

A small FastAPI application that reports image metadata for JPEG and PNG uploads.

## Development

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --locked
uv run fastapi dev
```

## API

- `GET /health` returns `{"status": "ok"}`.
- `POST /analyze` accepts a multipart upload under the `file` field and returns
  `format`, `width`, `height`, `size_bytes`, `mode`, and `processing_ms`.

```sh
curl -F "file=@image.png" http://127.0.0.1:8000/analyze
```

## Docker

```sh
docker build -t media-inspector .
docker run --rm -p 8080:8080 media-inspector
```
