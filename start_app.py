import webbrowser
import threading
from app import app

def abrir_navegador():
    webbrowser.open("http://127.0.0.1:3000")

if __name__ == "__main__":
    threading.Timer(1.0, abrir_navegador).start()
    app.run()
