set -eu

# Configurations
IMAGE_NAME="dms_postgres_image"
CONTAINER_NAME="dms_postgres_db"
CONTAINER_DATA_DIR="/var/lib/postgresql/data"
DATA_DIR="$HOME/postgres_data"
DMS_REPO_FOLDER="$HOME/dms_postgres"
MIGRATION_PATH="$DMS_REPO_FOLDER/data_migration"
VENV_PATH="$MIGRATION_PATH/venv"

# Download project using git
echo "Downloading files from repo..."

mkdir -p "$DMS_REPO_FOLDER"
if [ ! -d "$DMS_REPO_FOLDER/.git" ]; then 
    git clone --branch postgres-db --single-branch \
    https://github.com/MatanItzhaki12/domain_monitoring_devops.git "$DMS_REPO_FOLDER"
else
    echo "Repo already exists, pulling latest changes..."
    git -C "$DMS_REPO_FOLDER" pull
fi

# setup local data directory
echo "Setting up local directory for postgres database..."

mkdir -p "$DATA_DIR"
sudo chown -R 999:999 "$DATA_DIR"

echo "Building docker image via Dockerfile..."
docker build -t "$IMAGE_NAME" \
-f "$DMS_REPO_FOLDER/docker/Dockerfile" \
"$DMS_REPO_FOLDER"

# Clean and remove existing container
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping existing DB container..."
    docker stop "$CONTAINER_NAME"
    echo "Removing existing DB container..."
    docker rm "$CONTAINER_NAME"
fi

# run the postgres container
echo "Running the $CONTAINER_NAME..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p 5432:5432 \
    -v "$DATA_DIR":"$CONTAINER_DATA_DIR" \
    --restart unless-stopped \
    "$IMAGE_NAME"

echo "Database is starting. Run 'docker logs -f $CONTAINER_NAME' to see progress."

echo "Waiting for Postgres to be ready..."
until docker exec "$CONTAINER_NAME" pg_isready -U myuser; do
    sleep 2
done
echo "Postgres is ready."

read -p "do you want to migrate existing data? [Y/n]" migrate_answer
migrate_answer=${migrate_answer:-Y}

if [[ ! "$migrate_answer" =~ ^[Yy]$ ]]; then
    echo "Skipping data migration."
elif [[ ! -f "$DMS_REPO_FOLDER/data_migration/migration_to_db.py" ]]; then
    echo "Migration script not found!"
else
    if ! python3 -m venv --help >/dev/null 2>&1; then
        echo "python3-venv not found. Installing now..."
        sudo apt update && sudo apt install -y python3-venv
    fi

    if [ ! -d "$VENV_PATH" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv "$VENV_PATH"
    fi
    echo "Activating Python virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    echo "Installing migration dependencies..."
    if [ -f "$MIGRATION_PATH/requirements.txt" ]; then
        pip install -r "$DMS_REPO_FOLDER/data_migration/requirements.txt"
    else
        echo "requirements.txt does not exist, exiting..."
        exit 1
    fi

    echo "Migrating existing data..."
    python3 "$MIGRATION_PATH/migration_to_db.py" \
        "$MIGRATION_PATH/UsersData"
    echo "Migration completed."
fi