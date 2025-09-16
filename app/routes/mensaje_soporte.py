from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.users import MensajeSoporte, Users
from flask_login import login_required, current_user
from datetime import datetime

bp = Blueprint('mensaje_soporte', __name__, url_prefix='/mensaje_soporte')

@bp.route('/')
@login_required
def mensajes_soporte():
    # Filtrar mensajes según el rol del usuario
    if current_user.rol == 'admin':
        # Admin ve todos los mensajes
        mensajes_recibidos = MensajeSoporte.query.filter_by(receptor_id=current_user.idusuario).all()
        mensajes_enviados = MensajeSoporte.query.filter_by(emisor_id=current_user.idusuario).all()
    elif current_user.rol == 'tecnico':
        # Técnico ve mensajes de clientes y admin
        mensajes_recibidos = MensajeSoporte.query.filter(
            MensajeSoporte.receptor_id == current_user.idusuario,
            MensajeSoporte.emisor_id.in_(
                db.session.query(Users.idusuario).filter(Users.rol.in_(['cliente', 'admin']))
            )
        ).all()
        mensajes_enviados = MensajeSoporte.query.filter_by(emisor_id=current_user.idusuario).all()
    else:  # cliente
        # Cliente ve mensajes de técnicos y admin
        mensajes_recibidos = MensajeSoporte.query.filter(
            MensajeSoporte.receptor_id == current_user.idusuario,
            MensajeSoporte.emisor_id.in_(
                db.session.query(Users.idusuario).filter(Users.rol.in_(['tecnico', 'admin']))
            )
        ).all()
        mensajes_enviados = MensajeSoporte.query.filter_by(emisor_id=current_user.idusuario).all()

    # Obtener nombres de usuarios para mostrar
    usuarios = {user.idusuario: user.nombre for user in Users.query.all()}

    return render_template('mensajes_soporte.html',
                         mensajes_recibidos=mensajes_recibidos,
                         mensajes_enviados=mensajes_enviados,
                         usuarios=usuarios)

@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_mensaje_soporte():
    if request.method == 'POST':
        receptor_id = request.form.get('receptor_id')

        # Validar que el receptor existe y es válido según el rol
        receptor = Users.query.get_or_404(receptor_id)

        # Validaciones según rol
        if current_user.rol == 'cliente' and receptor.rol not in ['tecnico', 'admin']:
            flash('Como cliente solo puedes enviar mensajes a técnicos o administradores.', 'danger')
            return redirect(url_for('mensaje_soporte.nuevo_mensaje_soporte'))

        if current_user.rol == 'tecnico' and receptor.rol not in ['cliente', 'admin']:
            flash('Como técnico solo puedes enviar mensajes a clientes o administradores.', 'danger')
            return redirect(url_for('mensaje_soporte.nuevo_mensaje_soporte'))

        nuevo = MensajeSoporte(
            emisor_id=current_user.idusuario,
            receptor_id=receptor_id,
            asunto=request.form['asunto'],
            mensaje=request.form['mensaje'],
            leido=False,
            fecha_envio=datetime.now()
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Mensaje enviado exitosamente.', 'success')
        return redirect(url_for('mensaje_soporte.mensajes_soporte'))

    # Obtener lista de posibles receptores según el rol
    if current_user.rol == 'cliente':
        receptores = Users.query.filter(Users.rol.in_(['tecnico', 'admin'])).all()
    elif current_user.rol == 'tecnico':
        receptores = Users.query.filter(Users.rol.in_(['cliente', 'admin'])).all()
    else:  # admin
        receptores = Users.query.filter(Users.idusuario != current_user.idusuario).all()

    return render_template('nuevo_mensaje_soporte.html', receptores=receptores)

@bp.route('/marcar_leido/<int:id>', methods=['POST'])
@login_required
def marcar_leido(id):
    mensaje = MensajeSoporte.query.get_or_404(id)
    if mensaje.receptor_id == current_user.idusuario:
        mensaje.leido = True
        db.session.commit()
        flash('Mensaje marcado como leído.', 'success')
    return redirect(url_for('mensaje_soporte.mensajes_soporte'))
