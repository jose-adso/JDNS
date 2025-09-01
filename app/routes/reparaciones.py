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
        nueva_rep = Reparacion(
            fecha_ingreso=datetime.now(),   # ✅ fecha automática
            estado=request.form['estado'],
            problema_reparacion=request.form['problema_reparacion'],
            costo=request.form['costo'],
            fecha_entrega=None,  # ✅ cliente no define entrega, solo técnico/admin
            telefono_idtelefono=None,       # si manejas otra tabla teléfono, aquí se ajusta
            usuario_idusuario=current_user.idusuario,  # ✅ sesión del cliente
            dispositivo_iddispositivo=request.form['dispositivo_iddispositivo']
        )
        db.session.add(nueva_rep)
        db.session.commit()
        return redirect(url_for('reparacion.listar_reparaciones'))

    usuarios = Users.query.all()
    dispositivos = Dispositivo.query.all()
    return render_template('reparacion_nueva.html', usuarios=usuarios, dispositivos=dispositivos)
