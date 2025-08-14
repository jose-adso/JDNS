from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.users import MensajeSoporte
from datetime import datetime

bp = Blueprint('mensaje_soporte', __name__, url_prefix='/mensaje_soporte')

@bp.route('/')
def mensajes_soporte():
    mensajes = MensajeSoporte.query.all()
    return render_template('mensajes_soporte.html', mensajes=mensajes)

@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_mensaje_soporte():
    if request.method == 'POST':
        nuevo = MensajeSoporte(
            emisor_id=request.form['emisor_id'],
            receptor_id=request.form['receptor_id'],
            asunto=request.form['asunto'],
            mensaje=request.form['mensaje'],
            leido=False,
            fecha_envio=datetime.now()
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('mensaje_soporte.mensajes_soporte'))
    return render_template('nuevo_mensaje_soporte.html')
