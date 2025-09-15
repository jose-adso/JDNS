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
@pago.route('/pago/nuevo', methods=['GET'])
@login_required
def pago_nuevo():
    return render_template("pago_nuevo.html")


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

        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elementos = []
        styles = getSampleStyleSheet()

        
        try:
            
            logo_path = os.path.join(current_app.static_folder, 'logo.png')
            logo_path = os.path.abspath(logo_path)
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=100, height=60)  # ajusta tamaño según tu logo
                elementos.append(logo)
            else:
                elementos.append(Paragraph("<b>[Logo no encontrado]</b>", styles["Normal"]))
        except Exception:
            elementos.append(Paragraph("<b>[Logo no encontrado]</b>", styles["Normal"]))

        # Sección Empresa
        elementos.append(Spacer(1, 12))
        elementos.append(Paragraph("<b>EMPRESA:</b>", styles["Heading2"]))
        elementos.append(Paragraph("Nombre: JDNS Comunicaciones", styles["Normal"]))
        elementos.append(Paragraph("NIT: 1101755776-0", styles["Normal"]))
        elementos.append(Paragraph("Teléfono: +57 300 123 4567", styles["Normal"]))
        elementos.append(Paragraph("Dirección: Carrera 2 4 30, Vélez, Santander", styles["Normal"]))
        elementos.append(Paragraph("Correo: info@jdnscomunicaciones.com", styles["Normal"]))
        elementos.append(Spacer(1, 12))

        # Sección Cliente
        elementos.append(Paragraph("<b>CLIENTE:</b>", styles["Heading2"]))
        elementos.append(Paragraph(f"Nombre: {current_user.nombre}", styles["Normal"]))
        elementos.append(Paragraph(f"Correo: {current_user.correo or 'N/A'}", styles["Normal"]))
        elementos.append(Paragraph(f"Teléfono: {current_user.telefono or 'N/A'}", styles["Normal"]))
        elementos.append(Paragraph(f"Dirección: {current_user.direccion or 'N/A'}", styles["Normal"]))
        elementos.append(Spacer(1, 12))

        
        elementos.append(Paragraph(f"Fecha: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
        elementos.append(Spacer(1, 20))

        
        data = [["Producto", "Cantidad", "P. Unitario", "Subtotal"]]

        
        for item in productos_factura:
            precio_sin_iva = Decimal(str(item.producto.precio_unitario)) * Decimal('0.81')
            subtotal_sin_iva = Decimal(str(item.cantidad)) * precio_sin_iva
            data.append([
                item.producto.nombre,
                str(item.cantidad),
                f"${precio_sin_iva:.2f}",
                f"${subtotal_sin_iva:.2f}"
            ])

        
        # Calcular subtotal sin IVA (total * 0.81), IVA 19% (total * 0.19), total final
        subtotal = total * Decimal('0.81')
        iva = total * Decimal('0.19')
        total_final = total

        data.append(["", "", "Subtotal:", f"${subtotal}"])
        data.append(["", "", "IVA 19%:", f"${iva}"])
        data.append(["", "", "<b>Total:</b>", f"${total_final}"])

        
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
    
@pago.route('/admin/pedidos')
@login_required
def listar_pedidos():
    from app.models.users import VentaFactura
    pedidos = VentaFactura.query.filter_by(tipo_venta="online").all()
    return render_template("admin_compras_onlin.html", pedidos=pedidos)


@pago.route('/pagos/factura/<int:factura_id>')
@login_required
def descargar_factura(factura_id):
    factura = VentaFactura.query.get_or_404(factura_id)
    if current_user.rol != 'admin' and factura.usuario_idusuario != current_user.idusuario:
        flash("No tienes permiso para ver esta factura", "danger")
        return redirect(url_for('pago.listar_pedidos'))

    detalles = DetalleVenta.query.filter_by(ventas_factura_idventas_factura=factura_id).all()
    usuario = factura.usuario  # Asegúrate de tener relación a usuario desde VentaFactura

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elementos = []
    styles = getSampleStyleSheet()

    
    try:
        logo_path = os.path.join(current_app.static_folder, 'logo.png')
        logo_path = os.path.abspath(logo_path)
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=100, height=60)
            elementos.append(logo)
        else:
            elementos.append(Paragraph("[Logo no encontrado]", styles["Normal"]))
    except Exception:
        elementos.append(Paragraph("[Logo no encontrado]", styles["Normal"]))

    # Sección Empresa
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("<b>EMPRESA:</b>", styles["Heading2"]))
    elementos.append(Paragraph("Nombre: JDNS Comunicaciones", styles["Normal"]))
    elementos.append(Paragraph("NIT: 1101755776-0", styles["Normal"]))
    elementos.append(Paragraph("Teléfono: +57 300 123 4567", styles["Normal"]))
    elementos.append(Paragraph("Dirección: Carrera 2 4 30, Vélez, Santander", styles["Normal"]))
    elementos.append(Paragraph("Correo: info@jdnscomunicaciones.com", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    # Sección Cliente
    elementos.append(Paragraph("<b>CLIENTE:</b>", styles["Heading2"]))
    elementos.append(Paragraph(f"Nombre: {usuario.nombre}", styles["Normal"]))
    elementos.append(Paragraph(f"Correo: {usuario.correo or 'N/A'}", styles["Normal"]))
    elementos.append(Paragraph(f"Teléfono: {usuario.telefono or 'N/A'}", styles["Normal"]))
    elementos.append(Paragraph(f"Dirección: {usuario.direccion or 'N/A'}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"Fecha: {factura.fecha_venta.strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elementos.append(Spacer(1, 20))

    data = [["Producto", "Cantidad", "P. Unitario", "Subtotal"]]
    for det in detalles:
        
        precio_sin_iva = float(det.precio_unitario) * 0.81
        subtotal_sin_iva = float(det.cantidad) * precio_sin_iva
        data.append([
            det.producto.nombre,
            str(det.cantidad),
            f"${precio_sin_iva:,.2f}",
            f"${subtotal_sin_iva:,.2f}"
        ])
    # Calcular subtotal sin IVA (factura.total * 0.81), IVA 19% (factura.total * 0.19), total final
    subtotal = Decimal(str(factura.total)) * Decimal('0.81')
    iva = Decimal(str(factura.total)) * Decimal('0.19')
    total_final = factura.total

    data.append(["", "", "Subtotal:", f"${subtotal}"])
    data.append(["", "", "IVA 19%:", f"${iva}"])
    data.append(["", "", "<b>Total:</b>", f"${total_final}"])

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
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"factura_{factura.idventas_factura}.pdf",
        mimetype="application/pdf"
    )


@pago.route('/admin/pedidos/<int:id_factura>/estado', methods=['POST'])
@login_required
def cambiar_estado_pedido(id_factura):
    from app.models.users import VentaFactura
    nuevo_estado = request.form.get("estado")  # pendiente, pagado o anulado

    factura = VentaFactura.query.get_or_404(id_factura)

    if nuevo_estado not in ["pendiente", "pagado", "anulado"]:
        flash("Estado inválido", "danger")
        return redirect(url_for("pago.listar_pedidos"))

    factura.estado_envio = nuevo_estado
    # Crear notificación automática al usuario
    try:
        from app.models.users import Notificacion
        mensaje = f"El estado de su pedido #{factura.idventas_factura} ha cambiado a {nuevo_estado}."
        noti = Notificacion(usuario_idusuario=factura.usuario_idusuario, tipo='pedido', mensaje=mensaje, leida=False, fecha_envio=datetime.now())
        db.session.add(noti)
    except Exception:
        pass
    db.session.commit()
    flash(f"Pedido #{factura.idventas_factura} actualizado a {nuevo_estado}", "success")
    return redirect(url_for("pago.listar_pedidos"))


