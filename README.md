# test-api-websocket

API to receive messages via HTTP route and pass them via websocket

### Installation

```shell
git clone https://github.com/blenzi/test-api-websocket.git
cd test-api-websocket
pip install -r requirements.txt
```

### Running

```shell
uvicorn main:app --host 0.0.0.0 --port 5000
```

### Testing

```shell
pytest main.py
```
