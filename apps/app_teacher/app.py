import tkinter as tk
import tkinter.messagebox as msg
import socket
import configparser
import threading
import time
import os


def warning(message):
    msg.showwarning("Предупреждение", message)

def error(message, error=None):
    msg.showerror("Ошибка", message)
    print(error)

class Server(socket.socket):
    def __init__(self, host, port, max_connections, warning_disconnect=0, warning_connection_attempt=0):
        self.connections = []
        self.max_connections = max_connections
        self.warning_disconnect = warning_disconnect
        self.warning_connection_attempt = warning_connection_attempt
        self.address = host, port
        try:
            super().__init__(socket.AF_INET, socket.SOCK_STREAM)
            self.bind(self.address)
            self.listen(max_connections)
        except OSError as e:
            error(f"{e}\n{':'.join(map(str, self.address))} - Этот адрес уже используется или IP не действительный\nПопробуйте сменить порт или IP")
            print(f"{e}\n{':'.join(map(str, self.address))} - Этот адрес уже используется или IP не действительный")

    def start(self):
        while True:
            connection, sockname = self.accept()
            if len(self.connections) + 1 > self.max_connections:
                connection.close()
                if self.warning_connection_attempt:
                    warning(f"Попытка подключения, превышающее макс. кол-во подключений\nID({sockname[1]})")
                continue
            self.connections.append((connection, sockname[1]))
            print(f"\nID({sockname[1]}) подключился")
    
    def send_data(self, data):
        for connection in self.connections:
            try:
                connection[0].send(data.encode("utf-8"))
            except ConnectionError as e:
                print(f"\n{e}\nID({connection[1]}) закрыл соединение")
                self.connections.remove(connection)
                if self.warning_disconnect:
                    warning(f"ID({connection[1]}) закрыл соединение")
                continue


class App:
    def __init__(self):
        self.buffer_text = None
        self.config = configparser.ConfigParser()
        self.config.read(os.getcwd() + "/settings.conf")

        print("CONF_FILE:", os.getcwd() + "/settings.conf")
        print("IP:", socket.gethostbyname(socket.gethostname()))

        try:
            self.SHOW_WINDOW = int(self.config["APP"]["SHOW_WINDOW"])
            self.SHOW_DATA = int(self.config["APP"]["SHOW_DATA"])

            self.SERVER_PORT = 5567
            self.SERVER_HOST = self.config["SERVER"]["ADDRESS"]
            if self.SERVER_HOST != "None":
                self.SERVER_HOST = self.config["SERVER"]["ADDRESS"]
            else:
                self.SERVER_HOST = socket.gethostbyname(socket.gethostname())

            self.MAX_CONNECTIONS = int(self.config["CONNECTIONS"]["MAX_CONNECTIONS"])

            self.STUDENT_DISCONNECTION = int(self.config["SHOW_WARNINGS"]["STUDENT_DISCONNECTION"])
            self.CONNECTION_ATTEMPT = int(self.config["SHOW_WARNINGS"]["CONNECTION_ATTEMPT"])
        except KeyError as e:
            error("Неправильно составлен или отсутствует файл settings.conf", error=e)
        except ValueError as e:
            error("Неправильное значение параметров в файле settings.conf", error=e)

        self.server = Server(
            self.SERVER_HOST, 
            self.SERVER_PORT, 
            max_connections=self.MAX_CONNECTIONS, 
            warning_disconnect=self.STUDENT_DISCONNECTION, 
            warning_connection_attempt=self.CONNECTION_ATTEMPT
        )

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.resizable(False, False)

        if self.SHOW_WINDOW:
            self.root.deiconify()
            self.root.title("App")
            self.root.geometry(f"200x{100*self.SHOW_DATA}")
            self.root.wm_attributes("-topmost", True)

            if self.SHOW_DATA:
                self.root.resizable(True, True)
                self.text_data = tk.Text(self.root, text=self.buffer_text, state="disabled")
                self.text_data.config(bd=0, highlightthickness=0)
                self.text_data.pack(expand=True, fill="both")

        threading.Thread(target=self.check_buffer, daemon=True).start()
        threading.Thread(target=self.server.start, daemon=True).start()

        self.root.mainloop()
    
    def check_buffer(self):
        while True:
            time.sleep(0.1)
            try:
                self.server.send_data("¤")
                clipboard_text = self.root.clipboard_get()
                if clipboard_text != self.buffer_text:
                    self.buffer_text = clipboard_text
                    self._send_buffer()
            except tk.TclError:
                continue

    def _send_buffer(self):
        self.buffer_text = self.root.clipboard_get()
        self.server.send_data(self.buffer_text)
        if self.SHOW_DATA: 
            self._show_data()

    def _show_data(self):
        self.text_data.configure(state="normal")
        self.text_data.delete(1.0, "end")
        self.text_data.insert(1.0, self.buffer_text)
        self.text_data.configure(state="disabled")

if __name__ == "__main__":
    try:
        App()
    except KeyboardInterrupt:
        print("\nПриложение принудительно остановлено")
    except Exception as e:
        print(f"Ошибка: {e}")
