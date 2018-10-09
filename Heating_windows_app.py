# Run tkinter code in another thread

from tkinter import *
import threading
import time
import socket
import os
import sys

current_temperature = 0


# Heating system contact information
port = 1884
ip = "192.168.0.21"

run_event = threading.Event()

class App(threading.Thread):

    def __init__(self):
        # threading.Thread.__init__(self)
        super(App,self).__init__()
        self.start()

    def callback(self):
        global t1
        global run_event
        self.root.quit()
        run_event.clear()
        t1.join()
        sys.exit()


    def run(self):
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.var = StringVar()
        self.var.set("\nthe current temperature is: " + str(current_temperature) + "\n")
        self.label = Label(self.root, textvariable = self.var)
        self.label.pack()
        self.root.mainloop()

def get_temp(run_event):
    global current_temperature
    global app
    global var
    message = "temp please"
    server_test = 0
    while run_event.is_set():
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(5)
        while run_event.is_set():
            try:
                print("Trying to send message")
                client.sendto(message.encode('utf_8'), (ip, port))
                data, addr = client.recvfrom(1024)
                current_temperature = float(data)
                print("current_temperature: " + str(current_temperature))
                app.var.set("the current temperature is: " + str(current_temperature))
                # app.root.update_idletasks()
                time.sleep(6)
            except socket.timeout:
                server_test += 1
                print("Socket timeout. Count:= " +str(server_test))
                if server_test == 10:
                    print("Can not contact heating system")
                    server_test = 0
                break
            except socket.error as msg:
                print("Socket error")
                time.sleep(5)
                break

t1 = threading.Thread(target=get_temp, args = (run_event,))

def start():
    global run_event
    run_event.set()
    t1.start()
    time.sleep(0.5)

if __name__ == '__main__':
    app = App()
    start()
