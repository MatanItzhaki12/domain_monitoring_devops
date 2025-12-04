# Ansible Deployment Guide for Jenkins

## Автоматическое развёртывание Jenkins на AWS EC2

Эта конфигурация позволяет автоматически развернуть Jenkins Master и Slave на AWS EC2 инстансах с использованием Ansible.

## Структура ролей

```
infra/Ansible/
├── deploy-jenkins.yml          # Главный playbook для развёртывания
├── site.yml                     # Legacy playbook (будет обновлён)
├── inventory/
│   └── inventory.ini           # Inventory файл (заполняется после Terraform)
├── group_vars/
│   └── all/
│       └── vars.yml            # Глобальные переменные
└── roles/
    ├── jenkins_master/
    │   ├── tasks/
    │   │   └── main.yaml       # Задачи для установки Jenkins Master
    │   └── templates/
    │       ├── docker-compose.yml.j2
    │       └── env.j2
    └── jenkins_slave/
        ├── tasks/
        │   └── main.yaml       # Задачи для установки Jenkins Slave
        ├── templates/
        │   └── jenkins-agent.service.j2
        └── handlers/
            └── main.yaml
```

## Предварительные требования

1. **Terraform** - для создания EC2 инстансов
2. **Ansible** 2.9+ с коллекциями:
   ```bash
   ansible-galaxy collection install community.docker
   ansible-galaxy collection install amazon.aws
   ```
3. **SSH ключ** для подключения к EC2
4. **Переменные окружения** с credentials

## Шаг 1: Установка Ansible коллекций

```bash
cd infra/Ansible
ansible-galaxy collection install -r requirements.yml
```

Создайте `requirements.yml`:
```yaml
---
collections:
  - name: community.docker
    version: ">=3.0.0"
  - name: amazon.aws
    version: ">=5.0.0"
```

## Шаг 2: Настройка переменных окружения

Создайте файл с переменными окружения:

```bash
export JENKINS_ADMIN_PASSWORD="your-secure-password"
export JENKINS_DEVOPS_PASSWORD="devops-password"
export JENKINS_DEV_PASSWORD="dev-password"
export DOCKERHUB_USER="your-dockerhub-username"
export DOCKERHUB_PASS="your-dockerhub-password"
export GITHUB_USER="MatanItzhaki12"
export GITHUB_TOKEN="ghp_your_github_token"
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
```

## Шаг 3: Развёртывание инфраструктуры с Terraform

```bash
cd ../Terraform/environment
terraform init
terraform plan
terraform apply
```

После применения Terraform получите IP адреса:

```bash
terraform output jenkins_master_public_ip
terraform output jenkins_slave_public_ip
```

## Шаг 4: Обновление Inventory

Отредактируйте `inventory/inventory.ini`:

```ini
[jenkins_master]
jenkins-master ansible_host=<MASTER_PUBLIC_IP> ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/Group2-KeyPair.pem

[jenkins_slave]
jenkins-slave-1 ansible_host=<SLAVE_PUBLIC_IP> ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/Group2-KeyPair.pem

[jenkins:children]
jenkins_master
jenkins_slave

[jenkins:vars]
ansible_python_interpreter=/usr/bin/python3
```

## Шаг 5: Проверка подключения

```bash
cd infra/Ansible
ansible -i inventory/inventory.ini all -m ping
```

Ожидаемый результат:
```
jenkins-master | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
jenkins-slave-1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

## Шаг 6: Развёртывание Jenkins

### Вариант A: Развернуть всё сразу

```bash
ansible-playbook -i inventory/inventory.ini deploy-jenkins.yml
```

### Вариант B: Развернуть только Master

```bash
ansible-playbook -i inventory/inventory.ini deploy-jenkins.yml --tags master
```

### Вариант C: Развернуть только Slave

```bash
ansible-playbook -i inventory/inventory.ini deploy-jenkins.yml --tags slave
```

## Шаг 7: Проверка развёртывания

После завершения playbook:

```bash
# Проверьте статус Jenkins Master
ansible -i inventory/inventory.ini jenkins_master -m shell -a "docker ps"

