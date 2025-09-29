from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.users import Users
from sqlalchemy import func
import smtplib
import ssl
import random
import string
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
                # Verificar si necesita cambiar contraseña
                from flask import session
                if session.get('reset_user_id') == user.idusuario:
                    session.pop('reset_user_id', None)
                    temp_pass = session.pop('temp_password', None)
                    return redirect(url_for('auth.change_password'))
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
        # pasar lista de productos para que el panel de ventas físicas pueda listarlos
        from app.models.users import Producto
        productos = Producto.query.all()
        return render_template('admin.html', total_usuarios=50, total_bd=3, accesos_ultimos=12, productos=productos)
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





@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        correo = request.form['correo'].strip()
        user = Users.query.filter_by(correo=correo).first()
        if not user:
            flash('Correo no encontrado.', 'danger')
            return redirect(url_for('auth.reset_password'))

        # Generar nueva contraseña temporal
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        hashed_temp = generate_password_hash(temp_password)
        user.password = hashed_temp
        db.session.commit()

        # Almacenar en session para el cambio
        from flask import session
        session['reset_user_id'] = user.idusuario
        session['temp_password'] = temp_password

        # Enviar email
        try:
            smtp_server = "smtp.gmail.com"
            port = 587
            sender_email = "joserojas201890@gmail.com"
            password = os.environ.get('GMAIL_APP_PASSWORD', 'ccnctaiecoeeuxae')

            print(f"Enviando email a: {correo}")
            print(f"Usando servidor: {smtp_server}:{port}")
            print(f"Remitente: {sender_email}")

            with smtplib.SMTP(smtp_server, 587) as server:
                print("Conectando a servidor SMTP...")
                server.starttls()
                server.login(sender_email, password)
                print("Login exitoso")
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = correo
                msg['Subject'] = 'Contraseña Temporal - JDNS Comunicaciones'

                body = f"""Hola {user.nombre},

Tu contraseña temporal es: {temp_password}

Por favor, inicia sesión con esta contraseña y cámbiala inmediatamente por una nueva.

Saludos,
Equipo de JDNS Comunicaciones
"""
                msg.attach(MIMEText(body, 'plain'))

                server.sendmail(sender_email, correo, msg.as_string())
                print("Email enviado exitosamente")

            flash('Contraseña temporal enviada a tu correo. Inicia sesión y cambia tu contraseña.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            print(f"Error enviando email: {e}")
            # Fallback: mostrar la contraseña en flash
            flash(f'Error enviando email. Tu contraseña temporal es: {temp_password}. Inicia sesión y cambia tu contraseña.', 'warning')
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html')

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Las nuevas contraseñas no coinciden.', 'danger')
            return redirect(url_for('auth.change_password'))

        if len(new_password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return redirect(url_for('auth.change_password'))

        hashed_password = generate_password_hash(new_password)
        current_user.password = hashed_password
        db.session.commit()

        flash('Contraseña cambiada exitosamente.', 'success')
        return redirect(url_for('auth.dashboard'))

    return render_template('change_password.html')

@bp.route('/usuarios')
@login_required
def listar_usuarios():
    usuarios = Users.query.all()
    return render_template('usuarios.html', usuarios=usuarios)
