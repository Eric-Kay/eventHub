from app.db import SessionLocal, Base, engine
from app.models import User
from passlib.context import CryptContext

Base.metadata.create_all(bind=engine)

# IMPORTANT use bcrypt_sha256 (avoids bcrypt length/backend weirdness)
pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto"
)

db = SessionLocal()

users = [
    ("Admin User", "admin@example.com", "admin123", "admin"),
    ("Organizer One", "organizer@example.com", "organizer123", "organizer"),
    ("Customer One", "customer@example.com", "customer123", "customer"),
]

for name,email,password,role in users:
    db.add(
        User(
            name=name,
            email=email,
            password_hash=pwd_context.hash(password),
            role=role
        )
    )

db.commit()
db.close()

print("Seeded users cleanly")