# Проверьте статус Jenkins Slave
ansible -i inventory/inventory.ini jenkins_slave -m shell -a "systemctl status jenkins-agent"
```

Откройте браузер: `http://<MASTER_PUBLIC_IP>:8080`

Войдите с учётными данными:
- **Пользователь**: admin
- **Пароль**: значение переменной `JENKINS_ADMIN_PASSWORD`

## Что делают роли

### jenkins_master
1. Устанавливает Docker и Docker Compose
2. Копирует Dockerfile, plugins.txt, jenkins.yaml
3. Создаёт docker-compose конфигурацию
4. Запускает Jenkins Master в Docker
5. Ожидает запуска Jenkins

### jenkins_slave
1. Устанавливает Docker и Java 17
2. Создаёт пользователя jenkins
3. Скачивает agent.jar с Master
4. Создаёт systemd service для агента
5. Запускает и включает агент

## Управление развёрнутым Jenkins

### Просмотр логов

```bash
# Логи Master
ansible -i inventory/inventory.ini jenkins_master -m shell -a "docker logs jenkins-master"

# Логи Slave
ansible -i inventory/inventory.ini jenkins_slave -m shell -a "journalctl -u jenkins-agent -n 50"
```

### Перезапуск служб

```bash
# Перезапуск Master
ansible -i inventory/inventory.ini jenkins_master -m shell -a "docker restart jenkins-master"

# Перезапуск Slave
ansible -i inventory/inventory.ini jenkins_slave -m shell -a "systemctl restart jenkins-agent"
```

### Обновление конфигурации

После изменения `jenkins.yaml`:

```bash
ansible-playbook -i inventory/inventory.ini deploy-jenkins.yml --tags master
```

## Удаление развёртывания

```bash
# Остановить все контейнеры и службы
ansible -i inventory/inventory.ini jenkins_master -m shell -a "docker-compose -f /opt/jenkins/docker-compose.yml down -v"
ansible -i inventory/inventory.ini jenkins_slave -m shell -a "systemctl stop jenkins-agent && systemctl disable jenkins-agent"

# Или через Terraform
cd ../Terraform/environment
terraform destroy
```

## Переменные для кастомизации

Все переменные находятся в `group_vars/all/vars.yml`:

- `jenkins_admin_password` - пароль администратора
- `jenkins_url` - URL Jenkins Master
- `dockerhub_user`, `dockerhub_pass` - Docker Hub credentials
- `github_user`, `github_token` - GitHub credentials
- `aws_access_key_id`, `aws_secret_access_key` - AWS credentials

## Troubleshooting

### Проблема: Ansible не может подключиться

```bash
# Проверьте SSH ключ
ssh -i ~/.ssh/Group2-KeyPair.pem ubuntu@<MASTER_IP>

# Проверьте Security Group в AWS (порт 22 должен быть открыт)
```

### Проблема: Jenkins не запускается

```bash
# Проверьте логи
ansible -i inventory/inventory.ini jenkins_master -m shell -a "docker logs jenkins-master --tail 100"

# Проверьте что Docker работает
ansible -i inventory/inventory.ini jenkins_master -m shell -a "systemctl status docker"
```

### Проблема: Slave не подключается к Master

```bash
# Проверьте сетевую связность
ansible -i inventory/inventory.ini jenkins_slave -m shell -a "curl -I http://<MASTER_PRIVATE_IP>:8080"

# Проверьте логи агента
ansible -i inventory/inventory.ini jenkins_slave -m shell -a "journalctl -u jenkins-agent -f"
```

## Интеграция с CI/CD

После развёртывания Jenkins автоматически создаётся pipeline job:
- **Название**: `DevOps/domain-monitoring-pipeline`
- **Источник**: ваш GitHub репозиторий
- **Jenkinsfile**: из корня репозитория
- **Триггер**: GitHub webhook (нужно настроить в GitHub)

---

**Полная автоматизация: от голой EC2 до полностью настроенного Jenkins за 10-15 минут!**
