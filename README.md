# Microservicio de Lista Negra (Blacklist API)

Este proyecto es un microservicio construido con Flask que permite gestionar una lista negra de correos electrónicos. Incluye autenticación mediante JWT y está preparado para despliegue en AWS.

## Características

- **Autenticación:** Uso de `flask-jwt-extended` para proteger los endpoints.
- **Gestión de Lista Negra:** Permite agregar correos con motivos de bloqueo y consultar su estado.
- **Base de Datos:** Configurado para usar PostgreSQL (con soporte para SQLite en entornos de prueba).
- **Validación:** Uso de `marshmallow` para validar los datos de entrada.
- **CI/CD:** Configuración lista para AWS CodeBuild vía `buildspec.yml`.

## Requisitos Previos

- Python 3.12 o superior.
- Pip (gestor de paquetes de Python).
- (Opcional) Una base de datos PostgreSQL.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd pruebadevops
   ```

2. Crea un entorno virtual e instálalo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Ejecución Local

Para ejecutar la aplicación en modo desarrollo:

```bash
python application.py
```

La API estará disponible en `http://127.0.0.1:5000`.

## Endpoints Principales

| Método | Endpoint | Descripción | Requiere JWT |
|--------|----------|-------------|--------------|
| GET | `/health` | Verifica el estado del servicio. | No |
| POST | `/login` | Autenticación (Credenciales: `admin`/`admin123`). | No |
| POST | `/blacklists` | Agrega un email a la lista negra. | Sí |
| GET | `/blacklists/<email>` | Consulta si un email está bloqueado. | Sí |

## Pruebas

El proyecto utiliza `pytest` para las pruebas unitarias. Para ejecutarlas:

```bash
pytest test_application.py
```

## Configuración de CI/CD (AWS CodeBuild)

El archivo `buildspec.yml` define los pasos para la integración continua:
1. Instalación de dependencias.
2. Configuración de base de datos temporal (SQLite en memoria).
3. Ejecución de pruebas automáticas.
4. Generación de artefactos para despliegue.
