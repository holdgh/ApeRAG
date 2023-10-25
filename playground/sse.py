import requests

resp = requests.post("http://127.0.0.1:8000/events", stream=True)

for line in resp.iter_lines():
    if line:
        print(line)
