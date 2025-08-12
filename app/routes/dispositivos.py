from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.users import Dispositivo, Users

bp = Blueprint('dispositivo', __name__)

@bp.route('/dispositivo')
def listar_dispositivos():
    dispositivos = Dispositivo.query.all()
    return render_template('dispositivo.html', dispositivos=dispositivos)

@bp.route('/dispositivo/nuevo', methods=['GET', 'POST'])
def nuevo_dispositivo():
    if request.method == 'POST':
        nuevo_dispositivo = Dispositivo(
            marca=request.form['marca'],
            color=request.form['color'],
            imei=request.form['imei'],
            problema=request.form['problema'],
            usuario_idusuario=request.form['usuario_idusuario']
        )
        db.session.add(nuevo_dispositivo)
        db.session.commit()
        return redirect(url_for('dispositivo.listar_dispositivos'))
    usuarios = Users.query.all()
    return render_template('dispositivo_nuevo.html', usuarios=usuarios)

@bp.route('/dispositivo/<int:id>')
def detalle_dispositivo(id):
    dispositivo = Dispositivo.query.get_or_404(id)
    return render_template('dispositivo_detalle.html', dispositivo=dispositivo)