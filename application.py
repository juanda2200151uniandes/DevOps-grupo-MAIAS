# Se importan las librerías necesarias para construir la API
from flask import Flask, request
import os

from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from marshmallow import Schema, fields, ValidationError
from datetime import datetime, timezone, timedelta

# Se inicializa la aplicación Flask
app = Flask(__name__)
application = app

# Se establece la configuración de la aplicación, haciendo uso de los parámetros de ruta a la BBDD y definiendo la clave de autenticación
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "postgresql://postgres:password@devops.cwhg0wckmg13.us-east-1.rds.amazonaws.com:5432/postgres?sslmode=require")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "MaIA-Secret-Key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours = 1)

# Se instancian los objetos de base de datos, la API y el gestor de autenticación
db = SQLAlchemy(app)
api = Api(app)
jwt = JWTManager(app)

# Se define el esquema de la tabla blacklists
class Blacklist(db.Model):
    __tablename__ = "blacklists"

    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(255), unique = True, nullable=False)
    app_uuid = db.Column(db.String(255), nullable = False)
    blocked_reason = db.Column(db.String(255), nullable = True)
    ip = db.Column(db.String(50), nullable = False)
    created_at = db.Column(db.DateTime, nullable = False, default = lambda: datetime.now(timezone.utc))

# Se define el esquema de autenticación
class BlacklistSchema(Schema):
    email = fields.Email(required=True)
    app_uuid = fields.UUID(required = True)
    blocked_reason = fields.Str(required = False, validate = lambda x: len(x) <= 255)

# Se instancia el esquema de autenticación
blacklist_schema = BlacklistSchema()


# Error para probar el pipeline, cambiamos el servicio de salud con un error 500
# Se define un endpoint de prueba
class HealthResource(Resource):
    def get(self):
        return {"status": "fallo_intencional_ci"}, 500

# Se define el endpoint POST para registrarse y autenticarse
class LoginResource(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"mensaje": "El body de la solicitud es obligatorio en formato JSON"}, 400

        username = data.get("username")
        password = data.get("password")

        if username != "admin" or password != "admin123":
            return {"mensaje": "Credenciales inválidas"}, 401

        access_token = create_access_token(identity = username)

        return {
            "mensaje": "Login exitoso",
            "access_token": access_token
        }, 200

# Se define el endpoint POST para agregar correos a la lista negra
class BlacklistResource(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()

            if not data:
                return {"mensaje": "El body de la solicitud es obligatorio en formato JSON"}, 400

            validated_data = blacklist_schema.load(data)

            existing_email = Blacklist.query.filter_by(
                email=validated_data["email"]
            ).first()

            if existing_email:
                return {
                    "mensaje": "El email ya se encuentra en la lista negra"
                }, 409

            client_ip = request.remote_addr

            blacklist_entry = Blacklist(
                email = validated_data["email"],
                app_uuid = str(validated_data["app_uuid"]),
                blocked_reason = validated_data.get("blocked_reason"),
                ip = client_ip
            )

            db.session.add(blacklist_entry)
            db.session.commit()

            current_user = get_jwt_identity()

            return {
                "mensaje": "El email fue agregado exitosamente a la lista negra",
                "registrado_por": current_user,
                "id": blacklist_entry.id,
                "email": blacklist_entry.email,
                "app_uuid": blacklist_entry.app_uuid,
                "blocked_reason": blacklist_entry.blocked_reason,
                "ip": blacklist_entry.ip,
                "created_at": blacklist_entry.created_at.isoformat()
            }, 201

        except ValidationError as err:
            return {
                "mensaje": "Error de validación",
                "errores": err.messages
            }, 400

        except Exception as e:
            db.session.rollback()
            return {
                "mensaje": "Ocurrió un error interno al crear el registro",
                "error": str(e)
            }, 500

# Se define el endpoint para consultar correos en la lista negra
class BlacklistCheckResource(Resource):
    @jwt_required()
    def get(self, email):

        blacklist_entry = Blacklist.query.filter_by(email=email).first()

        if blacklist_entry:
            return {
                "is_blacklisted": True,
                "blocked_reason": blacklist_entry.blocked_reason
            }, 200

        return {
            "is_blacklisted": False
        }, 200

# Se agregan los endpoints a la API
api.add_resource(HealthResource, "/health")
api.add_resource(LoginResource, "/login")        
api.add_resource(BlacklistResource, "/blacklists")
api.add_resource(BlacklistCheckResource, "/blacklists/<string:email>")

#
with app.app_context():
    db.create_all()

# Para desarrollo local
if __name__ == "__main__":
    app.run(debug=True)