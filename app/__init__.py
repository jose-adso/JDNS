from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(idUser):
        from .models.users import Users
        return Users.query.get(int(idUser))

    from app.routes import auth, empresa, productos, ventas_factura, carrito, dispositivos, pago, reparaciones, historial_reparacion, notificaciones, mensaje_soporte, detalle_venta, adjunto_reparacion
    app.register_blueprint(historial_reparacion.bp)  
    app.register_blueprint(auth.bp)
    app.register_blueprint(empresa.bp)
    app.register_blueprint(productos.bp) 
    app.register_blueprint(ventas_factura.bp)
    app.register_blueprint(carrito.carrito)         
    app.register_blueprint(dispositivos.bp)         
    app.register_blueprint(pago.pago)               
    app.register_blueprint(reparaciones.bp)
    app.register_blueprint(notificaciones.bp)   
    app.register_blueprint(mensaje_soporte.bp) 
    app.register_blueprint(detalle_venta.bp)  
    app.register_blueprint(adjunto_reparacion.bp_adj)  

    
    

    return app