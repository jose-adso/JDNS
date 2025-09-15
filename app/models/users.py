from flask_login import UserMixin
from app import db
from datetime import datetime

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
    tipo = db.Column(db.Enum('repuesto', 'accesorio', 'telefonos', 'computadores'))
    precio_unitario = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer)
    imagen = db.Column(db.String(200))
    empresa_idempresa = db.Column(db.Integer, db.ForeignKey('empresa.idempresa'))
    

class Dispositivo(db.Model):
    __tablename__ = 'dispositivo'
    iddispositivo = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(45))
    color = db.Column(db.String(45))
    imei = db.Column(db.String(45))

    usuario_idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    
class Reparacion(db.Model):
    __tablename__ = 'reparacion'
    idreparacion = db.Column(db.Integer, primary_key=True)
    fecha_ingreso = db.Column(db.DateTime)
    estado = db.Column(db.String(200))
    problema_reparacion = db.Column(db.Text(500))
    costo = db.Column(db.Integer)
    fecha_entrega = db.Column(db.DateTime)
    telefono_idtelefono = db.Column(db.Integer)
    usuario_idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    dispositivo_iddispositivo = db.Column(db.Integer, db.ForeignKey('dispositivo.iddispositivo'))  
    usuario = db.relationship('Users', backref='reparaciones')
    dispositivo = db.relationship('Dispositivo', backref='reparaciones')
    
    
class HistorialReparacion(db.Model):
    __tablename__ = 'historial_reparacion'
    idhistorial_reparacion = db.Column(db.Integer, primary_key=True)
    reparacion_idreparacion = db.Column(db.Integer, db.ForeignKey('reparacion.idreparacion'))
    estado_anterior = db.Column(db.String(100))
    estado_nuevo = db.Column(db.String(100))
    observacion = db.Column(db.Text)
    fecha_cambio = db.Column(db.DateTime)

    reparacion = db.relationship('Reparacion', backref='historial')



   
    
class VentaFactura(db.Model):
    __tablename__ = 'ventas_factura'
    idventas_factura = db.Column(db.Integer, primary_key=True)
    usuario_idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'), nullable=False)
    fecha_venta = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tipo_venta = db.Column(db.Enum('fisica', 'online', name='tipo_venta_enum'))
    estado_envio = db.Column(db.Enum('pendiente', 'pagado', 'anulado', name='estado_envio_enum'), default='pendiente')
    total = db.Column(db.Numeric(10, 2), nullable=False) 
    usuario = db.relationship('Users', backref='ventas_facturas')  
    



class Pago(db.Model):
    __tablename__ = 'pago'
    idpago = db.Column(db.Integer, primary_key=True)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    monto = db.Column(db.DECIMAL(10, 2))
    metodo_pago = db.Column(db.Enum('efectivo', 'tarjeta', 'transferencia', 'mixto', name='metodo_pago_enum'))
    referencia_pago = db.Column(db.String(100))
    estado_pago = db.Column(db.Enum('pendiente', 'completado', 'fallido', name='estado_pago_enum'))
    proveedor_pago = db.Column(db.String(45))
    token_transaccion = db.Column(db.String(100))
    ventas_factura_idventas_factura = db.Column(db.Integer, db.ForeignKey('ventas_factura.idventas_factura'))

    
    factura = db.relationship('VentaFactura', backref='pagos', lazy=True)



class Carrito(db.Model):
    __tablename__ = 'carrito'
    idcarrito = db.Column(db.Integer, primary_key=True)
    usuario_idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'), nullable=False)
    producto_idproducto = db.Column(db.Integer, db.ForeignKey('producto.idproducto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    fecha_agregado = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    
    producto = db.relationship('Producto', backref='carritos', lazy=True)


    
class Notificacion(db.Model):
    __tablename__ = 'notificacion'
    idnotificacion = db.Column(db.Integer, primary_key=True)
    usuario_idusuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    tipo = db.Column(db.Enum('reparacion', 'pedido'))  
    mensaje = db.Column(db.Text(500))
    leida = db.Column(db.Boolean, default=False) 
    fecha_envio = db.Column(db.DateTime)
    
class MensajeSoporte(db.Model):
    __tablename__ = 'mensaje_soporte'
    idmensaje_soporte = db.Column(db.Integer, primary_key=True)
    emisor_id = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    receptor_id = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    asunto = db.Column(db.String(100))
    mensaje = db.Column(db.Text)
    leido = db.Column(db.Boolean, default=False)
    fecha_envio = db.Column(db.DateTime)
    

class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'
    iddetalles = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)  
    producto_idproducto = db.Column(db.Integer, db.ForeignKey('producto.idproducto'), nullable=False)
    ventas_factura_idventas_factura = db.Column(db.Integer, db.ForeignKey('ventas_factura.idventas_factura'), nullable=False)
    producto = db.relationship('Producto', backref='detalle_ventas')

    
    

class DetalleReparacionProducto(db.Model):
    __tablename__ = 'detalle_reparacion_producto'
    iddetalle_reparacion_producto = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    producto_idproducto = db.Column(db.Integer, db.ForeignKey('producto.idproducto'), nullable=False)
    reparacion_idreparacion = db.Column(db.Integer, db.ForeignKey('reparacion.idreparacion'), nullable=False)

    producto = db.relationship('Producto', backref='detalle_reparacion_productos')
    reparacion = db.relationship('Reparacion', backref='detalle_reparacion_productos')
    


class AdjuntoReparacion(db.Model):
    __tablename__ = 'adjunto_reparacion'
    idadjunto_reparacion = db.Column(db.Integer, primary_key=True)
    reparacion_idreparacion = db.Column(db.Integer, db.ForeignKey('reparacion.idreparacion'), nullable=False)
    ruta_archivo = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_subida = db.Column(db.DateTime)

    


   
   