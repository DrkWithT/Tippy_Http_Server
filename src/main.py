"""
    @file main.py
    @author Derek Tan
"""

import atexit
import http1.request as req
import http1.sender as res
import utils.rescache as rescache
import core.driver as driver

my_server = None

# HANDLERS

def handle_index(context: rescache.ResourceCache, time_generator: any, request: req.SimpleRequest, response: res.SimpleSender):
    temp_resource = context.get_item("index.html")

    response.send_heading("200")
    response.send_header("Date", time_generator())
    response.send_header("Connection", "Keep-Alive")
    response.send_header("Server", driver.SERVER_APP_NAME)

    if request.method == "HEAD":
        return response.send_body(res.RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(res.RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def handle_info(context: rescache.ResourceCache, time_generator: any, request: req.SimpleRequest, response: res.SimpleSender):
    temp_resource = context.get_item("info.html")

    response.send_heading("200")
    response.send_header("Date", time_generator())
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

atexit.register(interrupt_handler)

my_server = driver.TippyServer()

my_server.register_handler(["/index.html"], handle_index)
my_server.register_handler(["/info.html"], handle_info)

my_server.run()
