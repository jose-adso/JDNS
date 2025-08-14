from flask import Blueprint, render_template, redirect, url_for, request, flash
from app import db
from app.models.users import DetalleReparacionProducto
from app.models.users import Producto
from app.models.users import Reparacion
from flask_login import login_required

bp_detalle_rep = Blueprint('detalle_reparacion_producto', __name__, url_prefix='/detalle_reparacion_producto')

@bp_detalle_rep.route('/')
@login_required
def listar():
    detalles = DetalleReparacionProducto.query.all()
    return render_template('detalle_reparacion_producto_list.html', detalles=detalles)

@bp_detalle_rep.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    productos = Producto.query.all()
    reparaciones = Reparacion.query.all()

    if request.method == 'POST':
        cantidad = int(request.form['cantidad'])
        producto_id = int(request.form['producto_id'])
        reparacion_id = int(request.form['reparacion_id'])

        detalle = DetalleReparacionProducto(
            cantidad=cantidad,
            producto_idproducto=producto_id,
            reparacion_idreparacion=reparacion_id
        )
        db.session.add(detalle)
        db.session.commit()
        flash('Detalle de reparación creado correctamente', 'success')
        return redirect(url_for('detalle_reparacion_producto.listar'))

    return render_template('detalle_reparacion_producto_nuevo.html', productos=productos, reparaciones=reparaciones)
