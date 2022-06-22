import tkinter as tk
import tkinter.messagebox as msg
import socket
import configparser
import threading
import os


def warning(message):
    msg.showwarning("Предупреждение", message)

def error(message, error=None):
    msg.showerror("Ошибка", message)
    print(error)

class Client(socket.socket):
    def __init__(self, host, port, warning_disconnect=0):
        self.warning_disconnect = warning_disconnect
        self.address = host, port
        try:
            super().__init__(socket.AF_INET, socket.SOCK_STREAM)
            self.connect(self.address)
        except ConnectionError as e:
            print(f"{e}\nНе удается подключиться к серверу {':'.join(map(str, self.address))}")
            if self.warning_disconnect:
                warning(f"Не удается подключиться к серверу {':'.join(map(str, self.address))}.\nВозможно, этот сервер не существует или превышено макс. кол-во подлкючений на нем")
            exit()
        print(f"ID({self.getsockname()[1]})")
    
    def get_data(self, size=2048):
        try:
            data = self.recv(size).decode("utf-8")
            if data:
                return data
            return None
        except UnicodeDecodeError:
            pass

class App:
    def __init__(self):
        self.buffer_text = "Новые данные отсутствуют"

        self.config = configparser.ConfigParser()
        self.config.read(os.path.split(__file__)[0] + "/settings.conf")

        try:
            self.SERVER_PORT = int(self.config["SERVER"]["SERVER_PORT"])
            self.SERVER_IP = self.config["SERVER"]["SERVER_IP"]

            self.AUTOCOPY = int(self.config["APP"]["AUTOCOPY"])

            self.SERVER_DISCONNECTION = int(self.config["SHOW_WARNINGS"]["SERVER_DISCONNECTION"])

            self.client = Client(self.SERVER_IP, self.SERVER_PORT, warning_disconnect=self.SERVER_DISCONNECTION)
        except KeyError as e:
            error("Неправильно составлен или отсутствует файл settings.conf", error=e)
        except ValueError as e:
            error("Неправильное значение параметров в файле settings.conf", error=e)

        self.root = tk.Tk()
        root = self.root
        root.title(f"ID({self.client.getsockname()[1]})")
        root.geometry("300x0")
        root.wm_attributes("-topmost", True)
        if not self.AUTOCOPY:
            root.columnconfigure(0, weight=True)
            root.rowconfigure(0, weight=True)
            root.geometry(f"300x150+{root.winfo_screenwidth() - 300}+0")

            self.text_data = tk.Text(self.root)
            self.text_data.insert(0.0, self.buffer_text)
            self.text_data.config(bd=0, highlightthickness=0, state="disabled")
            self.text_data.grid(row=0, column=0, sticky="NSWE")

            tk.Button(root, text="Копировать", command=self._copy).grid(row=1, column=0, sticky="WE")

        threading.Thread(target=self._run_client, daemon=True).start()
        root.mainloop()

    def _run_client(self):
        while True:
            try:
                self.client.send(b"check")
                data = self.client.get_data() or self.buffer_text
                if not "¤" in data and data != self.buffer_text:
                    self.buffer_text = data
                    if self.AUTOCOPY:
                        self.root.clipboard_clear()
                        self.root.clipboard_append(self.buffer_text)
                    else:
                        self._show()
            except ConnectionError as e:
                print(f"{e}\nНе удается подключиться к серверу")
                self.client.close()
                warning(f"Не удается подключиться к серверу")
                os._exit(1)

    def _show(self):
        self.root.lift()
        self.text_data["state"] = "normal"
        self.text_data.delete(0.0, "end")
        self.text_data.insert(0.0, self.buffer_text)
        self.text_data["state"] = "disabled"
        self.root.deiconify()

    def _copy(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.buffer_text)
        self.root.withdraw()

if __name__ == "__main__":
    try:
        App()
    except KeyboardInterrupt:
        print("\nПриложение принудительно остановлено")
    except Exception as e:
        print(f"Ошибка: {e}")