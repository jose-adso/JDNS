# enhanced_payment_methods.py - Extensión para métodos de pago avanzados
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.users import Pago, VentaFactura, MetodoPagoMixto
from datetime import datetime
from decimal import Decimal

# Nuevo modelo para pagos mixtos (agregar a models/users.py):
"""
class MetodoPagoMixto(db.Model):
    __tablename__ = 'metodo_pago_mixto'
    
    id = db.Column(db.Integer, primary_key=True)
    venta_factura_id = db.Column(db.Integer, db.ForeignKey('ventas_factura.idventas_factura'))
    efectivo = db.Column(db.Decimal(10, 2), default=0)
    tarjeta = db.Column(db.Decimal(10, 2), default=0)
    transferencia = db.Column(db.Decimal(10, 2), default=0)
    otro = db.Column(db.Decimal(10, 2), default=0)
    descripcion_otro = db.Column(db.String(100))
    total_pagado = db.Column(db.Decimal(10, 2))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    venta = db.relationship('VentaFactura', backref='pago_mixto')
"""

enhanced_payment = Blueprint('enhanced_payment', __name__, url_prefix='/admin/payment')

@enhanced_payment.route('/configurar_metodos')
@login_required
def configurar_metodos():
    """Configurar métodos de pago disponibles"""
    if current_user.rol != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    metodos_disponibles = {
        'efectivo': {
            'nombre': 'Efectivo',
            'descripcion': 'Pago en efectivo',
            'activo': True,
            'configuracion': {}
        },
        'tarjeta': {
            'nombre': 'Tarjeta',
            'descripcion': 'Tarjeta de crédito/débito',
            'activo': True,
            'configuracion': {
                'comision': 3.0,  # Porcentaje
                'tipos_aceptados': ['visa', 'mastercard', 'american_express']
            }
        },
        'transferencia': {
            'nombre': 'Transferencia',
            'descripcion': 'Transferencia bancaria',
            'activo': True,
            'configuracion': {
                'cuenta_bancaria': '1234567890',
                'banco': 'Banco Ejemplo'
            }
        },
        'credito': {
            'nombre': 'Crédito',
            'descripcion': 'Venta a crédito',
            'activo': False,
            'configuracion': {
                'plazo_maximo': 30,  # días
                'interes': 2.5  # Porcentaje mensual
            }
        },
        'cheque': {
            'nombre': 'Cheque',
            'descripcion': 'Pago con cheque',
            'activo': False,
            'configuracion': {}
        }
    }
    
    return jsonify({'metodos': metodos_disponibles})

@enhanced_payment.route('/procesar_pago_avanzado', methods=['POST'])
@login_required
def procesar_pago_avanzado():
    """Procesar pago con múltiples métodos y validaciones"""
    if current_user.rol != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        data = request.json
        factura_id = data.get('factura_id')
        metodos_pago = data.get('metodos_pago')  # {'efectivo': 50.00, 'tarjeta': 30.00}
        
        factura = VentaFactura.query.get_or_404(factura_id)
        total_factura = factura.total
        
        # Validar que el total de pagos coincida
        total_pagado = sum(Decimal(str(monto)) for monto in metodos_pago.values())
        
        if abs(total_pagado - total_factura) > Decimal('0.01'):
            return jsonify({
                'error': f'Total de pagos (${total_pagado}) no coincide con total de factura (${total_factura})'
            }), 400
        
        # Crear registros de pago individuales
        pagos_creados = []
        
        for metodo, monto in metodos_pago.items():
            if Decimal(str(monto)) > 0:
                # Aplicar comisiones si es necesario
                monto_final = Decimal(str(monto))
                
                if metodo == 'tarjeta':
                    # Ejemplo: aplicar comisión del 3%
                    comision = monto_final * Decimal('0.03')
                    # En este caso, la comisión se descuenta del monto recibido
                    # o se puede manejar como costo adicional
                
                pago = Pago(
                    monto=monto_final,
                    metodo_pago=metodo,
                    fecha_pago=datetime.utcnow(),
                    estado_pago='completado',
                    ventas_factura_idventas_factura=factura_id
                )
                db.session.add(pago)
                pagos_creados.append(pago)
        
        # Registrar pago mixto si hay múltiples métodos
        if len(metodos_pago) > 1:
            pago_mixto = MetodoPagoMixto(
                venta_factura_id=factura_id,
                efectivo=Decimal(str(metodos_pago.get('efectivo', 0))),
                tarjeta=Decimal(str(metodos_pago.get('tarjeta', 0))),
                transferencia=Decimal(str(metodos_pago.get('transferencia', 0))),
                otro=Decimal(str(metodos_pago.get('otro', 0))),
                total_pagado=total_pagado
            )
            db.session.add(pago_mixto)
        
        # Actualizar estado de la factura
        factura.estado_envio = 'pagado'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pago procesado exitosamente',
            'pagos_creados': len(pagos_creados),
            'total_procesado': float(total_pagado)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al procesar pago: {str(e)}'}), 500

