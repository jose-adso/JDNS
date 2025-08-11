from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.users import Pago, VentaFactura

pago = Blueprint('pago', __name__)

@pago.route('/pago')
def listar_pagos():
    pagos = Pago.query.all()
    return render_template('pago.html', pagos=pagos)

@pago.route('/pago/nuevo', methods=['GET', 'POST'])
def nuevo_pago():
    if request.method == 'POST':
        nuevo_pago = Pago(
            fecha_pago=request.form['fecha_pago'],
            monto=request.form['monto'],
            metodo_pago=request.form['metodo_pago'],
            referencia_pago=request.form['referencia_pago'],
            estado_pago=request.form['estado_pago'],
            proveedor_pago=request.form['proveedor_pago'],
            token_transaccion=request.form['token_transaccion'],
            ventas_factura_idventas_factura=request.form['ventas_factura_idventas_factura']
        )
        db.session.add(nuevo_pago)
        db.session.commit()
        return redirect(url_for('pago.listar_pagos'))
    facturas = VentaFactura.query.all()
    return render_template('pago_nuevo.html', facturas=facturas)

@pago.route('/pago/<int:id>')
def detalle_pago(id):
    pago = Pago.query.get_or_404(id)
    return render_template('pago_detalle.html', pago=pago)