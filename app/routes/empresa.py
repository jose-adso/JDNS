from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.users import Empresa  # Importamos Empresa desde users.py

bp = Blueprint('empresa', __name__, url_prefix='/empresas')

@bp.route('/')
@login_required
def listar():
    empresas = Empresa.query.all()
    return render_template('empresas.html', empresas=empresas)

@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def crear():
    if current_user.rol != 'admin':
        flash('No tienes permiso para crear empresas.', 'danger')
        return redirect(url_for('empresa.listar'))
    
    if request.method == 'POST':
        razon_social = request.form['razon_social'].strip()
        telefono = request.form['telefono'].strip()
        correo = request.form['correo'].strip()
        direccion = request.form['direccion'].strip()

        
        if Empresa.query.filter_by(correo=correo).first():
            flash('El correo ya está registrado. Por favor usa otro.', 'danger')
            return redirect(url_for('empresa.crear'))

        nueva_empresa = Empresa(
            razon_social=razon_social,
            telefono=telefono,
            correo=correo,
            direccion=direccion
        )
        db.session.add(nueva_empresa)
        db.session.commit()
        flash('Empresa creada exitosamente.', 'success')
        return redirect(url_for('empresa.listar'))
    
    return render_template('empresa_nueva.html')

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    if current_user.rol != 'admin':
        flash('No tienes permiso para editar empresas.', 'danger')
        return redirect(url_for('empresa.listar'))
    
    empresa = Empresa.query.get_or_404(id)
    
    if request.method == 'POST':
        razon_social = request.form['razon_social'].strip()
        telefono = request.form['telefono'].strip()
        correo = request.form['correo'].strip()
        direccion = request.form['direccion'].strip()

        # Validar que el correo no esté en uso por otra empresa
        existing_empresa = Empresa.query.filter_by(correo=correo).first()
        if existing_empresa and existing_empresa.idempresa != empresa.idempresa:
            flash('El correo ya está registrado por otra empresa.', 'danger')
            return redirect(url_for('empresa.editar', id=id))

        empresa.razon_social = razon_social
        empresa.telefono = telefono
        empresa.correo = correo
        empresa.direccion = direccion
        db.session.commit()
        flash('Empresa actualizada exitosamente.', 'success')
        return redirect(url_for('empresa.listar'))
    
    return render_template('empresa_editar.html', empresa=empresa)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    if current_user.rol != 'admin':
        flash('No tienes permiso para eliminar empresas.', 'danger')
        return redirect(url_for('empresa.listar'))
    
    empresa = Empresa.query.get_or_404(id)
    db.session.delete(empresa)
    db.session.commit()
    flash('Empresa eliminada exitosamente.', 'success')
    return redirect(url_for('empresa.listar'))