# MCLabs Wiki RAG

Welcome to the [MCLabs](https://labs-mc.com/) (often shortened to MCL) Wiki RAG!

This tool will implement RAG (Retrieval-Augmented Generation) to support prompting [Google Gemini ](https://gemini.google.com/app)with specific context relative to our minecraft server from the [community wiki](https://labs-mc.com/wiki/Main_Page) and help ticket system. It will then offer an API for using the system via HTTP requests along with two interfaces for our community to interact with.

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

This project has implemented several different modules to provide a complete and interactive system.

### Data Collection

For data collection, we consider two sources of information that should be stored in our context base for reference during RAG: the MC-Labs Official Wiki, which hosts various articles created by staff that contain detailed information about the server, and our custom Help Ticket System, where we have Question-And-Answer style questions, which are much simpler and more direct with the information they provide.

To obtain the articles from our Official Wiki, we make HTTP requests to the MediaWiki API, allowing us to retrieve article titles and all of the content present on an article page. You can view how we make these requests in [docfetch.py](src/docfetch.py).

To extract the Help Ticket System data, we use a skript module for interacting with our MongoDB database to pull the question-answer pairs from various collections, providing us with simple answers to common questions present throughout multiple seasons of the server's lifetime. While the internal skript to pull data from our database is not provided here, you can view how we parse dump files in [docfetch.py](src/docfetch.py).

### Chunking, Embedding, and Indexing

The first step after data is collected is to chunk it using the appropriate chunking method:

* For Wiki articles, we split articles into chunks of a constant size with a configurable overlap amount. Because our Wiki has a wide variety in the format, layout, and contents of article pages, there is not a good way to derive chunking from the pages themselves. By introducent constant-size chunking with overlap, this allows for contextually related information to be kept together while breaking the content down into small enough chunks for scoping.
* For Q&A data, each question-answer pair is put into its own chunk. This allows for common questions to get very specific context since the similarity between query and chunk will be much higher.

All chunks are stored as dict-like or JSON-like data with some identifying tags:

* `title`: Identifying title of the chunk (only available for Wiki).
* `content`: The actual chunked content.
* `source`: Whether the content came from the Wiki or Help System.
* `date`: The original creation date of the included context (only available for Help System Q&A).

Next the chunks are embedded using Google Gemini's `text-embedding-004` embedding model. We use the `RETRIEVAL_DOCUMENT` task type when doing document embeddings since these chunks are being stored for later retrieval during query.

Finally we index and store our chunks using FAISS. We create a ``IndexFlatL2`` FAISS index (based on Euclidean distance) for the system at instance creation. We then insert each chunk's vector embedding into the index and store the un-embedded chunks themselves in a separate document storage for mapping during query time.

### Query Handling

Using Flask / Gunicorn, our implemented API handles all requests. For each request, the API first checks the requests limits to ensure that it is not being overloaded (based on minute/day request limits). Requests then get checked to see if they are carrying a valid API token. Assuming a request passes these checks, it is then passed on to the RAG pipeline:

1. The query is first embedded using the same `text-embedding-004` model but with the `RETRIEVAL_QUERY` task type
2. We then use L2 similarity search to find the `k*2=10` most similar vector embeddings in the FAISS index
3. The corresponding documents for the found indices from our document collection are then collected
4. Weightings are applied to the similarity scores for each document based on information source, map season, and time-since-creation
5. The final `k=5` similar documents post-weighting are combined with the user's prompt along with various instructions to tune the responses of the language model
6. We send the full prompt (instructions, context, question) to Google Gemini's 2.5-flash-lite model (via API) and wait for the response
7. The answer to the query is then returned to the API caller directly

### Skript Integration

The primary interface for players to use this tool is with the pre-existing Skript-based help ticket system. This sytem allows for users to create in-game help tickets, which previously required manual responses for all questions. Although the implementation of the help system is not given with this project, it directly uses the provided reflect section as discussed in [mclwikirag.sk](skript/mclwikirag.sk).

> One of the large problems with sending HTTP requests and receiving HTTP responses in Skript is the lack of stable addons. Though there are a few different addons that attempt to accomplish this functionality, each has its own pros and cons. After testing some of the addons we currently have implemented for other API's, it was found that none of them would be able to produce the required functionality for this project. Because of this, I implemented my own reflect section that allows for API requests to be made with all of the correct HTTP fields and field values.
>
> Reflect sections are made using [skript-reflect](https://github.com/SkriptLang/skript-reflect), an addon that bridges the gap between Skript development and Java development. Essentially, this allows us to implement Java code directly in our skript codebase, use it dynamically like we would other skript code, and combine the syntaxes of the two languages. While this does allow us to combine the benefits of the two languages, it also presents two different "rulebooks" that we have to conform to.
>
> To briefly demonstrate how this implementation is done, consider this line of reflection code:
>
> `try {_jsonRequestBody}.put("api_token", mwr_getEnvironmentalVariable("API_TOKEN"))`
>
> In this line, we have a skript-reflect try statement to catch Java errors that may result from us using a method of a Java object that is stored in a skript variable. We call this Java object's method with two parameters, one of which is a base Skript string and the other is also a Skript string that is returned from a Skript function defined elsewhere in our codebase. All of this accomplished by combining both Java and Skript syntax via reflection. If that doesn't make sense, don't worry, the point here is not to teach reflection or skript syntax. Just understand that most of the code seen here is not Java code, and it is not supposed to be, but it's not quite Skript code, either.

With the implemented reflection section, we provide two different ways that the rest of our codebase can interact with the API:

* Provide a player's name to the section and allow the section to directly mesage the output to the player. Preferred for cases where the raw output can be given to the player, such as for query commands or development / testing, along with implementation in triggers, where Skript will not allow waiting or delay before returning to the execution caller (player command or Skript event).
* Wait for the response from the section and handle it further. Preferred for cases where delay is allowed, such as with the help ticket system, when players would already have to wait for a response from a staff member.

Both allow this to happen asynchronously. The main difference is in whether or not you the caller can wait for responses before continuing and whether or not the end response needs further formatting or actions.

### Discord Integration

An additional interface for end users to interact with this system is Discord. To provide this, a lightweight implementation of a Discord Bot Application is provided in [the discord module](discord/). It creates a basic application (along with some styling like a displayed activity) and a singular command to ask questions. The application can then be invited to any desired servers, primarily our main community discord, our staff member discord, and our development/testing discord.

## Backend Deployment

For the backend, I have created two [Railway](https://railway.com/) instances:

* The first instance handles the full backend API
* The second instance provides the discord bot API

Both of these instances are synced from this GitHub Repository. Any updates made to this repository will automatically restart the instances so that they are running with the latest updates. The instances also have several environmental variables which are accessed throughout the [project codebase](src/).
