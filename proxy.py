# -*- coding: utf-8 -*-
import httplib
import BaseHTTPServer
import time
import re
import sys

class ProxyHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """proxy connection"""
    conn = None

    buffer_size = 1024

    rbufsize = 0

    def do_GET(self):
        self.do_request()

    def do_POST(self):
        self.do_request()

    def do_PUT(self):
        self.do_request()

    def do_DELETE(self):
        self.do_request()

    def do_request(self):
        headers = self.getformatheaders()
        body = ''
        if self.command == 'POST' or self.command == 'PUT':
            postsize = self.headers.getheader('Content-Length')
            postsize = int(postsize)
            times =  postsize/self.buffer_size+1
            for i in range(0,times):
                if i==times-1:
                    d = self.rfile.read(postsize%self.buffer_size)
                else:
                    d = self.rfile.read(self.buffer_size)
                body += d
                print len(body)
                time.sleep(1.0/hosts['speed'])

        data = self.proxy_request(self.path,headers,body)
        status = data[2]
        self.send_response(status['code'],status['msg'])
        for header in data[0]:
            self.send_header(header[0],header[1])
        self.end_headers()

        time.sleep(1.0/hosts['speed'])
        self.wfile.write(data[1])
        self.wfile.close()

    def send_response(self, code, message=None):
        self.log_request(code)
        if message is None:
            if code in self.responses:
                message = self.responses[code][0]
            else:
                message = ''
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("%s %d %s\r\n" %
                    (self.protocol_version, code, message))

    def getformatheaders(self):
        headers = self.headers.headers
        for i,header in enumerate(headers):
            h = re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", header)[0]
            if h[0] != "Host":
                headers[i] = h
        return headers

    def proxy_request(self,path,headers,body=''):
        conn = self.get_proxy_conn()
        conn.putrequest(self.command,path)
        for header in headers:
            conn.putheader(header[0],header[1])
        conn.endheaders()
        conn.send(body)

        response = conn.getresponse()
        source_headers = response.getheaders()
        headers = []
        for header in source_headers:
            if header[0].lower() == 'connection':
                continue
            if header[0].lower() == 'location':
                rege_str = hosts['remote']['host']+"(:"+str(hosts['remote']['port'])+")?"
                replacement = hosts['bind']['host']+":"+str(hosts['bind']['port'])
                header = ('location',re.sub(rege_str,replacement,header[1]))
            headers.append(header)
        return (headers,response.read(),{'code':response.status,'msg':response.reason})

    def get_proxy_conn(self):
        if self.conn is None:
            self.conn = httplib.HTTPConnection(hosts['remote']['host'],hosts['remote']['port'])
        return self.conn


def check_argv(argv):
    hosts = {}
    if len(argv)>1 and re.match(r".+:\d+",argv[1]):
        res = re.findall(r"(.+):(\d+)",argv[1])[0]
        hosts['bind'] = {
            'host':res[0],
            'port':int(res[1])
        }
    if len(argv)>2 and re.match(r".+:\d+",argv[2]):
        res = re.findall(r"(.+):(\d+)",argv[2])[0]
        hosts['remote'] = {
            'host':res[0],
            'port':int(res[1])
        }
    if len(argv)>3 and re.match(r'\d+',argv[3]):
        hosts['speed'] = int(argv[3])

    return hosts


hosts = check_argv(sys.argv)
if len(hosts)!=3:
    print 'incorrect argv'
    print u'python proxy.py local_server:port remote_server:port speed[1~∞]'
else:
    server_address = (hosts['bind']['host'],hosts['bind']['port'])
    httpd = BaseHTTPServer.HTTPServer(server_address,ProxyHTTPRequestHandler)
    httpd.serve_forever()
    print 'start proxy'

