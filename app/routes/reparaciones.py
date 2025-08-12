from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.users import Reparacion, Dispositivo, Users
from datetime import datetime

bp = Blueprint('reparacion', __name__)

# Listar reparaciones
@bp.route('/reparaciones')
def listar_reparaciones():
    reparaciones = Reparacion.query.all()
    return render_template('reparaciones.html', reparaciones=reparaciones)

# Crear reparación
@bp.route('/reparaciones/nueva', methods=['GET', 'POST'])
def nueva_reparacion():
    if request.method == 'POST':
        nueva = Reparacion(
            fecha_ingreso=datetime.strptime(request.form['fecha_ingreso'], "%Y-%m-%d"),
            estado=request.form['estado'],
            problema_reparacion=request.form['problema_reparacion'],
            costo=request.form['costo'],
            fecha_entrega=datetime.strptime(request.form['fecha_entrega'], "%Y-%m-%d"),
            telefono_jtelfono=request.form['telefono_jtelfono'],
            usuario_idusuario=request.form['usuario_idusuario'],
            dispositivo_iddispositivo=request.form['dispositivo_iddispositivo']
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('reparacion.listar_reparaciones'))

    dispositivos = Dispositivo.query.all()
    usuarios = Users.query.all()
    return render_template('reparacion_nueva.html', dispositivos=dispositivos, usuarios=usuarios)

# Detalle de reparación
@bp.route('/reparaciones/<int:id>')
def detalle_reparacion(id):
    reparacion = Reparacion.query.get_or_404(id)
    return render_template('reparacion_detalle.html', reparacion=reparacion)
