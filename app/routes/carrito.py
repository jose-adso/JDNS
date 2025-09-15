from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.users import Carrito, Producto, Pago, VentaFactura
from flask_login import current_user
from datetime import datetime

carrito = Blueprint('carrito', __name__)

@carrito.route('/carrito')
def ver_carrito():
    if current_user.is_authenticated:
        carritos = Carrito.query.filter_by(usuario_idusuario=current_user.idusuario).all()
        productos = {item.producto_idproducto: Producto.query.get(item.producto_idproducto) for item in carritos}
        total = sum(item.cantidad * productos[item.producto_idproducto].precio_unitario for item in carritos)
        return render_template('plantilla.html', carritos=carritos, productos=productos, total=total, carrito_view=True)
    return redirect(url_for('auth.login'))

@carrito.route('/carrito/agregar/<int:producto_id>', methods=['POST'])
def agregar_al_carrito(producto_id):
    if current_user.is_authenticated:
        producto = Producto.query.get_or_404(producto_id)
        if producto.stock > 0:
            carrito_item = Carrito.query.filter_by(usuario_idusuario=current_user.idusuario, producto_idproducto=producto_id).first()
            if carrito_item:
                carrito_item.cantidad += 1
            else:
                nuevo_item = Carrito(
                    usuario_idusuario=current_user.idusuario,
                    producto_idproducto=producto_id,
                    cantidad=1,
                    fecha_agregado=datetime.utcnow()  
                )
                db.session.add(nuevo_item)
            producto.stock -= 1
            db.session.commit()
            flash('Producto agregado al carrito!', 'success')
        else:
            flash('No hay stock disponible.', 'error')
    return redirect(url_for('producto.listar_productos'))

@carrito.route('/carrito/aumentar_cantidad/<int:carrito_id>', methods=['POST'])
def aumentar_cantidad(carrito_id):
    if current_user.is_authenticated:
        carrito_item = Carrito.query.get_or_404(carrito_id)
        if carrito_item.usuario_idusuario == current_user.idusuario:
            producto = Producto.query.get(carrito_item.producto_idproducto)
            if producto.stock > 0:
                carrito_item.cantidad += 1
                producto.stock -= 1
                db.session.commit()
                flash('Cantidad aumentada en el carrito!', 'success')
            else:
                flash('No hay stock disponible.', 'error')
    return redirect(url_for('carrito.ver_carrito'))

@carrito.route('/carrito/reducir_cantidad/<int:carrito_id>', methods=['POST'])
def reducir_cantidad(carrito_id):
    if current_user.is_authenticated:
        carrito_item = Carrito.query.get_or_404(carrito_id)
        if carrito_item.usuario_idusuario == current_user.idusuario:
            producto = Producto.query.get(carrito_item.producto_idproducto)
            if carrito_item.cantidad > 1:
                carrito_item.cantidad -= 1
                producto.stock += 1
                db.session.commit()
                flash('Cantidad reducida en el carrito!', 'success')
            else:
                producto.stock += 1
                db.session.delete(carrito_item)
                db.session.commit()
                flash('Última unidad eliminada del carrito!', 'success')
    return redirect(url_for('carrito.ver_carrito'))

@carrito.route('/carrito/eliminar/<int:carrito_id>', methods=['POST'])
def eliminar_del_carrito(carrito_id):
    if current_user.is_authenticated:
        carrito_item = Carrito.query.get_or_404(carrito_id)
        if carrito_item.usuario_idusuario == current_user.idusuario:
            producto = Producto.query.get(carrito_item.producto_idproducto)
            producto.stock += carrito_item.cantidad
            db.session.delete(carrito_item)
            db.session.commit()
            flash('Producto eliminado del carrito!', 'success')
    return redirect(url_for('carrito.ver_carrito'))

@carrito.route('/carrito/pagar', methods=['POST'])
def realizar_pago():
    if current_user.is_authenticated:
        carritos = Carrito.query.filter_by(usuario_idusuario=current_user.idusuario).all()
        if carritos:
            total = sum(item.cantidad * Producto.query.get(item.producto_idproducto).precio_unitario for item in carritos)
            nueva_factura = VentaFactura(usuario_idusuario=current_user.idusuario, total=total)
            db.session.add(nueva_factura)
            db.session.flush()
            for item in carritos:
                nuevo_pago = Pago(
                    fecha_pago=datetime.utcnow(),
                    monto=Producto.query.get(item.producto_idproducto).precio_unitario * item.cantidad,
                    metodo_pago='efectivo',
                    estado_pago='pendiente',
                    proveedor_pago='Proveedor Genérico',
                    token_transaccion='TOKEN_' + str(nueva_factura.idventas_factura),
                    ventas_factura_idventas_factura=nueva_factura.idventas_factura
                )
                db.session.add(nuevo_pago)
                db.session.delete(item)
            db.session.commit()
            flash('Pago iniciado con éxito!', 'success')
        else:
            flash('El carrito está vacío.', 'error')
    return redirect(url_for('carrito.ver_carrito'))