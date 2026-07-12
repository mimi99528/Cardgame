import http.client
import json

conn = http.client.HTTPSConnection("api.uniapi.io")
payload = json.dumps({
   "inputType": 10,
   "gptDescriptionPrompt": "Light, cheerful, and evocative of morning and beginnings. Game background music with a Celtic vibe, ideal for a game's starting village. Features lively flutes and guitars, along with ethnic percussion and string instruments",
   "makeInstrumental": True,
   "mv": "chirp-v5"
})
headers = {
   'Authorization': 'Bearer sk-dZb3Yj5Y3bVXHmN_IgYXoxXnEy6kzAxKdw7CEAfxe9yb9U_-tWQcZaD4Elg',
   'Content-Type': 'application/json'
}
conn.request("POST", "/suno/music/generate", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))