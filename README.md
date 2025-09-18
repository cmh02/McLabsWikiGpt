# MCLabs Wiki RAG

##### 🚧 Work in Progress: This project is currently under active development!

Welcome to the [MCLabs](https://labs-mc.com/) (often shortened to MCL) Wiki RAG!

This tool will implement RAG (Retrieval-Augmented Generation) to support prompting [Google Gemini ](https://gemini.google.com/app)with specific context relative to our minecraft server from the [community wiki](https://labs-mc.com/wiki/Main_Page). It will then offer an API for using the system via HTTP requests along with two interfaces for our community to interact with.

## Feature Overview

* [Data Collection](#data-collection)
  * Fetches and chunks [MediaWiki](https://www.mediawiki.org/wiki/API) articles automatically
  * Loads dump logs from our [Mongo](https://www.mongodb.com/) database and chunks Q&A pairs
* [Embedding and Indexing](#embedding-and-indexing)
  * Embeds content using [Google Gemini embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
  * Stores vectors in a [FAISS index](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes) for fast similarity search
* [Query Handling](query-handling)
  * Uses [k-top searching](https://github.com/facebookresearch/faiss/wiki/Getting-started#searching) to find the most relevant context material for a query
  * Ranks matched context chunks based on specialized weighting for source and origin time
  * Lightweight [Flask API](https://flask.palletsprojects.com/en/stable/) served with [Gunicorn](https://gunicorn.org/) for production-ready handling of RAG queries
  * Rate-limited API calls to handle [Google Gemini API restrictions](https://ai.google.dev/gemini-api/docs/rate-limits)
  * Uses [Google Gemini&#39;s 2.5 Flash Lite](https://ai.google.dev/gemini-api/docs/models) as the generative language model
  * Offers both [Skript](https://github.com/SkriptLang/Skript) (via [Skript-Reflect](https://github.com/SkriptLang/skript-reflect) Java code) and [Discord Bot](https://discord.com/) interfaces for end users

## Project Implementation

### Data Collection

### Embedding and Indexing

### Query Handling

## Deployment

### User Interfaces

* A minecraft in-game command built using [Skript](https://github.com/SkriptLang/Skript)
* A custom [Discord](https://discord.com/) application that is available in our community server

### Backend API

For the backend, I have created two [Railway](https://railway.com/) instances:

* The first project handles the full backend API
* The second project provides the discord bot API

Both of these instances are synced from this GitHub Repository. Any updates made to this repository will automatically restart the instances so that they are running with the latest updates. The instances also have several environmental variables which are accessed throughout the [project codebase](src/).
