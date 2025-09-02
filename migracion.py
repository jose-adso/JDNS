from app import create_app, db

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE detalle_venta ADD COLUMN subtotal NUMERIC(10,2) NOT NULL DEFAULT 0;"))
        print("✅ Columna 'subtotal' agregada correctamente a detalle_venta")
