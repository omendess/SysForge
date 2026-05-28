import os
import json

with open('version.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
data['version'] = '2.5.0'
with open('version.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

with open('gear/updater.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
content = re.sub(r'CURRENT_VERSION = ".*?"', 'CURRENT_VERSION = "2.5.0"', content)

with open('gear/updater.py', 'w', encoding='utf-8') as f:
    f.write(content)
