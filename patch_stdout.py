import os

with open('gear/updater.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove print() completely or redirect to dummy
content = "import sys\nif sys.stdout is None:\n    class Dummy:\n        def write(self, *a):\n            pass\n        def flush(self):\n            pass\n    sys.stdout = Dummy()\n    sys.stderr = Dummy()\n" + content

with open('gear/updater.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = "import sys\nif sys.stdout is None:\n    class Dummy:\n        def write(self, *a):\n            pass\n        def flush(self):\n            pass\n    sys.stdout = Dummy()\n    sys.stderr = Dummy()\n" + content

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
