# MCLabs Wiki GPT

##### 🚧 Work in Progress: This project is currently under active development!

Welcome to the [MCLabs](https://labs-mc.com/) (often shortened to MCL) Wiki GPT!

This tool will implement RAG (Retrieval-Augmented Generation) to support prompting a GPT with specific context relative to our minecraft server from the community wiki. It will then offer an API for using the system via HTTP requests.

## Features

* Fetches and chunks [MediaWiki](https://www.mediawiki.org/wiki/API) articles automatically
* Embeds content using [Google Gemini embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
* Stores vectors in a [FAISS index](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes) for fast similarity search
* Lightweight [Flask API](https://flask.palletsprojects.com/en/stable/) served with [Gunicorn](https://gunicorn.org/) for production-ready handling of RAG queries
* Rate-limited API calls to handle [Google Gemini API restrictions](https://ai.google.dev/gemini-api/docs/rate-limits)
* Uses [Google Gemini&#39;s 2.5 Flash Lite](https://ai.google.dev/gemini-api/docs/models) as the generative language model

## Deployment

This project is currently deployed using [Railway](https://railway.com/) with the entire GitHub Repo.
