from flask_login import UserMixin
from app import db

class Users(db.Model, UserMixin):
    __tablename__ = 'usuario'
    idusuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    telefono = db.Column(db.String(45))
    correo = db.Column(db.String(100), unique=True)
    direccion = db.Column(db.String(100))
    password = db.Column(db.String(255))
    rol = db.Column(db.Enum('cliente', 'tecnico', 'admin'))
    


    def get_id(self):
        return str(self.idusuario)

    
    @property
    def is_active(self):
        return True  
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
    
class Empresa(db.Model, UserMixin):
    __tablename__ = 'empresa'
    idempresa = db.Column(db.Integer, primary_key=True)
    razon_social = db.Column(db.String(100))
    telefono = db.Column(db.String(45))
    correo = db.Column(db.String(100))
    direccion = db.Column(db.String(100))
    
class Producto(db.Model):
    _tablename_ = 'producto'
    idproducto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Enum('repuesto', 'accesorio'))
    precio_unitario = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer)
    imagen = db.Column(db.String(200))
    empresa_idempresa = db.Column(db.Integer, db.ForeignKey('empresa.idempresa'))