import socket
import requests
from urllib.parse import urlparse,parse_qs
import json
import threading

server=socket.socket()
server_IP=''
port=1998
server.bind((server_IP,port))
server.listen()

cached_data={}
cors_headers='HTTP/1.1 200 OK\r\n'
cors_headers+='Content-Type:application/json\r\n'
cors_headers+='Access-Control-Allow-Origin:*\r\n'
cors_headers+='Access-Control-Allow-Methods:GET,POST,OPTIONS\r\n'
cors_headers+='Access-Control-Allow-Headers:Content-Type\r\n'
cors_headers+='\r\n'
def handle_connections():
    while True:
        print('server is listening for connections')
        client_sock,addr=server.accept()
        print(f'client with  IP address {addr[0]} | port {addr[1]} has connected successfully')
        client_port=str(addr[1])
        print(client_port)
        #handle_clients(client_sock,client_port)
        client_thread=threading.Thread(target=handle_clients,args=(client_sock,client_port))
        client_thread.start()

def handle_clients(client_sock,client_port):
    try:
        while True:
            data=client_sock.recv(1024).decode()
            #print(f"Data received:{data}")
            print("name received")
            recv_data=plain_http_name(data,client_port)
            name=recv_data["city_name"]
            strpName=name.strip()
            print(len(strpName))
            if len(strpName) <=0:
                msg={'Erro':'Sorry Name cannot be empty'}
                error_msg=json.dumps(msg)
                handle_response(data,error_msg,client_sock)
                continue
            modiName=recv_data["city_name"].capitalize()
            if recv_data["port"] not in cached_data:
                cached_data.update(dict([(recv_data["port"],{})]))
            else:
                pass
            print("about to fetch")
            response=server_response(recv_data["port"],modiName)
            print(f"response:{response}")
            if not response:
                handle_response(data,response[1],client_sock)
                continue
            handle_response(data,response,client_sock)
            #client_sock.shutdown(socket.SHUT_WR)
            #print("I'm here now")
            
    except Exception as e:
        print(f'Error handling client :{e}')
    finally:
        client_sock.close()


def plain_http_name(data,port):
    if '\r\n\r\n' in data:
        request_headers,request_body=data.split('\r\n\r\n',1)
        
        port_num=str(extract_http_port(request_headers))
        print("http port",port_num)
        city_name=request_body
        http_data={"port":port_num,
            "city_name":city_name
        }
        print(http_data)
        return http_data
    else:
        city_name=data
        plain_data={"port":port,
            "city_name":city_name
        }
        return plain_data
  
        
        
def extract_http_port(head):
    req_line,main_head=head.split('\r\n',1)
    headers={}
    split_headers=main_head.split('\r\n')
    for heads in split_headers:
        if ":" in heads:
            keys,value=heads.split(":",1)
            headers.update([(keys,value)])
    #print("updated headers: ",headers)
    host=headers.get("Host")
    base_url=f"http://{host}"
    rel_url=req_line.split(" ")[1]
    URL=f"{base_url}{rel_url}"
    parse_url=urlparse(URL)
    client_port=parse_qs(parse_url.query).get('client_port')[0]
    return client_port
 
    
        
def server_response(client_port,modName):
    if client_port in cached_data and modName in cached_data[client_port]:
        print("sending from cache")
        response=cached_data[client_port][modName]
        return response
        
    print("sending direct")
    response=fetch_weather(modName)
    set_cached_data(client_port,response,modName)
    return response




def fetch_weather(name):
    headers={
        'User-Agent':'MyweatherApp/1.0(ighoafokereality1@gmail.com)'
    }
    api_Key='66797e10ae014d3986b214726242212'
    base_url='http://api.weatherapi.com/v1/'
    current_url=f'{base_url}current.json?key={api_Key}&q={name}'
    forcast_url=f'{base_url}forecast.json?key={api_Key}&q={name}&alerts=yes&aqi=yes&days=5'
    #location_url=f"https://nominatim.openstreetmap.org/search?q={name}&limit=1&format=json"
    current=requests.get(current_url)
    forecast=requests.get(forcast_url)
    #location=requests.get(location_url,headers=headers)
    #print(location.status_code)
    print('im here now')
    try:
        if current.status_code == 200 and forecast.status_code == 200:
            print("I got here Cox of 200")
            api_response={
                'current_response':current.json(),
                'forecaste_response':forecast.json(),
                #'location_response':location.json()
            }
            response=json.dumps(api_response)
            print(f"returned response:{response}")
            return response
        else:
            if current.status_code == 404 and forecast.status_code == 404:
                msg={'Error':f'{name} does not match city name'}
                api_response=json.dumps(msg)
                print(api_response)
                return api_response
    except Exception as e:
        return f'Error fetching weather data:{str(e)}'




#def validate_invalid_name(name,client_sock):
    #if len(name) <=0:
        #msg='name cannot be empty '
        #temp_headers=cors_headers.replace('Content-Type:application/json\r\n','Content-Type:text/plain\r\n') + '\r\n' + msg
        #error_msg=temp_headers
        #client_sock.send(error_msg.encode('utf-8'))
        #return False
    #else:
        #return True
  
  
  
    
#def validate_response(respone_msg,client_sock,name):
    #if not respone_msg:
        #msg=f'{name} is not a valid name pls enter a valid name'
        #temp_headers=cors_headers.replace('Content-Type:application/json\r\n','Content-Type:text/plain\r\n') + '\r\n' + msg
        #error_msg=temp_headers
        #client_sock.send(error_msg.encode('utf-8'))
        #return False
    #else:
        #return True
    



def set_cached_data(port,data,name):
    #print(name)
    client_private_cache=dict([(name,data)])
    #print(client_private_cache)
    cached_data[port].update(client_private_cache)

def handle_response(data,response,client_sock):
    if '\r\n\r\n' in data:
        full_response=cors_headers + '\r\n' + response
        client_sock.send(full_response.encode("utf-8"))
        client_sock.shutdown(socket.SHUT_WR)
    else:
        full_response=response
        client_sock.send(full_response.encode("utf-8"))
        print("message sent successfully ")
        #client_sock.shutdown(socket.SHUT_WR)
    
        
      
handle_connections()