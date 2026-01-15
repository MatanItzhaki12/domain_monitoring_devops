import json
import os
# check if file exists and make it is a file if not create it

if not os.path.exists(os.path.join(os.path.dirname(__file__), 'matrix.json')):
    with open(os.path.join(os.path.dirname(__file__), 'matrix.json'), 'w') as f:
        matrix = {"backend": {}}
        json.dump(matrix, f)

with open(os.path.join(os.path.dirname(__file__), 'matrix.json')) as f:
    matrix = json.load(f)

frontend_version = os.environ.get(
    "NEW_VERSION_TAG", "localhost"
)
backend_version = os.environ.get(
    "BACKEND_VERSION", "localhost"
)

if backend_version not in matrix["backend"]:
    matrix["backend"][backend_version] = []

matrix["backend"][backend_version].append(frontend_version)

with open(os.path.join(os.path.dirname(__file__), 'matrix.json'), 'w') as f:
    json.dump(matrix, f, indent=2)
