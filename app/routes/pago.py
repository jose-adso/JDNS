from flask import Blueprint, render_template, request, flash, send_file, make_response
from app import db
from app.models.users import Pago, VentaFactura, Carrito, Producto, Users, DetalleVenta
from flask_login import current_user
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io

pago = Blueprint('pago', __name__)

@pago.route('/pago')
def listar_pagos():
    pagos = Pago.query.all()
    return render_template('pago.html', pagos=pagos)

@pago.route('/pago/nuevo', methods=['GET', 'POST'])
def nuevo_pago():
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            numero_tarjeta = request.form['numero_tarjeta']
            fecha_expiracion = request.form['fecha_expiracion']
            cvv = request.form['cvv']
            nombre_titular = request.form['nombre_titular']

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
            db.session.flush()  # Obtener ID de la factura

            # Crear detalles de la venta
            for item in carrito_items:
                producto = Producto.query.get(item.producto_idproducto)
                detalle = DetalleVenta(
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio_unitario,
                    subtotal=item.cantidad * producto.precio_unitario,
                    producto_idproducto=item.producto_idproducto,
                    ventas_factura_idventas_factura=nueva_factura.idventas_factura
                )
                db.session.add(detalle)
                db.session.delete(item)  # Vaciar el carrito después de crear los detalles
            db.session.commit()

            # Crear pago
            nuevo_pago = Pago(
                fecha_pago=fecha_pago,
                monto=monto,
                metodo_pago='tarjeta',
                referencia_pago='',  # Puedes usar número de tarjeta o CVV como referencia, pero no es seguro; usa tokenización real
                estado_pago='completado',
                proveedor_pago='Stripe/PayPal',  # Ajusta según tu integración
                token_transaccion='',  # Genera un token real en producción
                ventas_factura_idventas_factura=nueva_factura.idventas_factura
            )
            db.session.add(nuevo_pago)
            db.session.commit()

            # Generar PDF
            pdf_buffer = generar_factura_pdf(nueva_factura.idventas_factura, monto, 'tarjeta')

            # Descargar PDF
            response = make_response(pdf_buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=factura_{nueva_factura.idventas_factura}.pdf'
            flash("Pago realizado exitosamente. Descargando factura.", "success")
            return response

        except Exception as e:
            db.session.rollback()
            flash(f"Error al procesar el pago: {str(e)}", "danger")
            return render_template('pago_nuevo.html')

    return render_template('pago_nuevo.html')

@pago.route('/pago/<int:id>')
def detalle_pago(id):
    pago = Pago.query.get_or_404(id)
    return render_template('pago_detalle.html', pago=pago)

def generar_factura_pdf(id_factura, monto, metodo_pago):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Encabezado
    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, height - inch, "FACTURA JDNS Comunicaciones")

    # Datos del pago
    c.setFont("Helvetica", 12)
    c.drawString(inch, height - 2*inch, f"Factura ID: {id_factura}")
    c.drawString(inch, height - 2.5*inch, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawString(inch, height - 3*inch, f"Método de Pago: {metodo_pago}")
    c.drawString(inch, height - 3.5*inch, f"Monto: ${monto:.2f}")

    # Pie de página
    c.drawString(inch, inch, "Gracias por su compra en JDNS Comunicaciones")

    c.save()
    buffer.seek(0)
    return buffer