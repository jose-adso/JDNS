from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.users import Notificacion
from datetime import datetime

bp = Blueprint('notificaciones', __name__, url_prefix='/notificaciones')

@bp.route('/')
def notificaciones():
    notificaciones = Notificacion.query.all()
    return render_template('notificaciones.html', notificaciones=notificaciones)

@bp.route('/nueva', methods=['GET', 'POST'])
def nueva_notificacion():
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
