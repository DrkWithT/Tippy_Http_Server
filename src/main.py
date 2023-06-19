"""
    @file main.py
    @description Contains app handlers and startup code.
    @author Derek Tan
"""

import atexit  # For key interrupt handler
import json    # For config file
import http1.request as req  # Request object
import http1.sender as res   # Response writer
import handlers.ctx.context as handlerctx  # Special object to store more service functionality
import core.driver as driver  # Server logic

my_server = None

# MISC. HELPERS

def get_config_json(file_path: str):
    """
        @description Reads a config file for the server startup.
    """
    result = {
        "serveaddr": "localhost",
        "port": 8080
    }

    fs = None
    file_size = 0
    raw_json = None

    try:
        fs = open(file_path, "r")

        fs.seek(0, 2)
        file_size = fs.tell()
        fs.seek(0, 0)

        raw_json = fs.read(file_size)
        result = json.loads(raw_json)
    except OSError as err:
        print(err.with_traceback(err))
    except Exception as ex:
        print(ex.with_traceback(ex))
    else:
        if fs is not None:
            fs.close()

    return result

# HANDLERS

def handle_fallback(context: handlerctx.HandlerCtx, request: req.SimpleRequest, response: res.SimpleSender):
    last_res = request.before_close()

    response.send_heading("404")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")
    response.send_header("Server", driver.SERVER_APP_NAME)

    if request.method == "HEAD":
        return response.send_body(res.RES_HEAD_BODY, "*/*", b'')
    else:
        return response.send_body(res.RES_ERR_BODY, "*/*", b'')

def handle_favicon(context: handlerctx.HandlerCtx, request: req.SimpleRequest, response: res.SimpleSender):
    temp_resource = context.get_resource("favicon.ico")
    last_res = request.before_close()

    response.send_heading("200")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")

    response.send_header("Server", driver.SERVER_APP_NAME)

    if request.method == "HEAD":
        response.send_body(res.RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        response.send_body(res.RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def handle_index(context: handlerctx.HandlerCtx, request: req.SimpleRequest, response: res.SimpleSender):
    temp_resource = context.get_resource("index.html")
    last_res = request.before_close()

    response.send_heading("200")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")

    response.send_header("Server", driver.SERVER_APP_NAME)

    if request.method == "HEAD":
        return response.send_body(res.RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(res.RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def handle_info(context: handlerctx.HandlerCtx, request: req.SimpleRequest, response: res.SimpleSender):
    temp_resource = context.get_resource("info.html")
    last_res = request.before_close()

    response.send_heading("200")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")

    response.send_header("Server", driver.SERVER_APP_NAME)

    if request.method == "HEAD":
        return response.send_body(res.RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(res.RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def handle_css(context: handlerctx.HandlerCtx, request: req.SimpleRequest, response: res.SimpleSender):
    temp_resource = context.get_resource("style.css")
    last_res = request.before_close()

    response.send_heading("200")
    response.send_header("Date", context.get_gmt_str())

    if last_res:
        response.send_header("Connection", "Close")
    else:
        response.send_header("Connection", "Keep-Alive")
    response.send_header("Server", driver.SERVER_APP_NAME)

    if request.method == "HEAD":
        return response.send_body(res.RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(res.RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def interrupt_handler():
    my_server.force_stop()
    print("Stopped server.")

# RUN SERVER

atexit.register(interrupt_handler)  # NOTE This handles CTRL+C to close the server gracefully.

config_dict = get_config_json("./config.json")
my_server = driver.TippyServer(hostname = config_dict["serveaddr"], port = config_dict["port"])

my_server.register_fallback_handler(handle_fallback)
my_server.register_handler(["/index.html"], handle_index)
my_server.register_handler(["/info.html"], handle_info)
my_server.register_handler(["/style.css"], handle_css)

my_server.run()
