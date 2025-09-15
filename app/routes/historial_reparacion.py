from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from app import db
from app.models.users import HistorialReparacion, Reparacion, DetalleReparacionProducto, Producto
from datetime import datetime
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

bp = Blueprint('historial_reparacion', __name__)


@bp.route('/historial/<int:reparacion_id>')
def listar_historial(reparacion_id):
    historial = HistorialReparacion.query.filter_by(reparacion_idreparacion=reparacion_id).all()
    reparacion = Reparacion.query.get_or_404(reparacion_id)
    print(f"DEBUG: Reparacion ID: {reparacion.idreparacion}, Dispositivo ID: {reparacion.dispositivo_iddispositivo}, Dispositivo Marca: {reparacion.dispositivo.marca if reparacion.dispositivo else 'None'}")
    print(f"DEBUG: Historial count: {len(historial)}")
    return render_template('historial_listar.html', historial=historial, reparacion=reparacion)


@bp.route('/historial/nuevo/<int:reparacion_id>', methods=['GET', 'POST'])
def nuevo_historial(reparacion_id):
    reparacion = Reparacion.query.get_or_404(reparacion_id)
    if request.method == 'POST':
        nuevo = HistorialReparacion(
            reparacion_idreparacion=reparacion_id,
            estado_anterior=request.form['estado_anterior'],
            estado_nuevo=request.form['estado_nuevo'],
            observacion=request.form['observacion'],
            fecha_cambio=datetime.strptime(request.form['fecha_cambio'], "%Y-%m-%d")
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('historial_reparacion.listar_historial', reparacion_id=reparacion_id))
    return render_template('historial_nuevo.html', reparacion=reparacion)


@bp.route('/admin')
@login_required
def listar_todos():
    # Sólo admins
    if getattr(current_user, 'rol', None) != 'admin':
        abort(403)
    todos = HistorialReparacion.query.order_by(HistorialReparacion.fecha_cambio.desc()).all()
    print(f"DEBUG: Total historial entries: {len(todos)}")
    for h in todos[:5]:  # Log first 5
        print(f"DEBUG: Historial ID: {h.idhistorial_reparacion}, Reparacion ID: {h.reparacion_idreparacion}, Dispositivo Marca: {h.reparacion.dispositivo.marca if h.reparacion and h.reparacion.dispositivo else 'None'}")
    return render_template('historial_admin_list.html', historial=todos)


@bp.route('/detalle_reparacion_producto/')
@login_required
def listar_detalle():
    detalles = DetalleReparacionProducto.query.options(
        joinedload(DetalleReparacionProducto.producto),
        joinedload(DetalleReparacionProducto.reparacion)
    ).all()
    return render_template('detalle_reparacion_producto_list.html', detalles=detalles)


@bp.route('/detalle_reparacion_producto/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_detalle():
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
        return redirect(url_for('historial_reparacion.listar_detalle'))
    return render_template('detalle_reparacion_producto_nuevo.html', productos=productos, reparaciones=reparaciones)


@bp.route('/admin/actualizar_costo', methods=['POST'])
@login_required
def actualizar_costo():
    # Solo admins
    if getattr(current_user, 'rol', None) != 'admin':
        abort(403)
    reparacion_id = request.form.get('reparacion_id')
    nuevo_costo = request.form.get('costo')
    if not reparacion_id:
        flash('Debe ingresar ID de reparación', 'error')
        return redirect(url_for('auth.dashboard'))
    try:
        reparacion_id = int(reparacion_id)
    except ValueError:
        flash('ID de reparación debe ser un número válido', 'error')
        return redirect(url_for('auth.dashboard'))
    reparacion = Reparacion.query.get_or_404(reparacion_id)
    if nuevo_costo:
        try:
            reparacion.costo = int(nuevo_costo)
            db.session.commit()
            flash('Costo actualizado correctamente', 'success')
        except ValueError:
            flash('Costo debe ser un número válido', 'error')
    else:
        flash('Debe ingresar un costo', 'error')
    return redirect(url_for('auth.dashboard'))
