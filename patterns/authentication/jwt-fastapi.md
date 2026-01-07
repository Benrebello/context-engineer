---
pattern_id: "auth-jwt-fastapi"
name: "JWT Authentication with FastAPI"
category: "authentication"
stack: ["python", "fastapi"]
complexity: "medium"
tags: ["auth", "jwt", "security", "fastapi"]

dependencies:
 - "python-jose[cryptography]"
 - "passlib[bcrypt]"
 - "python-multipart"

description: |
 Implementa autenticação JWT completa com FastAPI, incluindo:
 - Login com email/senha
 - Geração de tokens JWT
 - Refresh tokens
 - Proteção de rotas

when_to_use:
 - APIs RESTful que precisam de autenticação
 - Aplicações stateless
 - Quando precisa de refresh tokens

when_not_to_use:
 - Aplicações com sessões server-side
 - Quando precisa de revogação imediata de tokens

related_patterns:
 - "auth-oauth2"
 - "auth-session-based"

phases_required:
 - "F2" # Data Model
 - "F3" # API Contracts
 - "F8" # Security

code_examples:
 domain_entity: |
 # src/domain/entities/user.py
 from sqlmodel import SQLModel, Field
 from datetime import datetime
 
 class User(SQLModel, table=True):
 id: int | None = Field(default=None, primary_key=True)
 email: str = Field(unique=True, index=True)
 password_hash: str
 is_active: bool = Field(default=True)
 created_at: datetime = Field(default_factory=datetime.utcnow)
 
 service: |
 # src/application/services/auth_service.py
 from jose import JWTError, jwt
 from passlib.context import CryptContext
 from datetime import datetime, timedelta
 
 pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
 class AuthService:
 def verify_password(self, plain: str, hashed: str) -> bool:
 return pwd_context.verify(plain, hashed)
 
 def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
 to_encode = data.copy()
 if expires_delta:
 expire = datetime.utcnow() + expires_delta
 else:
 expire = datetime.utcnow() + timedelta(minutes=15)
 to_encode.update({"exp": expire})
 return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

integration_steps:
 - step: "Add dependencies to requirements.txt"
 code: "python-jose[cryptography] passlib[bcrypt] python-multipart"
 
 - step: "Create User entity in domain layer"
 file: "src/domain/entities/user.py"
 
 - step: "Create AuthService in application layer"
 file: "src/application/services/auth_service.py"

validation:
 - command: "pytest tests/application/services/test_auth_service.py -v"
 expected: "all tests pass"
 
 - command: "ruff check src/application/services/auth_service.py"
 expected: "no errors"

pitfalls:
 - "Não armazenar senhas em plain text"
 - "Usar SECRET_KEY forte e não commitá-la"
 - "Validar expiração do token em cada request"
 - "Implementar rate limiting no endpoint de login"

