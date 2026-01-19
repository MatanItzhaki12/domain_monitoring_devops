set -e

KEY_FILE_NAME="group2_${params.CLIENT_NAME}_private_key.pem"
SRC="$WORKSPACE/Terraform/environment/keys/$KEY_FILE_NAME"
DEST="$HOME/.ssh/keys/$KEY_FILE_NAME"

mkdir -p "$HOME/.ssh/keys"
chmod 700 "$HOME/.ssh"
chmod 700 "$HOME/.ssh/keys"

if [ -f "$DEST" ]; then
    rm -f "$DEST"
fi

cp "$SRC" "$DEST"
chmod 600 "$DEST"
# or

env.CLIENT_KEY = "$SRC"