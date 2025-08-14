from flask import Blueprint, render_template, redirect, url_for, request, flash
from app import db
from app.models.users import DetalleVenta
from app.models.users import Producto, VentaFactura
from flask_login import login_required

bp = Blueprint('detalle_venta', __name__, url_prefix='/detalle_venta')

@bp.route('/')
@login_required
def listar():
    detalles = DetalleVenta.query.all()
    return render_template('detalle_venta_list.html', detalles=detalles)

@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    productos = Producto.query.all()
    facturas = VentaFactura.query.all()

    if request.method == 'POST':
        cantidad = int(request.form['cantidad'])
        precio_unitario = float(request.form['precio_unitario'])
        producto_id = int(request.form['producto_id'])
        factura_id = int(request.form['factura_id'])

        detalle = DetalleVenta(
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            producto_idproducto=producto_id,
            ventas_factura_idventas_factura=factura_id
        )
        db.session.add(detalle)
        db.session.commit()
        flash('Detalle de venta creado', 'success')
        return redirect(url_for('detalle_venta.listar'))

    return render_template('detalle_venta_nuevo.html', productos=productos, facturas=facturas)
