# 🚀 Полная автоматизация развёртывания Jenkins

## Архитектура решения

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Cloud (Terraform)                    │
│                                                              │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │   EC2: Jenkins       │      │   EC2: Jenkins        │    │
│  │      Master          │◄────►│      Slave            │    │
│  │   (Docker)           │      │   (systemd)           │    │
│  └──────────────────────┘      └──────────────────────┘    │
│         ▲                              ▲                     │
│         │                              │                     │
│         └──────────────┬───────────────┘                     │
│                        │                                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         │ Ansible
                         │
                    ┌────▼─────┐
                    │   Dev    │
                    │  Machine │
                    └──────────┘
```

## 🎯 Что автоматизировано

✅ **Инфраструктура (Terraform)**
- Создание VPC, Subnets, Security Groups
- Запуск EC2 для Jenkins Master и Slave
- Настройка сетевых правил

✅ **Развёртывание Jenkins (Ansible)**
- Установка Docker на Master
- Развёртывание Jenkins в Docker с JCasC
- Автоматическая установка плагинов
- Создание пользователей (admin, devops, developer)
- Настройка Slave и подключение к Master

✅ **Конфигурация (JCasC)**
- Все настройки Jenkins в YAML
- Credentials для GitHub, DockerHub, AWS
- Готовый Pipeline job для вашего проекта
- Полностью настроенная система безопасности

## 📋 Полный процесс развёртывания

### Этап 1: Подготовка (5 минут)

1. **Клонируйте репозиторий**
   ```bash
   git clone https://github.com/MatanItzhaki12/domain_monitoring_devops.git
   cd domain_monitoring_devops
   ```

2. **Установите необходимые инструменты**
   ```bash
   # Terraform
   # https://www.terraform.io/downloads
   
   # Ansible
   pip install ansible
   
   # AWS CLI
   pip install awscli
   aws configure
   ```

3. **Установите Ansible коллекции**
   ```bash
   cd infra/Ansible
   ansible-galaxy collection install community.docker
   ansible-galaxy collection install amazon.aws
   ```

4. **Настройте переменные окружения**
   ```bash
   # Создайте файл env.sh
   cat > env.sh << 'EOF'
   export JENKINS_ADMIN_PASSWORD="YourSecurePassword123"
   export JENKINS_DEVOPS_PASSWORD="DevOpsPassword123"
   export JENKINS_DEV_PASSWORD="DevPassword123"
   export DOCKERHUB_USER="your-dockerhub-username"
   export DOCKERHUB_PASS="your-dockerhub-password"
   export GITHUB_USER="MatanItzhaki12"
   export GITHUB_TOKEN="ghp_yourGitHubPersonalAccessToken"
   export AWS_ACCESS_KEY_ID="your-aws-access-key"
   export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
   export JENKINS_URL="http://jenkins.example.com"
   export JENKINS_ADMIN_EMAIL="admin@example.com"
   EOF
   
   # Загрузите переменные
   source env.sh
   ```

### Этап 2: Развёртывание инфраструктуры (5-7 минут)

1. **Запустите Terraform**
   ```bash
   cd infra/Terraform/environment
   
   # Инициализация
   terraform init
   
   # Проверка плана
   terraform plan
   
   # Применение конфигурации
   terraform apply -auto-approve
   ```

2. **Получите IP адреса инстансов**
   ```bash
   # Сохраните IP адреса
   export MASTER_IP=$(terraform output -raw jenkins_master_public_ip)
   export SLAVE_IP=$(terraform output -raw jenkins_slave_public_ip)
   
   echo "Jenkins Master IP: $MASTER_IP"
   echo "Jenkins Slave IP: $SLAVE_IP"
   ```

3. **Обновите Ansible inventory**
   ```bash
   cd ../../Ansible
   
   cat > inventory/inventory.ini << EOF
   [jenkins_master]
   jenkins-master ansible_host=$MASTER_IP ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/Group2-KeyPair.pem
   
   [jenkins_slave]
   jenkins-slave-1 ansible_host=$SLAVE_IP ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/Group2-KeyPair.pem
   
   [jenkins:children]
   jenkins_master
   jenkins_slave
   
   [jenkins:vars]
   ansible_python_interpreter=/usr/bin/python3
   EOF
   ```

### Этап 3: Развёртывание Jenkins (10-15 минут)

1. **Проверьте подключение к инстансам**
   ```bash
   # Дождитесь пока инстансы запустятся (1-2 минуты)
   sleep 120
   
   # Проверьте SSH подключение
   ansible -i inventory/inventory.ini all -m ping
   ```

2. **Запустите Ansible playbook**
   ```bash
   # Полное развёртывание
   ansible-playbook -i inventory/inventory.ini deploy-jenkins.yml
   
   # Или по частям:
   # ansible-playbook -i inventory/inventory.ini deploy-jenkins.yml --tags master
   # ansible-playbook -i inventory/inventory.ini deploy-jenkins.yml --tags slave
   ```

3. **Дождитесь завершения установки**
   Ansible автоматически:
   - Установит Docker на Master
   - Развернёт Jenkins с JCasC
   - Установит все плагины из plugins.txt
   - Создаст пользователей
   - Настроит Slave и подключит к Master

### Этап 4: Проверка и использование (2 минуты)

1. **Откройте Jenkins в браузере**
   ```bash
   echo "Jenkins URL: http://$MASTER_IP:8080"
   ```

2. **Войдите в систему**
   - **Пользователь**: `admin`
   - **Пароль**: значение `$JENKINS_ADMIN_PASSWORD`
   
   **Никакого setup wizard! Всё уже настроено.**

3. **Проверьте что всё работает**
   - ✅ Dashboard загружается
   - ✅ Slave подключен (Manage Jenkins → Nodes)
   - ✅ Credentials настроены (Manage Jenkins → Credentials)
   - ✅ Pipeline job создан (`DevOps/domain-monitoring-pipeline`)

## 🔄 Локальное тестирование (без AWS)

Для тестирования конфигурации локально:

```bash
cd infra/Jenkins

