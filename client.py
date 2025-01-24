import socket

client=socket.socket()
client_IP="127.0.0.1"
port=1998
client.connect((client_IP,port))

def select_city_name():
    city_name=input("Enter your city name ")
    client.send(city_name.encode("utf-8"))
    return city_name


def communicate():
    try:
    #connt=client.recv(1024).decode()
    #print(connt)
        while True:
            select_city_name()
            msg=client.recv(1024).decode()
            if msg=="Name cannot be Empty! Try again" or msg=="cannot find city name try again":
                print("Server Response >>>>")
                print(msg)
                continue
            else:
                print(msg)
    except Exception as e:
        print(f"Error:{e}")
    
    
communicate()