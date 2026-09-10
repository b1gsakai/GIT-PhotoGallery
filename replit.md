# Project setup

This is a dependency-free vanilla HTML/CSS/JavaScript website with a small Python standard-library server for the secure Groq description endpoint. There is no frontend framework, build step, or package installation required.

## Run locally

Serve the project directory on port 5000:

```bash
python3 server.py
```

The server reads `GROQ_API_KEY` from Replit Secrets. The key stays server-side and is never sent to the browser.