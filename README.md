# README
## Project: "Tippy" HTTP/1.1 Server

### Brief
Lately I've been on an HTTP (1.1) server writing frenzy, and I decided to try Python 3.x for implementing a very minimal, single-threaded HTTP server. This is a toy project made only for learning purposes rather than production uses. Finally, I credit the "HTTP Made Really Easy" guide and _RFC 9112_ as my references. Feel free to fork, etc.

### Supported HTTP Features:
 - Basic message reading:
    - Basic syntax checks are done.
    - Headers such as `Host`, `Content-Length` and `Content-Type` are checked.
 - Persistent or closing connection handling.
 - HEAD and GET methods.
 - Basic cache control headers are supported.

### Current Bugs:
 1. On connection problems, the server may give malformed responses such as a "run-on" response message with multiple status lines and header groups. As of now, I am at a loss on how to fix this.
   - This usually happens with `curl` using HTTP 1.1!

### Old Sample Run:
<img width="400" src="./imgs/PythonHttpServer_Test2.png">

### Some cURL Test Commands:
 - `curl --verbose -I http://localhost:8080/index.html` (HEAD of static resource)
 - `curl --verbose -X GET http://localhost:8080/index.html` (GET page)
 - `curl --verbose -X GET http://localhost:8080/info.html` (GET page)
 - `curl --verbose -X GET http://localhost:8080/index.html -H "Connection: Close" -H "If-Modified-Since: Mon, 12 Jun 2023 23:59:59 GMT"` (GET page with update date check... modify `public/index.html` to test this.)

### Things To Do??
 1. Refactor server code to be cleaner: modular, well-named, etc.
 2. Add URL parsing for relative and absolute URLs.
 3. Add better URL handling for resources and generic paths.
 4. Support 100 Continue. (To do...)
