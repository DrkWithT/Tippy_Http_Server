# README
## Project: "Tippy" HTTP/1.1 Server

### Brief
Lately I've been on an HTTP (1.1) server writing frenzy, and I decided to try Python 3.x for implementing a very minimal, single-threaded HTTP server. This is a toy project made only for learning purposes and _not_ for production! Feel free to fork, etc.

### Supported HTTP Features:
 - Basic message reading:
    - Basic syntax checks are done.
    - Headers such as `Host`, `Content-Length` and `Content-Type` are checked.
 - Persistent or closing connection handling.
 - HEAD and GET methods.

### Current Bugs:
 1. On connection problems, the server may give malformed responses such as a "run-on" response message with multiple status lines and header groups. As of now, I am at a loss on how to fix this.

### Sample Pictures:
<img width="400" src="./imgs/PythonHttpServer_Test2.png">

### Things To Add??
 1. Support 100 Continue.
 2. Support chunked transfer encoding.
