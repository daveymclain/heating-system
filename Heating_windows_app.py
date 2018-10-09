# Run tkinter code in another thread

from tkinter import *
import threading
import time
import socket
import os
import sys

current_temperature = 0

temp_changed = True

message = "temp please"

# Heating system contact information
port = 1884
ip = "192.168.0.42"

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
        self.root.grid()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)


        self.UserIn = StringVar()
        self.var = StringVar()

        self.label_new_temp = Label(self.root, text = "Enter a new desired temp: ",
        font = ("Verdana", 20, "bold"))
        self.label_new_temp.grid(row = 1, column = 1)

        self.user_input = Entry(self.root, bg = "#5BC8AC", bd = 29,
        insertwidth = 4, width = 6,
        font = ("Verdana", 20, "bold"), textvariable = self.UserIn, justify = RIGHT)
        self.user_input.grid(row = 1, column = 2)

        self.user_input.insert(0, "20")

        self.var.set("\nthe current temperature is: " + str(current_temperature) + "\n")
        self.label_currebt_temp = Label(self.root, textvariable = self.var, font = ("Verdana", 20, "bold"))
        self.label_currebt_temp.grid(row = 2, column = 1)

        self.button1 = Button(self.root, bg = "#98DBC6", bd = 12,
        text = "Send", padx = 33, pady = 25, font = ("Helvetica", 20, "bold"),
        command = lambda : self.button_click())
        self.button1.grid(row = 2, column = 2, sticky = W)

        self.root.resizable(width = False, height = False)
        self.root.mainloop()

    def button_click(self):
        global message
        global temp_changed

        temp_changed = False

        message = self.user_input.get()


def get_temp(run_event):
    global current_temperature
    global app
    global var
    global message

    server_test = 0
    while run_event.is_set():
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(5)
        while run_event.is_set():
            try:
                print("Trying to send message")
                client.sendto(message.encode('utf_8'), (ip, port))
                d = client.recvfrom(1024)
                data = d[0]
                addr = d[1]
                print(data.decode())
                if data.decode() == "changed":
                    print("working")
                    message = "temp please"
                    temp_changed = True
                else:
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
