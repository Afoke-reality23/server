import socket
import requests
from urllib.parse import urlparse,parse_qs
import json
import threading
import os
import traceback


server=socket.socket()
server_IP=''
port=int(os.getenv("PORT",8080))
server.bind((server_IP,port))
server.listen()

cached_data={}
cors_headers=(
    'HTTP/1.1 200 OK\r\n'
    'Content-Type:application/json\r\n'
    'Access-Control-Allow-Origin:*\r\n'
    'Access-Control-Allow-Methods:GET,POST,OPTIONS\r\n'
    'Access-Control-Allow-Headers:Content-Type\r\n'
    'Access-Control-Max-Age:86400\r\n'
    '\r\n'
)

preflight_headers=(
    "HTTP/1.1 No Content\r\n"
    "Access-Control-Allow-Methods:GET,POST,OPTIONS\r\n"
    "Access-Control-Allow-Origin:*\r\n"
    "Access-Control-Allow-Headers:Content-Type\r\n"
    "Content-Type:application/json\r\n"
    "\r\n"
    )
def handle_connections():
    while True:
        print('server is listening for real connections')
        client_sock,addr=server.accept()
        client_thread=threading.Thread(target=handle_clients,args=(client_sock,addr))
        client_thread.start()


def handle_clients(client_sock,addr):
    try:
        while True:
            data=reciev_full_data(client_sock)
            if data.startswith('OPTIONS'):
                client_sock.send(preflight_headers.encode('utf-8'))
                #client_sock.close()
                continue
        print(f'client with  IP address {str(addr[0])} | port {str(addr[1])} has connected successfully')
        print(data)
        req_city=extractdata(data,addr)
        name=req_city["city_name"]
        strpName=name.strip()
        print(strpName)
        if len(strpName) <=0:
            msg={'Error':'Sorry Name cannot be empty'}
            error_msg=json.dumps(msg)
            handle_response(data,error_msg,client_sock)
            return
        modiName=req_city["city_name"].capitalize()
        if req_city["port"] not in cached_data:
            cached_data.update(dict([(req_city["port"],{})]))
        else:
            pass
        response=server_response(req_city["port"],modiName)
        print(response)
        if response is None:
            handle_response(data,response[1],client_sock)
            return
        handle_response(data,response,client_sock)
        print('message sent successfully')
    except Exception as e:
        print(f"An Error Occurred :{e}")
        traceback.print_exc()
        # client_sock.close()
  


def reciev_full_data(sock):
    try:
        print("ABOUT TO RECEIVE DATA")
        headers=''
        while "\r\n\r\n" not in headers:
            chunk=sock.recv(1024).decode()
            if not chunk:
                return None
            headers+=chunk
        print("SPLITING THE HEAD FRORM THE BODY")
        header,remaining=headers.split('\r\n\r\n',1)
        print("sSUCCESSFULLY SPLITED")
        content_length=0
        print("HEADER PRINT===>",repr(header))
        for line in header.split('\r\n'):
            if line.lower().startswith('content-length:'):
                content_length=line.split(':')[1].strip()
                break
        body=remaining if len(remaining) > 0 else "".strip()
        while len(body) < int(content_length):
            chunk=sock.recv(1024).decode()
            if not chunk:
                print("empty chunk")
                break
            remaining_byte=int(content_length)-len(body)
            body+=chunk[:remaining_byte]
        print("body",repr(body))
        response=header + '\r\n\r\n'+ body
        return response
    except Exception as error:
        print(error)
        traceback.print_exc()


def extractdata(data,port):
    if '\r\n\r\n' in data:
        print('if statment passed')
        head,body=data.split("\r\n\r\n",1)
        try:
            print('insited extraction functon',repr(body))
            parse_body=json.loads(body)
            city_name=parse_body.get('city'," ")
            port_id=parse_body['clientId']
            http_data={
            "city_name":city_name,
            "port":port_id
            }
            # print('http data',http_data)
            return http_data
        except json.JSONDecodeError as error:
            print(error)
    else:
        print(data)
        city_name=data
        plain_data={"port":port,
            "city_name":city_name
        }
        return plain_data
    
def server_response(addr,modName):
    if addr in cached_data and modName in cached_data[addr]:
        response=cached_data[addr][modName]
        return response
    response=fetch_weather(modName)
    set_cached_data(addr,response,modName)
    return response


def fetch_weather(name):
    headers={
        'User-Agent':'MyweatherApp/1.0(ighoafokereality1@gmail.com)'
    }
    api_Key='66797e10ae014d3986b214726242212'
    base_url='http://api.weatherapi.com/v1/'
    current_url=f'{base_url}current.json?key={api_Key}&q={name}'
    forcast_url=f'{base_url}forecast.json?key={api_Key}&q={name}&alerts=yes&aqi=yes&days=5'
    current=requests.get(current_url)
    forecast=requests.get(forcast_url)
    try:
        if current.status_code == 200 and forecast.status_code == 200:
            api_response={
                'current_response':current.json(),
                'forecast_response':forecast.json()
            }
            response=json.dumps(api_response)
            return response
        else:
            if current.status_code == 404 and forecast.status_code == 404:
                msg={'Error':f'{name} does not match city name'}
                api_response=json.dumps(msg)
                return api_response
    except Exception as e:
        return f'Error fetching weather data:{str(e)}'
    



def set_cached_data(port,data,name):
    client_private_cache=dict([(name,data)])
    cached_data[port].update(client_private_cache)

def handle_response(data,response,client_sock):
    try:
        if '\r\n\r\n' in data:
            full_response=cors_headers+response
            #print('full response',full_response)
            client_sock.send(full_response.encode("utf-8"))
            client_sock.shutdown(socket.SHUT_WR)
        else:
            full_response=response
            client_sock.send(full_response.encode("utf-8"))
    except Exception as error:
        print(error)    
    
        
      
handle_connections()
