import json

path = r'G:\work_software\claw\.workbuddy\AI酒馆\SillyTavern-re\data\default-user\secrets.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
for k, v in data.items():
    if v and ('api' in k.lower() or 'key' in k.lower() or 'token' in k.lower()):
        print(k + ':', str(v)[:50])

path2 = r'G:\work_software\claw\.workbuddy\AI酒馆\SillyTavern-re\data\default-user\settings.json'
with open(path2, 'r', encoding='utf-8') as f:
    data2 = json.load(f)
for k in ['apiKeyRevision', 'openaiApiKey', 'openaiApiUrl']:
    if k in data2:
        print(k + ':', str(data2[k])[:80])
