import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from app import db
from app.models.users import AdjuntoReparacion
from app.models.users import Reparacion
from flask_login import login_required
from werkzeug.utils import secure_filename
from datetime import datetime

bp_adj = Blueprint('adjunto_reparacion', __name__, url_prefix='/adjunto_reparacion')

@bp_adj.route('/')
@login_required
def listar():
    adjuntos = AdjuntoReparacion.query.all()
    return render_template('adjunto_reparacion_list.html', adjuntos=adjuntos)

@bp_adj.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    reparaciones = Reparacion.query.all()
    if request.method == 'POST':
        reparacion_id = int(request.form['reparacion_id'])
        descripcion = request.form['descripcion']
        archivo = request.files['archivo']
        fecha_subida = datetime.now()
        if archivo:
            nombre_archivo = secure_filename(archivo.filename)
            ruta = os.path.join(current_app.config['UPLOAD_FOLDER'], nombre_archivo)
            archivo.save(ruta)
            ruta_relativa = os.path.join('uploads', nombre_archivo)
            adj = AdjuntoReparacion(
                reparacion_idreparacion=reparacion_id,
                ruta_archivo=ruta_relativa,
                descripcion=descripcion,
                fecha_subida=fecha_subida
            )
            db.session.add(adj)
            db.session.commit()
            flash('Archivo adjuntado con éxito', 'success')
            return redirect(url_for('adjunto_reparacion.listar'))
        else:
            flash('Debe seleccionar un archivo', 'danger')

    return render_template('adjunto_reparacion_nuevo.html', reparaciones=reparaciones)