# 1. Создайте .env файл
cp .env.example .env
# Отредактируйте .env со своими credentials

# 2. Запустите Jenkins локально
# Windows:
.\deploy-jenkins.ps1

# Linux/Mac:
chmod +x deploy-jenkins.sh
./deploy-jenkins.sh

# 3. Откройте браузер
# http://localhost:8080
```

## 🛠️ Управление после развёртывания

### Просмотр логов

```bash
# Master
ansible -i inventory/inventory.ini jenkins_master -m shell -a "docker logs jenkins-master --tail 100"

# Slave
ansible -i inventory/inventory.ini jenkins_slave -m shell -a "journalctl -u jenkins-agent -n 100"
```

### Перезапуск служб

```bash
# Master
ansible -i inventory/inventory.ini jenkins_master -m shell -a "docker restart jenkins-master"

# Slave
ansible -i inventory/inventory.ini jenkins_slave -m shell -a "systemctl restart jenkins-agent"
```

### Обновление конфигурации

После изменения `jenkins.yaml`:

```bash
# Пересоздать Jenkins с новой конфигурацией
ansible-playbook -i inventory/inventory.ini deploy-jenkins.yml --tags master
```

### Добавление нового Slave

1. В `jenkins.yaml` добавьте новый node
2. Обновите Terraform для создания новой EC2
3. Добавьте в inventory новый хост
4. Запустите:
   ```bash
   ansible-playbook -i inventory/inventory.ini deploy-jenkins.yml --tags slave --limit new-slave
   ```

## 🗑️ Удаление всей инфраструктуры

```bash
# 1. Остановить Jenkins
ansible -i inventory/inventory.ini jenkins_master -m shell -a "docker-compose -f /opt/jenkins/docker-compose.yml down -v"

