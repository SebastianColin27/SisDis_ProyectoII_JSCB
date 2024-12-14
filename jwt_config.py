from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from typing import Dict
from fastapi import HTTPException

def dame_token(dato: Dict) -> str:
    """Genera un token JWT con el payload proporcionado."""
    token: str = encode(payload=dato, key='mi_clave', algorithm='HS256')
    return token

def valida_token(token: str) -> Dict:
    """Valida un token JWT y retorna su contenido."""
    try:
        dato: Dict = decode(token, key='mi_clave', algorithms=['HS256'])
        return dato
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
