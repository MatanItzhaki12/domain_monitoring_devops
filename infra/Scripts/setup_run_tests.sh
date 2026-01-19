set -e

cd $WORKSPACE/tests/

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/ --maxfail=1 --disable-warnings -q