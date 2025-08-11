from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.users import VentaFactura, Users

ventas_factura = Blueprint('ventas_factura', __name__)

@ventas_factura.route('/ventas_factura')
def listar_ventas():
    ventas = VentaFactura.query.all()
    return render_template('ventas_factura.html', ventas=ventas)

@ventas_factura.route('/ventas_factura/nueva', methods=['GET', 'POST'])
def nueva_venta():
    if request.method == 'POST':
        nueva_venta = VentaFactura(
            usuario_idusuario=request.form['usuario_idusuario'],
            tipo_venta=request.form['tipo_venta'],
            estado_envio=request.form['estado_envio'],
            total=request.form['total']
        )
        db.session.add(nueva_venta)
        db.session.commit()
        return redirect(url_for('ventas_factura.listar_ventas'))
    usuarios = Users.query.all()
    return render_template('ventas_factura_nueva.html', usuarios=usuarios)

@ventas_factura.route('/ventas_factura/<int:id>')
def detalle_venta(id):
    venta = VentaFactura.query.get_or_404(id)
    return render_template('ventas_factura_detalle.html', venta=venta)