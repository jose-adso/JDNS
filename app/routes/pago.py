from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models.users import Carrito, Pago, VentaFactura, DetalleVenta
from datetime import datetime
from decimal import Decimal
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

pago = Blueprint('pago', __name__)

# Ruta para mostrar formulario de pago
@pago.route('/pago/nuevo', methods=['GET'])
@login_required
def pago_nuevo():
    return render_template("pago_nuevo.html")


# Ruta para procesar el pago
@pago.route('/pago/nuevo', methods=['POST'])
@login_required
def nuevo_pago():
    try:
        numero_tarjeta = request.form.get("numero_tarjeta")
        fecha_exp = request.form.get("fecha_exp")
        cvv = request.form.get("cvv")
        titular = request.form.get("titular")

        if not numero_tarjeta or not fecha_exp or not cvv or not titular:
            flash("Todos los campos son obligatorios", "danger")
            return redirect(url_for("pago.pago_nuevo"))

        carrito_items = Carrito.query.filter_by(usuario_idusuario=current_user.idusuario).all()
        if not carrito_items:
            flash("Tu carrito está vacío", "warning")
            return redirect(url_for("carrito.ver_carrito"))

        total = sum([Decimal(str(item.cantidad)) * Decimal(str(item.producto.precio_unitario)) for item in carrito_items])

        factura = VentaFactura(
            fecha_venta=datetime.utcnow(),
            total=Decimal(str(total)),
            usuario_idusuario=current_user.idusuario,
            tipo_venta='online',
            estado_envio='pagado'
        )
        db.session.add(factura)
        db.session.flush()

        for item in carrito_items:
            detalle = DetalleVenta(
                cantidad=int(item.cantidad),
                precio_unitario=Decimal(str(item.producto.precio_unitario)),
                subtotal=Decimal(str(item.cantidad)) * Decimal(str(item.producto.precio_unitario)),
                producto_idproducto=item.producto_idproducto,
                ventas_factura_idventas_factura=factura.idventas_factura
            )
            db.session.add(detalle)

        nuevo_pago = Pago(
            monto=Decimal(str(total)),
            metodo_pago="tarjeta",
            fecha_pago=datetime.utcnow(),
            estado_pago="completado",
            ventas_factura_idventas_factura=factura.idventas_factura
        )
        db.session.add(nuevo_pago)

        productos_factura = list(carrito_items)

        for item in carrito_items:
            db.session.delete(item)

        db.session.commit()

        # 📄 Generar factura PDF con logo
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elementos = []
        styles = getSampleStyleSheet()

        # Insertar logo (asegúrate de que la ruta sea correcta)
        try:
            # Usar la carpeta estática de la aplicación para obtener una ruta absoluta confiable
            logo_path = os.path.join(current_app.static_folder, 'logo.png')
            logo_path = os.path.abspath(logo_path)
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=100, height=60)  # ajusta tamaño según tu logo
                elementos.append(logo)
            else:
                elementos.append(Paragraph("<b>[Logo no encontrado]</b>", styles["Normal"]))
        except Exception:
            elementos.append(Paragraph("<b>[Logo no encontrado]</b>", styles["Normal"]))

        # Encabezado empresa
        elementos.append(Paragraph("<b>JDNS Comunicaciones</b>", styles["Title"]))
        elementos.append(Paragraph("NIT: 1101755776-0", styles["Normal"]))
        elementos.append(Paragraph(f"Cliente: {current_user.nombre}", styles["Normal"]))
        elementos.append(Paragraph(f"Fecha: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
        elementos.append(Spacer(1, 20))

        # Encabezado de tabla
        data = [["Producto", "Cantidad", "P. Unitario", "Subtotal"]]

        # Filas con productos
        for item in productos_factura:
            subtotal = Decimal(str(item.cantidad)) * Decimal(str(item.producto.precio_unitario))
            data.append([
                item.producto.nombre,
                str(item.cantidad),
                f"${item.producto.precio_unitario}",
                f"${subtotal}"
            ])

        # Total
        data.append(["", "", "Total:", f"${total}"])

        # Crear tabla estilizada
        tabla = Table(data, colWidths=[200, 80, 100, 100])
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        elementos.append(tabla)
        doc.build(elementos)

        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="factura.pdf", mimetype="application/pdf")

    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar el pago: {str(e)}", "danger")
        return redirect(url_for("pago.pago_nuevo"))
