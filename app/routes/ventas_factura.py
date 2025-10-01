from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.users import VentaFactura, Users
from decimal import Decimal
from datetime import datetime
from flask_login import login_required, current_user
from sqlalchemy import func

bp = Blueprint('ventas_factura', __name__)

@bp.route('/ventas_factura')
def listar_ventas():
    ventas = VentaFactura.query.all()
    return render_template('ventas_factura.html', ventas=ventas)

@bp.route('/ventas_factura/nueva', methods=['GET', 'POST'])
def nueva_venta():
    if request.method == 'POST':
        # convertir tipos: usuario a int y total a Decimal
        usuario_id = int(request.form['usuario_idusuario']) if request.form.get('usuario_idusuario') else None
        total_val = Decimal(str(request.form.get('total', '0')))
        nueva_venta = VentaFactura(
            usuario_idusuario=usuario_id,
            tipo_venta=request.form.get('tipo_venta'),
            estado_envio=request.form.get('estado_envio'),
            total=total_val
        )
        db.session.add(nueva_venta)
        db.session.commit()
        return redirect(url_for('ventas_factura.listar_ventas'))
    usuarios = Users.query.all()
    return render_template('ventas_factura_nueva.html', usuarios=usuarios)

@bp.route('/ventas_factura/<int:id>')
def detalle_venta(id):
    venta = VentaFactura.query.get_or_404(id)
    return render_template('ventas_factura_detalle.html', venta=venta)

@bp.route('/ventas_factura/fisica', methods=['POST'])
def venta_fisica():
    try:
        data = request.json  # Esperamos los productos desde el frontend (JS)
        productos = data.get("productos", [])
        metodo_pago = data.get("metodo_pago", "efectivo")
        if not productos:
            return {"error": "No se enviaron productos"}, 400

        # Resolver cliente: puede venir usuario_idusuario o cliente_nombre
        usuario_id = data.get("usuario_idusuario")
        cliente_nombre = data.get("cliente_nombre")
        cliente_correo = data.get("cliente_correo")
        cliente_telefono = data.get("cliente_telefono")
        cliente_direccion = data.get("cliente_direccion")
        from app.models.users import Users

        if not usuario_id:
            # Verificar si ya existe un usuario con este correo
            if cliente_correo:
                usuario_existente = Users.query.filter_by(correo=cliente_correo).first()
                if usuario_existente:
                    usuario_id = usuario_existente.idusuario
                else:
                    # Crear un nuevo usuario solo si no existe
                    nuevo_usuario = Users(
                        nombre=cliente_nombre or 'Cliente',
                        telefono=cliente_telefono,
                        correo=cliente_correo,
                        direccion=cliente_direccion,
                        password=None,  # Usuario temporal sin contraseña
                        rol='cliente'
                    )
                    db.session.add(nuevo_usuario)
                    db.session.flush()
                    usuario_id = nuevo_usuario.idusuario
            else:
                # Si no hay correo, crear usuario temporal sin validación
                nuevo_usuario = Users(
                    nombre=cliente_nombre or 'Cliente',
                    telefono=cliente_telefono,
                    correo=None,  # Sin correo para evitar conflictos
                    direccion=cliente_direccion,
                    password=None,
                    rol='cliente'
                )
                db.session.add(nuevo_usuario)
                db.session.flush()
                usuario_id = nuevo_usuario.idusuario

        # Crear factura
        # asegurar que total es Decimal
        total_val = Decimal(str(data.get("total", 0)))
        nueva_factura = VentaFactura(
            usuario_idusuario=usuario_id,
            tipo_venta="fisica",
            estado_envio="pagado",
            total=total_val
        )
        db.session.add(nueva_factura)
        db.session.flush()

        # Detalles de la venta
        from app.models.users import DetalleVenta, Producto
        for item in productos:
            prod = Producto.query.get(item["id"])
            if not prod or prod.stock < item["cantidad"]:
                return {"error": f"Stock insuficiente para {prod.nombre if prod else 'producto'}"}, 400
            detalle = DetalleVenta(
                cantidad=item["cantidad"],
                precio_unitario=prod.precio_unitario,
                subtotal=item["cantidad"] * prod.precio_unitario,
                producto_idproducto=prod.idproducto,
                ventas_factura_idventas_factura=nueva_factura.idventas_factura
            )
            prod.stock -= item["cantidad"]  # Descontar stock
            db.session.add(detalle)

        db.session.commit()
        return {"mensaje": "Venta física registrada", "factura_id": nueva_factura.idventas_factura}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500

