from flask import Blueprint, render_template, request, flash, send_file
from app import db
from app.models.users import Pago, VentaFactura, Carrito, Producto, Users, DetalleVenta
from flask_login import current_user
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

pago = Blueprint('pago', __name__)

# ---- RUTA PARA NUEVO PAGO ----
@pago.route('/pago/nuevo', methods=['GET', 'POST'])
def nuevo_pago():
    if request.method == 'POST':
        try:
            # Carrito del usuario
            carrito_items = Carrito.query.filter_by(usuario_idusuario=current_user.idusuario).all()
            if not carrito_items:
                flash("Tu carrito está vacío.", "danger")
                return render_template('pago_nuevo.html')

            # Calcular total
            monto = sum(item.cantidad * Producto.query.get(item.producto_idproducto).precio_unitario for item in carrito_items)
            if monto <= 0:
                flash("El monto debe ser mayor a 0.", "danger")
                return render_template('pago_nuevo.html')

            fecha_pago = datetime.now()

            # Crear factura
            nueva_factura = VentaFactura(
                fecha_venta=fecha_pago,
                total=monto,
                tipo_venta='online',
                estado_envio='pagado',
                usuario_idusuario=current_user.idusuario
            )
            db.session.add(nueva_factura)
            db.session.flush()

            # Crear pago (solo tarjeta, compra online)
            nuevo_pago = Pago(
                fecha_pago=fecha_pago,
                monto=monto,
                metodo_pago='tarjeta',
                referencia_pago='',
                estado_pago='completado',
                proveedor_pago='Pasarela Ficticia',
                token_transaccion='TOKEN-DE-PRUEBA',
                ventas_factura_idventas_factura=nueva_factura.idventas_factura
            )
            db.session.add(nuevo_pago)

            # Guardar detalle de la venta
            for item in carrito_items:
                producto = Producto.query.get(item.producto_idproducto)
                detalle = DetalleVenta(
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio_unitario,
                    producto_idproducto=producto.idproducto,
                    ventas_factura_idventas_factura=nueva_factura.idventas_factura
                )
                db.session.add(detalle)

            # Vaciar carrito
            for item in carrito_items:
                db.session.delete(item)

            db.session.commit()

            # Descargar la factura en PDF directamente
            return factura_pdf(nueva_factura.idventas_factura)

        except Exception as e:
            db.session.rollback()
            flash(f"Error al procesar el pago: {str(e)}", "danger")
            return render_template('pago_nuevo.html')

    return render_template('pago_nuevo.html')


# ---- RUTA PARA GENERAR FACTURA PDF ----
@pago.route('/factura/<int:id>')
def factura_pdf(id):
    factura = VentaFactura.query.get_or_404(id)
    pago = Pago.query.filter_by(ventas_factura_idventas_factura=id).first()
    usuario = Users.query.get(factura.usuario_idusuario)
    detalles = DetalleVenta.query.filter_by(ventas_factura_idventas_factura=id).all()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Encabezado
    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, 750, "FACTURA DE COMPRA")

    # Datos cliente
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Factura ID: {factura.idventas_factura}")
    c.drawString(50, 705, f"Cliente: {usuario.nombre} - {usuario.correo}")
    c.drawString(50, 690, f"Fecha: {factura.fecha_venta.strftime('%Y-%m-%d %H:%M')}")
    c.drawString(50, 675, f"Método de Pago: {pago.metodo_pago}")

    # Encabezado tabla productos
    y = 640
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Producto")
    c.drawString(300, y, "Cantidad")
    c.drawString(400, y, "Precio Unitario")
    c.drawString(500, y, "Subtotal")

    # Listado de productos desde DetalleVenta
    c.setFont("Helvetica", 12)
    y -= 20
    for detalle in detalles:
        producto = Producto.query.get(detalle.producto_idproducto)
        subtotal = float(detalle.precio_unitario) * detalle.cantidad
        c.drawString(50, y, producto.nombre)
        c.drawString(300, y, str(detalle.cantidad))
        c.drawString(400, y, f"${float(detalle.precio_unitario):.2f}")
        c.drawString(500, y, f"${subtotal:.2f}")
        y -= 20

    # Total
    c.setFont("Helvetica-Bold", 14)
    c.drawString(400, y - 10, "TOTAL:")
    c.drawString(500, y - 10, f"${float(factura.total):.2f}")

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,  # <<--- esto hace que se descargue automáticamente
        download_name=f"factura_{factura.idventas_factura}.pdf",
        mimetype='application/pdf'
    )
