import json

file = "/tmp/momenta/collection-qa-points.json"
with open(file) as fd:
    data = json.loads(fd.read())

for p in data["result"]["points"]:
    content = json.loads(p["payload"]["_node_content"])
    text = content["text"]
    print(text)
