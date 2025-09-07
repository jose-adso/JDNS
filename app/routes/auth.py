from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.users import Users
from sqlalchemy import func

from app import db  

bp = Blueprint('auth', __name__)

@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        password = request.form['password']
        print(f"Intentando iniciar sesión con nombre: {nombre}")
        user = Users.query.filter(func.lower(Users.nombre) == func.lower(nombre)).first()
        if user:
            print(f"Usuario encontrado: {user.nombre}, hash almacenado: {user.password}")
            if check_password_hash(user.password, password):
                print("¡Contraseña correcta!")
                login_user(user)
                flash("¡Inicio de sesión exitoso!", "success")
                return redirect(url_for('auth.dashboard'))
            else:
                print("La contraseña no coincide.")
                flash('Contraseña incorrecta.', 'danger')
        else:
            print("Usuario no encontrado.")
            flash('Nombre de usuario no encontrado.', 'danger')
    
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return render_template("login.html")

@bp.route('/dashboard')
@login_required
def dashboard():
    print(f"Usuario actual: {current_user.nombre}, Rol: {current_user.rol}")
    if current_user.rol == 'cliente':
        return render_template('cliente.html', fichas_total=10, solicitudes_pendientes=5, instructores_activos=8)
    elif current_user.rol == 'tecnico':
        return render_template('tecnico.html', fichas_asignadas=4, programas_total=2, mensajes_nuevos=1)
    elif current_user.rol == 'admin':
        return render_template('admin.html', total_usuarios=50, total_bd=3, accesos_ultimos=12)
    else:
        return "No tienes permiso para ver este panel", 403

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        correo = request.form['correo']
        telefono = request.form['telefono']
        password = request.form['password']
        direccion = request.form['direccion']

        if Users.query.filter(func.lower(Users.nombre) == func.lower(nombre)).first():
            flash('El nombre de usuario ya existe. Por favor elige otro.', 'danger')
            return redirect(url_for('auth.register_cliente'))

        if Users.query.filter_by(correo=correo).first():
            flash('El correo ya está registrado. Por favor usa otro.', 'danger')
            return redirect(url_for('auth.register_cliente'))

        hashed_password = generate_password_hash(password)
        new_user = Users(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            direccion=direccion,
            password=hashed_password,
            rol='cliente'
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template("register.html")

@bp.route('/register_admin', methods=['GET', 'POST'])
@login_required
def register_admin():
    if current_user.rol != 'admin':
        return "No tienes permiso para acceder a esta página", 403

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()  # Quitamos espacios
        correo = request.form['correo']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        password = request.form['password']
        rol = request.form['rol']

        if rol not in ['tecnico', 'admin']:
            flash('Rol no permitido.', 'danger')
            return redirect(url_for('auth.register_admin'))

        
        if Users.query.filter(func.lower(Users.nombre) == func.lower(nombre)).first():
            flash('El nombre de usuario ya existe. Por favor elige otro.', 'danger')
            return redirect(url_for('auth.register_admin'))
        if Users.query.filter_by(correo=correo).first():
            flash('El correo ya está registrado. Por favor usa otro.', 'danger')
            return redirect(url_for('auth.register_admin'))

        hashed_password = generate_password_hash(password)
        new_user = Users(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            direccion=direccion,
            password=hashed_password,
            rol=rol
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Usuario registrado exitosamente.', 'success')
        return redirect(url_for('auth.dashboard'))
    
    return render_template("register_admin.html")