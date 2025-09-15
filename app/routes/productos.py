from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.users import Producto, Empresa, Users
import os
from werkzeug.utils import secure_filename

bp = Blueprint('producto', __name__, url_prefix='/productos')

UPLOAD_FOLDER = 'app/static/images/productos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/', endpoint='listar_productos')
@login_required
def listar_productos():
    productos = Producto.query.all()
    empresas = Empresa.query.all()
    if current_user.rol == 'admin':
        return render_template('productos.html', productos=productos, empresas=empresas)
    elif current_user.rol == 'cliente':
        return render_template('plantilla.html', productos=productos, empresas=empresas)
    elif current_user.rol == 'tecnico':
        return render_template('productos.html', productos=productos, empresas=empresas, use_carousel=True)
    else:
        return "No tienes permiso para ver esta página", 403
    
@bp.route('/',endpoint='listar')
@login_required
def listar():
    productos = Producto.query.all()
    empresas = Empresa.query.all()  # Añadimos la consulta de empresas
    return render_template('productos.html', productos=productos, empresas=empresas)
    

@bp.route('/carrusel', endpoint='listar_carrusel')
@login_required
def listar_carrusel():
    productos = Producto.query.all()
    empresas = Empresa.query.all()
    return render_template('plantilla.html', productos=productos, empresas=empresas, use_carousel=True)

@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def crear():
    if current_user.rol != 'admin':
        flash('No tienes permiso para crear productos.', 'danger')
        return redirect(url_for('producto.listar_productos'))
    
    empresas = Empresa.query.all()  
    if not empresas:
        flash('No hay empresas registradas. Crea una empresa primero.', 'danger')
        return redirect(url_for('empresa.crear'))

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        descripcion = request.form['descripcion'].strip()
        tipo = request.form['tipo']
        precio_unitario = request.form['precio_unitario']
        stock = request.form['stock']
        empresa_idempresa = request.form['empresa_idempresa']

        if tipo not in ['repuesto', 'accesorio', 'telefonos', 'computadores']:
            flash('Tipo de producto no válido.', 'danger')
            return redirect(url_for('producto.crear'))
        
        try:
            precio_unitario = float(precio_unitario)
            stock = int(stock)
            empresa_idempresa = int(empresa_idempresa)
        except ValueError:
            flash('Precio unitario y stock deben ser numéricos.', 'danger')
            return redirect(url_for('producto.crear'))

        if precio_unitario < 0 or stock < 0:
            flash('Precio unitario y stock no pueden ser negativos.', 'danger')
            return redirect(url_for('producto.crear'))

        empresa = Empresa.query.get(empresa_idempresa)
        if not empresa:
            flash('Empresa no encontrada.', 'danger')
            return redirect(url_for('producto.crear'))

        nuevo_producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            tipo=tipo,
            precio_unitario=precio_unitario,
            stock=stock,
            imagen='',  # Inicializamos el campo imagen
            empresa_idempresa=empresa_idempresa
        )
        db.session.add(nuevo_producto)
        db.session.flush()  # Para obtener el idproducto antes de commit
        db.session.commit()

       
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                filename = secure_filename(f"{nuevo_producto.idproducto}.jpg")
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                nuevo_producto.imagen = f"images/productos/{filename}"  # Guardamos la ruta relativa
                db.session.commit()
                flash('Producto y imagen creados exitosamente.', 'success')
            else:
                flash('Tipo de archivo no permitido. Usa imágenes (png, jpg, jpeg, gif).', 'danger')
        else:
            flash('Producto creado exitosamente, pero no se subió ninguna imagen.', 'info')

        return redirect(url_for('producto.listar_productos'))
    
    return render_template('producto_nuevo.html', empresas=empresas)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    if current_user.rol != 'admin':
        flash('No tienes permiso para editar productos.', 'danger')
        return redirect(url_for('producto.listar_productos'))
    
    producto = Producto.query.get_or_404(id)
    empresas = Empresa.query.all()
    if not empresas:
        flash('No hay empresas registradas. Crea una empresa primero.', 'danger')
        return redirect(url_for('empresa.crear'))

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        descripcion = request.form['descripcion'].strip()
        tipo = request.form['tipo']
        precio_unitario = request.form['precio_unitario']
        stock = request.form['stock']
        empresa_idempresa = request.form['empresa_idempresa']

        if tipo not in ['repuesto', 'accesorio', 'telefonos', 'computadores']:
            flash('Tipo de producto no válido.', 'danger')
            return redirect(url_for('producto.editar', id=id))
        
        try:
            precio_unitario = float(precio_unitario)
            stock = int(stock)
            empresa_idempresa = int(empresa_idempresa)
        except ValueError:
            flash('Precio unitario y stock deben ser numéricos.', 'danger')
            return redirect(url_for('producto.editar', id=id))

        if precio_unitario < 0 or stock < 0:
            flash('Precio unitario y stock no pueden ser negativos.', 'danger')
            return redirect(url_for('producto.editar', id=id))

        empresa = Empresa.query.get(empresa_idempresa)
        if not empresa:
           flash('Empresa no encontrada.', 'danger')
           return redirect(url_for('producto.editar', id=id))

        producto.nombre = nombre
        producto.descripcion = descripcion
        producto.tipo = tipo
        producto.precio_unitario = precio_unitario
        producto.stock = stock
        producto.empresa_idempresa = empresa_idempresa
        db.session.commit()

        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                filename = secure_filename(f"{producto.idproducto}.jpg")
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                producto.imagen = f"images/productos/{filename}"
                db.session.commit()
                flash('Producto y imagen actualizados exitosamente.', 'success')
            else:
                flash('Tipo de archivo no permitido. Usa imágenes (png, jpg, jpeg, gif).', 'danger')
        else:
            flash('Producto actualizado exitosamente, pero no se subió ninguna nueva imagen.', 'info')

        return redirect(url_for('producto.listar_productos'))
    
    return render_template('producto_editar.html', producto=producto, empresas=empresas)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    if current_user.rol != 'admin':
        flash('No tienes permiso para eliminar productos.', 'danger')
        return redirect(url_for('producto.listar_productos'))
    
    producto = Producto.query.get_or_404(id)
    
    if producto.imagen:
        image_path = os.path.join(UPLOAD_FOLDER, os.path.basename(producto.imagen))
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado exitosamente.', 'success')
    return redirect(url_for('producto.listar_productos'))