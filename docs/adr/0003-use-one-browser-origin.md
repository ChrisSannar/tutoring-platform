# Use one origin for the browser and API

The browser calls relative `/api/*` paths on the same origin that serves the frontend.
Vite proxies those paths to FastAPI during local development and E2E, while FastAPI
does not enable CORS. This keeps deployment and the future secure-cookie model simple
and avoids an unnecessary cross-origin trust boundary.
