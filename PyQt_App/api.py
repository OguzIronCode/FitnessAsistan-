import requests
from PyQt6.QtCore import QThread, pyqtSignal
from state import state

API_BASE = "http://localhost:8000/api"


class _Worker(QThread):
    result  = pyqtSignal(object)
    error   = pyqtSignal(str)

    def __init__(self, method, endpoint, token=None, data=None, params=None):
        super().__init__()
        self.method   = method
        self.endpoint = endpoint
        self.token    = token
        self.data     = data
        self.params   = params

    def run(self):
        try:
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            url = f"{API_BASE}{self.endpoint}"

            r = None
            if self.method == "GET":
                r = requests.get(url, headers=headers, params=self.params, timeout=10)
            elif self.method == "POST":
                r = requests.post(url, headers=headers, json=self.data,
                                  params=self.params, timeout=15)
            elif self.method == "PUT":
                r = requests.put(url, headers=headers, json=self.data, timeout=10)
            elif self.method == "PATCH":
                r = requests.patch(url, headers=headers, params=self.params,
                                   json=self.data, timeout=10)
            elif self.method == "DELETE":
                r = requests.delete(url, headers=headers, timeout=10)
                if r is not None and r.status_code == 204:
                    self.result.emit(None)
                    return

            if r is not None and r.ok:
                try:
                    self.result.emit(r.json())
                except Exception:
                    self.result.emit(None)
            elif r is not None:
                try:
                    err = r.json()
                    self.error.emit(err.get("detail", str(r.text)))
                except Exception:
                    self.error.emit(f"HTTP {r.status_code}")
            else:
                self.error.emit("Bilinmeyen hata")

        except requests.exceptions.ConnectionError:
            self.error.emit("Backend'e bağlanılamadı.\nuvicorn'u çalıştırdığınızdan emin olun.")
        except requests.exceptions.Timeout:
            self.error.emit("İstek zaman aşımına uğradı.")
        except Exception as e:
            self.error.emit(str(e))


class ApiClient:
    def __init__(self):
        self._workers: list[_Worker] = []

    def _call(self, method, endpoint, callback, error_cb=None, data=None, params=None):
        w = _Worker(method, endpoint, state.token, data, params)
        w.result.connect(callback)
        if error_cb:
            w.error.connect(error_cb)
        w.finished.connect(lambda: self._workers.remove(w) if w in self._workers else None)
        self._workers.append(w)
        w.start()
        return w

    def get(self, endpoint, callback, error_cb=None, params=None):
        return self._call("GET", endpoint, callback, error_cb, params=params)

    def post(self, endpoint, data, callback, error_cb=None, params=None):
        return self._call("POST", endpoint, callback, error_cb, data=data, params=params)

    def put(self, endpoint, data, callback, error_cb=None):
        return self._call("PUT", endpoint, callback, error_cb, data=data)

    def patch(self, endpoint, params=None, data=None, callback=lambda _: None, error_cb=None):
        return self._call("PATCH", endpoint, callback, error_cb, data=data, params=params)

    def delete(self, endpoint, callback=lambda _: None, error_cb=None):
        return self._call("DELETE", endpoint, callback, error_cb)


api = ApiClient()
