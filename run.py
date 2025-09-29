from app import create_app, db
from app.models.users import Users
from werkzeug.security import generate_password_hash
import os

app = create_app()

with app.app_context():
    db.create_all()
    # Crear usuario admin por defecto si no existe
    admin_user = Users.query.filter_by(nombre='joseluis').first()
    if not admin_user:
        hashed_password = generate_password_hash('12345')
        admin_user = Users(
            nombre='joseluis',
            correo='admin@jdns.com',  # Correo por defecto
            telefono='0000000000',  # Teléfono por defecto
            direccion='Admin Address',  # Dirección por defecto
            password=hashed_password,
            rol='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario admin 'joseluis' creado por defecto.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    
  