@bp.route('/estadisticas_ventas')
@login_required
def estadisticas_ventas():
    if current_user.rol != 'admin':
        return redirect(url_for('ventas_factura.listar_ventas'))

    # Total ventas
    total_ventas = db.session.query(func.sum(VentaFactura.total)).scalar() or 0
    total_ventas = float(total_ventas)

    # IVA (19%)
    iva_total = total_ventas * 0.19

    # Ganancias (10%)
    ganancias = total_ventas * 0.10

    # Formatear con puntos como separadores de miles
    def format_currency(value):
        return f"{value:,.0f}".replace(",", ".")

    total_ventas_str = f"$ {format_currency(total_ventas)}"
    iva_total_str = f"$ {format_currency(iva_total)}"
    ganancias_str = f"$ {format_currency(ganancias)}"

    # Ventas semanales (últimas 4 semanas)
    semanal = db.session.query(
        func.strftime('%Y-%W', VentaFactura.fecha_venta).label('semana'),
        func.sum(VentaFactura.total).label('total')
    ).filter(
        VentaFactura.fecha_venta >= func.date('now', '-28 days')
    ).group_by(
        func.strftime('%Y-%W', VentaFactura.fecha_venta)
    ).order_by(
        func.strftime('%Y-%W', VentaFactura.fecha_venta)
    ).all()

    # Ventas mensuales (últimos 12 meses)
    mensual = db.session.query(
        func.strftime('%Y-%m', VentaFactura.fecha_venta).label('mes'),
        func.sum(VentaFactura.total).label('total')
    ).filter(
        VentaFactura.fecha_venta >= func.date('now', '-12 months')
    ).group_by(
        func.strftime('%Y-%m', VentaFactura.fecha_venta)
    ).order_by(
        func.strftime('%Y-%m', VentaFactura.fecha_venta)
    ).all()

    # Preparar datos para Chart.js
    semanas_labels = [f"Semana {s.semana.split('-')[1]}" for s in semanal]
    semanas_data = [float(s.total) for s in semanal]

    meses_labels = [f"{m.mes.split('-')[0]}-{m.mes.split('-')[1]}" for m in mensual]
    meses_data = [float(m.total) for m in mensual]

    return render_template('estadisticas_ventas.html',
                          total_ventas_str=total_ventas_str,
                          iva_total_str=iva_total_str,
                          ganancias_str=ganancias_str,
                          semanas_labels=semanas_labels,
                          semanas_data=semanas_data,
                          meses_labels=meses_labels,
                          meses_data=meses_data)

@bp.route('/ventas_factura/reparacion/<int:id_reparacion>', methods=['POST'])
def facturar_reparacion(id_reparacion):
    try:
        from app.models.users import Reparacion

        reparacion = Reparacion.query.get_or_404(id_reparacion)
        if reparacion.estado != "terminada":
            return {"error": "La reparación aún no está lista"}, 400

        nueva_factura = VentaFactura(
            usuario_idusuario=reparacion.usuario_idusuario,
            tipo_venta="reparacion",
            estado_envio="pagado",
            total=reparacion.costo  # el costo lo dejas solo admin
        )
        db.session.add(nueva_factura)
        db.session.flush()

        # Creamos un detalle con la descripción de reparación
        from app.models.users import DetalleVenta
        detalle = DetalleVenta(
            cantidad=1,
            precio_unitario=reparacion.costo,
            subtotal=reparacion.costo,
            producto_idproducto=None,  # no aplica producto
            ventas_factura_idventas_factura=nueva_factura.idventas_factura
        )
        db.session.add(detalle)

        db.session.commit()
        return {"mensaje": "Factura de reparación generada", "factura_id": nueva_factura.idventas_factura}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500
