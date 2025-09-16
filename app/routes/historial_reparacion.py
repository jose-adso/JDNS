from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from app import db
from app.models.users import HistorialReparacion, Reparacion, DetalleReparacionProducto, Producto, Dispositivo
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
    todos = HistorialReparacion.query.options(
        joinedload(HistorialReparacion.reparacion).joinedload(Reparacion.dispositivo)
    ).order_by(HistorialReparacion.fecha_cambio.desc()).all()
    print(f"DEBUG: Total historial entries: {len(todos)}")
    dispositivos_vistos = set()
    reparaciones_sin_dispositivo = 0
    for h in todos:
        if not h.reparacion:
            print(f"DEBUG: ERROR - Historial ID {h.idhistorial_reparacion} no tiene reparacion asociada")
            continue
        dispositivo_id = h.reparacion.dispositivo_iddispositivo
        dispositivo = h.reparacion.dispositivo
        if dispositivo_id is None:
            reparaciones_sin_dispositivo += 1
            print(f"DEBUG: Reparacion ID {h.reparacion_idreparacion} no tiene dispositivo_iddispositivo asignado")
        elif dispositivo is None:
            print(f"DEBUG: Reparacion ID {h.reparacion_idreparacion} tiene dispositivo_id {dispositivo_id} pero no se pudo cargar el dispositivo")
        else:
            dispositivo_marca = dispositivo.marca
            print(f"DEBUG: Historial ID: {h.idhistorial_reparacion}, Reparacion ID: {h.reparacion_idreparacion}, Dispositivo ID: {dispositivo_id}, Marca: {dispositivo_marca}")
            dispositivos_vistos.add(dispositivo_id)
    print(f"DEBUG: Dispositivos únicos con historial: {len(dispositivos_vistos)}")
    print(f"DEBUG: Reparaciones sin dispositivo asignado: {reparaciones_sin_dispositivo}")
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


@bp.route('/dispositivo/buscar', methods=['GET', 'POST'])
@login_required
def buscar_dispositivo():
    if request.method == 'POST':
        busqueda = request.form.get('busqueda', '').strip()
        if busqueda:
            # Buscar por IMEI o marca
            dispositivos = Dispositivo.query.filter(
                db.or_(
                    Dispositivo.imei.contains(busqueda),
                    Dispositivo.marca.contains(busqueda)
                )
            ).all()
        else:
            dispositivos = Dispositivo.query.all()
    else:
        dispositivos = Dispositivo.query.all()

    return render_template('dispositivo_buscar.html', dispositivos=dispositivos)


@bp.route('/dispositivo/<int:dispositivo_id>/historial')
@login_required
def historial_dispositivo(dispositivo_id):
    dispositivo = Dispositivo.query.get_or_404(dispositivo_id)

    # Obtener todas las reparaciones del dispositivo
    reparaciones = Reparacion.query.filter_by(dispositivo_iddispositivo=dispositivo_id).options(
        joinedload(Reparacion.historial),
        joinedload(Reparacion.usuario)
    ).order_by(Reparacion.fecha_ingreso.desc()).all()

    # Calcular estadísticas
    total_reparaciones = len(reparaciones)
    costo_total = sum(r.costo for r in reparaciones if r.costo)

    # Obtener todos los historiales de todas las reparaciones
    todos_historiales = []
    for reparacion in reparaciones:
        for h in reparacion.historial:
            todos_historiales.append({
                'historial': h,
                'reparacion': reparacion
            })

    # Ordenar por fecha descendente
    todos_historiales.sort(key=lambda x: x['historial'].fecha_cambio, reverse=True)

    print(f"DEBUG: Dispositivo {dispositivo.marca} - {dispositivo.imei}")
    print(f"DEBUG: Total reparaciones: {total_reparaciones}")
    print(f"DEBUG: Total historiales: {len(todos_historiales)}")

    return render_template('dispositivo_historial.html',
                         dispositivo=dispositivo,
                         reparaciones=reparaciones,
                         todos_historiales=todos_historiales,
                         total_reparaciones=total_reparaciones,
                         costo_total=costo_total)


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
