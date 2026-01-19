set -e

cd $WORKSPACE/Ansible/

VAULT_FILE=$(mktemp)
echo "$VAULT_PASS" > "$VAULT_FILE"
chmod 600 "$VAULT_FILE"

ansible-playbook playbook.yaml -i inventory/aws_ec2.yml \
--vault-password-file "$VAULT_FILE"

rm -f "$VAULT_FILE"