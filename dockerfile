# 1. Imagen base
FROM public.ecr.aws/docker/library/python:3.9-slim

# 2. Creamos el hogar de la app dentro del contenedor
WORKDIR /app

# 3. Copiamos requisitos e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos TODO (incluyendo application.py y newrelic.ini) al /app del contenedor
COPY . .

# 5. Exponemos el puerto de tu microservicio
EXPOSE 5000

# 6. El comando modificado: Envuelve tu app con el agente de New Relic
CMD ["newrelic-admin", "run-program", "python", "application.py"]