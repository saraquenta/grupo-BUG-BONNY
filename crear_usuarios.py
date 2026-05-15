import sys
import os
import bcrypt

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

USUARIOS = [
    {"username": "admin",         "email": "admin@eamedical.com",      "full_name": "Administrador General",       "password": "admin123", "role": "admin",      "phone": None},
    {"username": "katerin.quenta","email": "katerin@eamedical.com",    "full_name": "Katerin Sara Quenta Ticona",  "password": "admin123", "role": "admin",      "phone": "591-71234001"},
    {"username": "supervisor",    "email": "supervisor@eamedical.com", "full_name": "Supervisor de Inventario",    "password": "super123", "role": "supervisor", "phone": None},
    {"username": "jayu.mendoza",  "email": "jayu@eamedical.com",       "full_name": "Jayu Tomas Mendoza Amaru",   "password": "super123", "role": "supervisor", "phone": "591-71234002"},
    {"username": "almacenero",    "email": "almacenero@eamedical.com", "full_name": "Almacenero de Prueba",        "password": "alma123",  "role": "almacenero", "phone": None},
    {"username": "adiel.pabon",   "email": "adiel@eamedical.com",      "full_name": "Adiel Noel Pabon Nina",       "password": "alma123",  "role": "almacenero", "phone": "591-71234003"},
    {"username": "eric.luna",     "email": "eric@eamedical.com",       "full_name": "Eric Mauricio Luna Pinto",    "password": "alma123",  "role": "almacenero", "phone": "591-71234004"},
]

def main():
    db = SessionLocal()
    try:
        count = db.query(User).count()
        if count > 0:
            print(f"Ya existen {count} usuarios.")
            resp = input("Borrarlos y recrearlos? (s/n): ").strip().lower()
            if resp != "s":
                print("Cancelado.")
                return
            db.query(User).delete()
            db.commit()
            print("Usuarios anteriores eliminados.\n")

        print("Creando usuarios...\n")
        for data in USUARIOS:
            hashed = hash_password(data["password"])
            user = User(
                username=data["username"], email=data["email"],
                full_name=data["full_name"], hashed_password=hashed,
                role=data["role"], phone=data["phone"], is_active=True,
            )
            db.add(user)
            print(f"  OK {data['role']:12} | {data['username']:20} | pass: {data['password']}")

        db.commit()
        print("\nUsuarios creados correctamente!")
        print(f"\n  {'Usuario':<20} {'Contrasena':<12} Rol")
        for u in USUARIOS:
            print(f"  {u['username']:<20} {u['password']:<12} {u['role']}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()