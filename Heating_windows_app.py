# Run tkinter code in another thread

from tkinter import *
import threading
import time
import socket
import os
import sys
from pathlib import Path
import pickle

image_folder = Path("C:/Users/brave/Desktop/Git/images")

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

    def image_update(self, on):
        if on:
            self.image = PhotoImage(file = image_folder / "on.png")
            self.label_image.configure(image=self.image)
        else:
            self.image = PhotoImage(file = image_folder / "off.png")
            self.label_image.configure(image=self.image)


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

        self.var.set("The current temperature is: " + str(current_temperature) + "\n")
        self.label_currebt_temp = Label(self.root, textvariable = self.var, font = ("Verdana", 20, "bold"))
        self.label_currebt_temp.grid(row = 2, column = 1)

        self.button1 = Button(self.root, bg = "#98DBC6", bd = 12,
        text = "Send", padx = 33, pady = 25, font = ("Helvetica", 20, "bold"),
        command = lambda : self.button_click())
        self.button1.grid(row = 2, column = 2, sticky = W)

        self.image = PhotoImage(file = image_folder / "off.png")

        self.label_image = Label(image = self.image)
        self.label_image.grid(row = 3, column = 2)

        self.root.title("Goss Heating System")
        self.root.resizable(width = False, height = False)
        self.root.mainloop()

    def button_click(self):
        global message
        global temp_changed

        temp_changed = False

        message = self.user_input.get()
        print(message)
        try:
            float(message)
        except ValueError:
            app.user_input.delete(0, END)
            app.user_input.insert(0, "Error")
            messgae = "temp please"
        self.root.focus_force()




def get_temp(run_event):
    global current_temperature
    global app
    global var
    global message

    last_pic = "False"
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
                data = pickle.loads(data)
                print(data)
                if data[2] == "changed":
                    print("working")
                    message = "temp please"
                    temp_changed = True

                if data[1] == "True" != last_pic:
                    app.image_update(True)
                    last_pic = "True"
                elif data[1] == "False" != last_pic:
                    last_pic = "False"
                    app.image_update(False)

                current_temperature = float(data[0])
                if "." == str(app.root.focus_get()):
                    app.user_input.delete(0, END)
                    app.user_input.insert(0, data[3]) # update the input with the current des temp on the pi

                print("current_temperature: " + str(current_temperature))
                app.var.set("The current temperature is: " + str(current_temperature))
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
