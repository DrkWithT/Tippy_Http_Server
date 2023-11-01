# README
## Project: "Tippy" HTTP/1.1 Server

### Brief
Lately I've been on an HTTP (1.1) server writing frenzy, and I decided to try Python 3.x for implementing a toy web server. This is a toy project made only for learning purposes and to show off my skills. Finally, I credit the "HTTP Made Really Easy" guide and _RFC 9112_ as my references. Feel free to fork, etc.

### Supported HTTP Features:
 - Basic message reading:
    - Basic syntax checks are done.
    - Headers such as `Host`, `Content-Length` and `Content-Type` are checked.
 - Persistent or closing connection handling.
 - HEAD and GET methods.
 - Basic cache control headers are supported.

### Other Features:
 - Producer-Worker thread pooling for handling multiple connections (WIP)
 - Graceful shutdown (WIP)

### Bugs:
 1. On multiple tabs from Firefox, only one worker is providing service although another is also awake. This could be dependent on varying browser behavior on refresh. Edge / Chrome usually restarts a new connection on a random port, but Firefox seems more conservative with starting new connections?

### Old Sample Run:
<img width="400" src="./imgs/PythonHttpServer_Test2.png">

### Some cURL Test Commands:
 - `curl --verbose -I http://localhost:8080/index.html` (HEAD of static resource)
 - `curl --verbose -X GET http://localhost:8080/index.html` (GET page)
 - `curl --verbose -X GET http://localhost:8080/info.html` (GET page)
 - `curl --verbose -X GET http://localhost:8080/index.html -H "Connection: Close" -H "If-Modified-Since: Mon, 12 Jun 2023 23:59:59 GMT"` (GET page with update date check... modify `public/index.html` to test this.)

### Things To Do??
 1. Refactor server code to be cleaner: modular, well-named, etc. (WIP)
 2. Add URL parsing for relative and absolute URLs.
 3. Add threading. (WIP)
 4. Support 100 Continue. (To do...)

### Usage:
 1a. On a Mac or UNIX system, run `ifconfig -a` in the terminal and find your IPv4 address under `inet`.
 1b. On Windows, run `ipconfig` in the shell and find your IPv4 address.
 2. Create a `config.json` file in the project root folder. It should follow this format:
   ```json
   {
      "serveaddr": "localhost",
      "port": 8080,
      "backlog": 4
   }
   ```
 3. Run `python3 src/main.py` for Mac, or `python src/main.py` for Windows within the project root folder.
 4. Make requests with cURL or your browser!
