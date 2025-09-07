from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.users import Reparacion, Users, Dispositivo
from flask_login import login_required, current_user
from datetime import datetime

bp = Blueprint('reparacion', __name__)

@bp.route('/reparacion/nueva', methods=['GET', 'POST'])
@login_required
def nueva_reparacion():
    if request.method == 'POST':
        if current_user.rol == 'admin':
            usuario_id = request.form['usuario_idusuario']
        else:
            usuario_id = current_user.idusuario

        nueva_rep = Reparacion(
            fecha_ingreso=datetime.now(),
            estado=request.form['estado'],
            problema_reparacion=request.form['problema_reparacion'],
            costo=request.form['costo'] or None,
            fecha_entrega=None,
            telefono_idtelefono=None,
            usuario_idusuario=usuario_id,
            dispositivo_iddispositivo=request.form['dispositivo_iddispositivo']
        )
        db.session.add(nueva_rep)
        db.session.commit()
        return redirect(url_for('reparacion.listar_reparaciones'))

    usuarios = Users.query.all()
    dispositivos = Dispositivo.query.all()
    return render_template('reparacion_nueva.html', usuarios=usuarios, dispositivos=dispositivos)

@bp.route('/reparaciones/listar')
@login_required
def listar_reparaciones():
    if current_user.rol == 'admin':
        reparaciones = Reparacion.query.order_by(Reparacion.fecha_ingreso.desc()).all()
    else:
        reparaciones = Reparacion.query.filter_by(
            usuario_idusuario=current_user.idusuario
        ).order_by(Reparacion.fecha_ingreso.desc()).all()
    return render_template('listar_reparaciones.html', reparaciones=reparaciones)

@bp.route('/reparacion/<int:reparacion_id>')
@login_required
def ver_reparacion(reparacion_id):
    reparacion = Reparacion.query.get_or_404(reparacion_id)
    if current_user.rol != 'admin' and reparacion.usuario_idusuario != current_user.idusuario:
        return redirect(url_for('reparacion.listar_reparaciones'))
    return render_template('ver_reparacion.html', reparacion=reparacion)

@bp.route('/reparacion/editar/<int:reparacion_id>', methods=['GET', 'POST'])
@login_required
def editar_reparacion(reparacion_id):
    reparacion = Reparacion.query.get_or_404(reparacion_id)
    if current_user.rol not in ['admin', 'tecnico']:
        return redirect(url_for('reparacion.listar_reparaciones'))
    if request.method == 'POST':
        reparacion.estado = request.form['estado']
        reparacion.problema_reparacion = request.form['problema_reparacion']
        reparacion.costo = request.form['costo'] or None
        if request.form['estado'] == 'completada' and not reparacion.fecha_entrega:
            reparacion.fecha_entrega = datetime.now()
        db.session.commit()
        return redirect(url_for('reparacion.ver_reparacion', reparacion_id=reparacion_id))
    usuarios = Users.query.all()
    dispositivos = Dispositivo.query.all()
    return render_template('editar_reparacion.html', reparacion=reparacion, usuarios=usuarios, dispositivos=dispositivos)

@bp.route('/reparaciones/estadisticas')
@login_required
def estadisticas_reparaciones():
    if current_user.rol != 'admin':
        return redirect(url_for('reparacion.listar_reparaciones'))
    total = Reparacion.query.count()
    completadas = Reparacion.query.filter_by(estado='completada').count()
    pendientes = Reparacion.query.filter_by(estado='pendiente').count()
    en_proceso = Reparacion.query.filter_by(estado='en_proceso').count()
    estadisticas = {
        'total': total,
        'completadas': completadas,
        'pendientes': pendientes,
        'en_proceso': en_proceso
    }
    return render_template('estadisticas_reparaciones.html', estadisticas=estadisticas)
