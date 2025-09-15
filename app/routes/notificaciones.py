from flask import Blueprint, render_template, request, redirect, url_for, abort, jsonify
from app import db
from app.models.users import Notificacion
from datetime import datetime
from flask_login import login_required, current_user

bp = Blueprint('notificaciones', __name__, url_prefix='/notificaciones')


@bp.route('/')
@login_required
def notificaciones():
    # Admin ve todas; usuario normal solo sus notificaciones
    if getattr(current_user, 'rol', None) == 'admin':
        notis = Notificacion.query.order_by(Notificacion.fecha_envio.desc()).all()
    else:
        notis = Notificacion.query.filter_by(usuario_idusuario=current_user.idusuario).order_by(Notificacion.fecha_envio.desc()).all()
    return render_template('notificaciones.html', notificaciones=notis)


@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_notificacion():
    # Solo admins pueden crear notificaciones manualmente
    if getattr(current_user, 'rol', None) != 'admin':
        abort(403)
    if request.method == 'POST':
        nueva = Notificacion(
            usuario_idusuario=request.form['usuario_id'],
            tipo=request.form['tipo'],
            mensaje=request.form['mensaje'],
            leida=False,
            fecha_envio=datetime.now()
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('notificaciones.notificaciones'))
    return render_template('nueva_notificacion.html')


@bp.route('/api')
@login_required
def notificaciones_api():
    # Devuelve notificaciones en JSON (filtrado por usuario si no es admin)
    if getattr(current_user, 'rol', None) == 'admin':
        notis = Notificacion.query.order_by(Notificacion.fecha_envio.desc()).limit(20).all()
    else:
        notis = Notificacion.query.filter_by(usuario_idusuario=current_user.idusuario).order_by(Notificacion.fecha_envio.desc()).limit(20).all()
    result = []
    for n in notis:
        result.append({
            'id': n.idnotificacion,
            'usuario_id': n.usuario_idusuario,
            'tipo': n.tipo,
            'mensaje': n.mensaje,
            'leida': bool(n.leida),
            'fecha_envio': n.fecha_envio.isoformat() if n.fecha_envio else None
        })
    return jsonify(result)


@bp.route('/leer/<int:id>', methods=['POST'])
@login_required
def marcar_leida(id):
    # marcar como leida por el usuario propietario o admin
    n = Notificacion.query.get_or_404(id)
    if getattr(current_user, 'rol', None) != 'admin' and n.usuario_idusuario != current_user.idusuario:
        abort(403)
    n.leida = True
    db.session.commit()
    return jsonify({'ok': True})



