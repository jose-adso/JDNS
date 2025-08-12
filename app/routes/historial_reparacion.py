from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.users import HistorialReparacion, Reparacion
from datetime import datetime

bp = Blueprint('historial', __name__)


@bp.route('/historial/<int:reparacion_id>')
def listar_historial(reparacion_id):
    historial = HistorialReparacion.query.filter_by(reparacion_idreparacion=reparacion_id).all()
    reparacion = Reparacion.query.get_or_404(reparacion_id)
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
        return redirect(url_for('historial.listar_historial', reparacion_id=reparacion_id))
    return render_template('historial_nuevo.html', reparacion=reparacion)
