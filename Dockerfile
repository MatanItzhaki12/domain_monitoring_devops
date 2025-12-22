FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY DomainManagementEngine.py .
COPY UserManagementModule.py .
COPY MonitoringSystem.py .
COPY UsersData ./UsersData
COPY tests ./tests

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "app.py"]