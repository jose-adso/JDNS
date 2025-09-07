from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.users import Dispositivo

bp = Blueprint('dispositivo', __name__)

@bp.route('/dispositivo')
@login_required
def listar_dispositivos():

    dispositivos = Dispositivo.query.filter_by(usuario_idusuario=current_user.idusuario).all()
    return render_template('dispositivo.html', dispositivos=dispositivos)

@bp.route('/dispositivo/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_dispositivo():
    if request.method == 'POST':
        nuevo_dispositivo = Dispositivo(
            marca=request.form['marca'],
            color=request.form['color'],
            imei=request.form['imei'],  
            usuario_idusuario=current_user.idusuario  
        )
        db.session.add(nuevo_dispositivo)
        db.session.commit()
        return redirect(url_for('reparacion.nueva_reparacion'))  
    
    return render_template('dispositivo_nuevo.html')
