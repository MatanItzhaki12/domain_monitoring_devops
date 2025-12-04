# Jenkins Infrastructure - Automated Deployment

Полностью автоматизированное развёртывание Jenkins Master и Slave с использованием Docker и Configuration as Code (JCasC).

## 🚀 Особенности

- ✅ **Полная автоматизация** - без ручного setup wizard
- ✅ **Предустановленные пользователи** - admin, devops, developer
- ✅ **Автоматическая установка плагинов** - все необходимые плагины устанавливаются при запуске
- ✅ **Configuration as Code (JCasC)** - вся конфигурация в YAML
- ✅ **Docker-in-Docker** - поддержка Docker внутри Jenkins
- ✅ **Master + Slave архитектура** - готовая распределённая система
- ✅ **Credentials предустановлены** - GitHub, DockerHub, AWS
- ✅ **Pipeline готов** - автоматически создаётся job для вашего репозитория

## 📁 Структура

```
infra/Jenkins/
├── Dockerfile              # Образ Jenkins Master с JCasC
├── docker-compose.yml      # Оркестрация Master + Slave
├── jenkins.yaml            # Полная конфигурация Jenkins (JCasC)
├── plugins.txt             # Список плагинов для автоустановки
├── .env.example            # Пример переменных окружения
├── deploy-jenkins.sh       # Скрипт развёртывания (Linux/Mac)
├── deploy-jenkins.ps1      # Скрипт развёртывания (Windows)
└── README.md               # Эта документация
```

## 🔧 Быстрый старт

### Шаг 1: Подготовка окружения

```bash
# Перейдите в директорию Jenkins
cd infra/Jenkins

# Создайте .env файл из примера
cp .env.example .env

# Отредактируйте .env и укажите свои credentials
nano .env  # или используйте любой редактор
```

### Шаг 2: Настройка .env файла

Откройте `.env` и заполните:

```env
# Jenkins Admin Credentials
JENKINS_ADMIN_PASSWORD=your-secure-password-here
JENKINS_DEVOPS_PASSWORD=devops-secure-password
JENKINS_DEV_PASSWORD=dev-secure-password

# Jenkins URL
JENKINS_URL=http://localhost:8080
JENKINS_ADMIN_EMAIL=admin@yourdomain.com

# Docker Hub Credentials
DOCKERHUB_USER=your-dockerhub-username
DOCKERHUB_PASS=your-dockerhub-password-or-token

# GitHub Credentials
GITHUB_USER=MatanItzhaki12
GITHUB_TOKEN=ghp_your_github_personal_access_token

# AWS Credentials (для Terraform)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

### Шаг 3: Запуск Jenkins

#### На Windows:
```powershell
.\deploy-jenkins.ps1
```

#### На Linux/Mac:
```bash
chmod +x deploy-jenkins.sh
./deploy-jenkins.sh
```

### Шаг 4: Доступ к Jenkins

После успешного запуска (2-3 минуты):

1. Откройте браузер: http://localhost:8080
2. Войдите с любым из пользователей:
   - **admin** / your-admin-password (полные права)
   - **devops** / your-devops-password (build, read)
   - **developer** / your-dev-password (только read)

**Никакого setup wizard! Всё готово к работе.**

## 🎯 Что настроено автоматически

### ✅ Пользователи и права
- **admin** - полный доступ ко всему
- **devops** - может создавать/запускать jobs, читать логи
- **developer** - только просмотр jobs и логов

### ✅ Credentials
- **dockerhub-creds** - для push/pull образов
- **github-token** - для клонирования репозиториев
- **aws-credentials** - для Terraform/AWS
- **jenkins-ssh-key** - для подключения агентов

### ✅ Jenkins Slave
- Автоматически подключается к Master
- Поддержка Docker-in-Docker
- Label: "docker linux slave"
- 3 executor'а

### ✅ Pipeline Job
- Автоматически создаётся job: `DevOps/domain-monitoring-pipeline`
- Подключён к вашему GitHub репозиторию
- Использует Jenkinsfile из корня проекта
- Триггер на GitHub push

### ✅ Установленные плагины
- Configuration as Code (JCasC)
- Git, GitHub, Pipeline
- Docker, BlueOcean
- Credentials, Role-based Auth
- Timestamper, HTML Publisher
- Prometheus, Slack, Telegram
- И многие другие (см. plugins.txt)

## 🛠️ Управление Jenkins

### Просмотр логов
```bash
docker-compose logs -f jenkins-master
docker-compose logs -f jenkins-slave
```

### Остановка/Запуск
```bash
docker-compose stop      # Остановить
docker-compose start     # Запустить
docker-compose restart   # Перезапустить
```

### Полное удаление
```bash
docker-compose down -v   # Удалить контейнеры и volumes
```

### Обновление конфигурации
После изменения `jenkins.yaml`:
```bash
docker-compose restart jenkins-master
```

## 🔄 Интеграция с Terraform

Эта конфигурация готова для развёртывания на AWS через Terraform:

1. Jenkins Master будет запущен на отдельной EC2 инстансе
2. Jenkins Slave - на другой EC2 инстансе
3. Все credentials уже предустановлены
4. Pipeline автоматически подключится к GitHub

### Для развёртывания на AWS:

```bash
cd ../Terraform/environment
terraform init
terraform plan
terraform apply
```

## 📝 Настройка для production

### Security
1. Измените пароли по умолчанию в `.env`
2. Используйте secrets manager (AWS Secrets Manager, Vault)
3. Включите HTTPS (nginx reverse proxy)
4. Настройте firewall rules

### Persistence
Volumes для сохранения данных:
- `jenkins_home` - данные Jenkins Master
- `jenkins_slave_home` - workspace агента

### Мониторинг
Jenkins экспортирует метрики для Prometheus:
- Endpoint: http://localhost:8080/prometheus

### Backup
```bash
# Backup Jenkins home
docker run --rm -v jenkins_home:/data -v $(pwd):/backup \
  alpine tar czf /backup/jenkins-backup.tar.gz /data
```

## 🐛 Troubleshooting

### Jenkins не запускается
```bash
# Проверьте логи
docker-compose logs jenkins-master

# Проверьте что порты не заняты
netstat -an | grep 8080
```

### Slave не подключается
```bash
# Проверьте логи slave
docker-compose logs jenkins-slave

# Проверьте что Master запущен
curl http://localhost:8080/login
```

### Плагины не устанавливаются
```bash
# Пересоберите образ
docker-compose build --no-cache jenkins-master
docker-compose up -d
```

## 📚 Дополнительные ресурсы

- [Jenkins Configuration as Code](https://github.com/jenkinsci/configuration-as-code-plugin)
- [Jenkins Docker Image](https://hub.docker.com/r/jenkins/jenkins)
- [Jenkins Plugin Index](https://plugins.jenkins.io/)

## 🤝 Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker-compose logs`
2. Убедитесь что `.env` заполнен правильно
3. Проверьте что Docker работает корректно

---

**Готово! Jenkins полностью настроен и готов к работе без единого клика в UI.**