# 2. Удалить EC2 через Terraform
cd infra/Terraform/environment
terraform destroy -auto-approve
```

## 📊 Мониторинг и метрики

Jenkins автоматически настроен с Prometheus экспортером:

```bash
# Метрики доступны по адресу:
curl http://$MASTER_IP:8080/prometheus
```

## 🔐 Security Best Practices

1. **Измените пароли по умолчанию**
   ```bash
   # В env.sh установите надёжные пароли
   export JENKINS_ADMIN_PASSWORD="VerySecurePassword123!@#"
   ```

2. **Настройте HTTPS**
   - Используйте nginx как reverse proxy
   - Получите SSL сертификат (Let's Encrypt)

3. **Ограничьте доступ по IP**
   ```bash
   # В Terraform настройте Security Group
   # Разрешите доступ только с ваших IP
   ```

4. **Используйте AWS Secrets Manager**
   ```bash
   # Храните credentials в Secrets Manager
   # Ansible может загружать их автоматически
   ```

## 📚 Структура файлов

```
domain_monitoring_devops/
├── infra/
│   ├── Jenkins/                    # Docker конфигурация
│   │   ├── Dockerfile              # Jenkins образ с JCasC
│   │   ├── docker-compose.yml      # Master + Slave локально
│   │   ├── jenkins.yaml            # JCasC конфигурация
│   │   ├── plugins.txt             # Список плагинов
│   │   ├── .env.example            # Пример переменных
│   │   ├── deploy-jenkins.sh       # Локальный запуск (Linux)
│   │   ├── deploy-jenkins.ps1      # Локальный запуск (Windows)
│   │   └── README.md               # Документация
│   │
│   ├── Terraform/                  # AWS инфраструктура
│   │   └── environment/
│   │       ├── main.tf             # Главная конфигурация
│   │       ├── compute.tf          # EC2 инстансы
│   │       ├── networking.tf       # VPC, Subnets
│   │       ├── security.tf         # Security Groups
│   │       └── outputs.tf          # IP адреса
│   │
│   └── Ansible/                    # Автоматизация развёртывания
│       ├── deploy-jenkins.yml      # Главный playbook
│       ├── inventory/
│       │   └── inventory.ini       # Список серверов
│       ├── group_vars/
│       │   └── all/vars.yml        # Глобальные переменные
│       ├── roles/
│       │   ├── jenkins_master/     # Роль для Master
│       │   └── jenkins_slave/      # Роль для Slave
│       └── README_DEPLOYMENT.md    # Подробная документация
│
└── Jenkinsfile                     # CI/CD Pipeline
```

## ❓ Troubleshooting

### Проблема: Terraform не может создать инстансы

**Решение:**
```bash
# Проверьте AWS credentials
aws sts get-caller-identity

# Проверьте квоты EC2
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A
```

### Проблема: Ansible не может подключиться

**Решение:**
```bash
# Проверьте SSH ключ
ls -la ~/.ssh/Group2-KeyPair.pem
chmod 400 ~/.ssh/Group2-KeyPair.pem

# Проверьте Security Group (порт 22)
# Добавьте ваш IP в AWS Console
```

### Проблема: Jenkins не запускается

**Решение:**
```bash
# Проверьте логи Docker
ansible -i inventory/inventory.ini jenkins_master \
  -m shell -a "docker logs jenkins-master --tail 200"

# Проверьте что памяти достаточно
ansible -i inventory/inventory.ini jenkins_master \
  -m shell -a "free -h"
```

### Проблема: Slave не подключается

**Решение:**
```bash
# Проверьте сетевую связность
ansible -i inventory/inventory.ini jenkins_slave \
  -m shell -a "curl -I http://<MASTER_PRIVATE_IP>:8080"

# Проверьте логи агента
ansible -i inventory/inventory.ini jenkins_slave \
  -m shell -a "journalctl -u jenkins-agent -f"

# Проверьте Security Group (порт 50000)
```

## 🎓 Дополнительные ресурсы

- [Jenkins Configuration as Code](https://github.com/jenkinsci/configuration-as-code-plugin)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Ansible Documentation](https://docs.ansible.com/)
- [Jenkins Docker Image](https://hub.docker.com/r/jenkins/jenkins)

---

## ✅ Чек-лист развёртывания

- [ ] Terraform установлен и настроен
- [ ] Ansible установлен с коллекциями
- [ ] AWS CLI настроен с credentials
- [ ] Переменные окружения заполнены в env.sh
- [ ] SSH ключ для EC2 готов
- [ ] Terraform apply выполнен успешно
- [ ] IP адреса получены и добавлены в inventory
- [ ] Ansible playbook выполнен без ошибок
- [ ] Jenkins доступен по URL
- [ ] Вход с учётными данными работает
- [ ] Slave подключен к Master
- [ ] Pipeline job создан и работает

**Время полного развёртывания: ~20-25 минут**

**Результат: Полностью настроенный Jenkins без единого ручного действия в UI!**