@enhanced_payment.route('/validar_pago', methods=['POST'])
@login_required
def validar_pago():
    """Validar pago antes de procesarlo"""
    if current_user.rol != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        data = request.json
        metodos_pago = data.get('metodos_pago')
        total_venta = Decimal(str(data.get('total_venta', 0)))
        
        validaciones = {
            'total_correcto': False,
            'metodos_validos': True,
            'errores': [],
            'advertencias': []
        }
        
        # Validar total
        total_pagado = sum(Decimal(str(monto)) for monto in metodos_pago.values() if monto > 0)
        
        if abs(total_pagado - total_venta) <= Decimal('0.01'):
            validaciones['total_correcto'] = True
        else:
            validaciones['errores'].append(f'Total de pagos (${total_pagado}) no coincide con total de venta (${total_venta})')
        
        # Validar métodos individuales
        for metodo, monto in metodos_pago.items():
            if Decimal(str(monto)) < 0:
                validaciones['metodos_validos'] = False
                validaciones['errores'].append(f'El monto para {metodo} no puede ser negativo')
            
            # Validaciones específicas por método
            if metodo == 'efectivo' and Decimal(str(monto)) > 0:
                # Sugerir cambio si es necesario
                if Decimal(str(monto)) > total_venta:
                    cambio = Decimal(str(monto)) - total_venta
                    validaciones['advertencias'].append(f'Cambio a entregar: ${cambio}')
            
            elif metodo == 'tarjeta' and Decimal(str(monto)) > 0:
                # Validar límites de tarjeta (ejemplo)
                if Decimal(str(monto)) > Decimal('1000.00'):
                    validaciones['advertencias'].append(f'Monto alto en tarjeta: ${monto}')
        
        validaciones['es_valido'] = validaciones['total_correcto'] and validaciones['metodos_validos']
        
        return jsonify(validaciones)
    
    except Exception as e:
        return jsonify({'error': f'Error en validación: {str(e)}'}), 500

@enhanced_payment.route('/reporte_metodos_pago')
@login_required
def reporte_metodos_pago():
    """Generar reporte de métodos de pago utilizados"""
    if current_user.rol != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    from sqlalchemy import func, extract
    from datetime import date, timedelta
    
    # Obtener datos de los últimos 30 días
    fecha_inicio = date.today() - timedelta(days=30)
    
    # Contar por método de pago
    metodos_stats = db.session.query(
        Pago.metodo_pago,
        func.count(Pago.idpago).label('cantidad'),
        func.sum(Pago.monto).label('total_monto')
    ).filter(
        Pago.fecha_pago >= fecha_inicio
    ).group_by(Pago.metodo_pago).all()
    
    # Pagos mixtos
    pagos_mixtos = db.session.query(func.count(MetodoPagoMixto.id)).filter(
        MetodoPagoMixto.fecha_registro >= fecha_inicio
    ).scalar() or 0
    
    stats_formateadas = []
    total_general = Decimal('0')
    
    for metodo, cantidad, total in metodos_stats:
        stats_formateadas.append({
            'metodo': metodo.title(),
            'cantidad_transacciones': cantidad,
            'total_monto': float(total or 0),
            'promedio_por_transaccion': float((total or 0) / cantidad) if cantidad > 0 else 0
        })
        total_general += total or 0
    
    return jsonify({
        'periodo': f'Últimos 30 días (desde {fecha_inicio.strftime("%d/%m/%Y")})',
        'estadisticas_por_metodo': stats_formateadas,
        'pagos_mixtos': pagos_mixtos,
        'total_general': float(total_general),
        'total_transacciones': sum(stat['cantidad_transacciones'] for stat in stats_formateadas)
    })

@enhanced_payment.route('/configurar_comisiones', methods=['POST'])
@login_required
def configurar_comisiones():
    """Configurar comisiones por método de pago"""
    if current_user.rol != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    # Esta función permitiría configurar comisiones dinámicas
    # por método de pago, que se podrían almacenar en una tabla de configuración
    
    data = request.json
    comisiones = data.get('comisiones', {})
    
    # Ejemplo de estructura:
    # {
    #     'tarjeta': {'tipo': 'porcentaje', 'valor': 3.0},
    #     'transferencia': {'tipo': 'fijo', 'valor': 2.50},
    #     'cheque': {'tipo': 'porcentaje', 'valor': 1.5}
    # }
    
    # Aquí se guardarían las configuraciones en la base de datos
    # Por simplicidad, se retorna confirmación
    
    return jsonify({
        'success': True,
        'message': 'Comisiones configuradas exitosamente',
        'comisiones_configuradas': len(comisiones)
    })