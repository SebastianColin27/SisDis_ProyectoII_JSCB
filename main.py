#Crear APIs y manejar exepciones
from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException,  Depends, status, Request
#PAquete para trabajar con la estructura de los datos
from fastapi.responses import JSONResponse
from pydantic import BaseModel
#Conexion con MongoDB
from motor import motor_asyncio
from bson import ObjectId
from pymongo import MongoClient
from typing import List, Optional
from pydantic import BaseModel, Field
from typing import Optional, List

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt_config import dame_token, valida_token
 
app = FastAPI()



#-------------------------------------Configuración---------------------------------------
# Definir los tags con descripciones
tags_metadata = [
    {
        "name": "Alumnos",
        "description": "Gestión de Alumnos",
    },
    {
        "name": "Profesores",
        "description": "Gestión de Profesores",
    },
    {
        "name": "Materias",
        "description": "Gestión de Materias",
    },
   

    {
        "name": "Calificaciones",
        "description": "Gestionar calificaciones de cada materia a la que está inscrita el alumno",
    },
    {
        "name": "Usuario",
        "description": "Admin",
    }
    
]

# Inicializar la aplicación FastAPI
app = FastAPI(title="Sistema Escolar",
    description="API para gestionar el sistema escolar de alumnos, profesores, materias y calificaciones",
    version="1.0.0", openapi_tags=tags_metadata)

#Configurar conexion con MongoDB
MONGO_URI="mongodb://localhost:27017" 
#Ejecutar el cliente de base de datos 
cliente=motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db=cliente["ProyectoII_SisDis"] 

#------------------------------------------------Colecciones-------------------------------------------------------------
alumnos_collection = db["Alumnos"]
profesores_collection = db["Profesores"]
materias_collection = db["Materias"]
calificaciones_collection = db["Calificaciones"]

#----------------------------------------------------Clases--------------------------------------------------------------
class Usuario(BaseModel):
    email:str
    clave:str

class Alumno(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento:str
    direccion: str
    fotografia: Optional[str]  # URL de S3
    materias_alumno_id: List[str] = []
  

class Profesor(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento:str
    direccion: str
    especialidad: str 
    materias_profesor_id: List[str] = []


class Materia(BaseModel):
    nombre:str
    descripcion: str
    profesor_id: str  # Profesor asignado a la materia
    alumnos_id: List[str] = []  # Lista de alumnos inscritos en la materia
    #calificaciones: List[Calificacion] = []  # Calificaciones asociadas a la materia

class Calificacion(BaseModel):
    alumno_id: str  # Alumno al que pertenece la calificación
    materia_id: str  # Materia en la que se asigna la calificación
    calificacion: float  # Valor numérico de la calificación


class Portador(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        try:
            # Obtener la autorización del padre
            autorizacion = await super().__call__(request)
            
            # Validar el token
            dato = valida_token(autorizacion.credentials)
            
            # Verificar el email
            if dato.get('email') != 'admin@administrador.com':
                raise HTTPException(status_code=403, detail='No autorizado')
            
            return autorizacion
        except Exception as e:
            raise HTTPException(status_code=401, detail='Token inválido')
        
        


#------------------------------------------- Modelo de actualizacion parcial--------------------------------------------
class UpdateAlumnoModel(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    direccion: Optional[str] = None
    fotografia: Optional[str] = None
    materias_alumno_id: Optional[List[str]] = None

class UpdateProfesorModel(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    direccion: Optional[str] = None
    especialidad: Optional[str] = None
    materias_profesor_id: Optional[List[str]] = None

class UpdateMateriaModel(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    profesor_id: Optional[str]= None
    alumnos_id: Optional[List[str]] = None

class UpdateCalificacionModel(BaseModel):
    calificacion: Optional[float] = None
    alumno_id: Optional[str] = None
    materia_id: Optional[str] = None


#-------------------------------------------------METODOS GET------------------------------------------------------------
#dependencies=[Depends(Portador())]
@app.get("/alumnos/", tags=["Alumnos"])
async def get_alumnos():
    resultados = dict()
    alumnos = await alumnos_collection.find().to_list(None)  # Obtener todos los alumnos de la DB

    for i, alumno in enumerate(alumnos):
        resultados[i] = dict()
        resultados[i]["nombre"] = alumno["nombre"]
        resultados[i]["apellido"] = alumno["apellido"]
        resultados[i]["fecha_nacimiento"] = alumno["fecha_nacimiento"]
        resultados[i]["direccion"] = alumno["direccion"]
        resultados[i]["fotografia"] = alumno["fotografia"]
       

       # Resolver referencias de materias asignadas
        materias_ids = alumno.get("materias_alumno_id", [])
        # Convertir los IDs a ObjectId
        materias_ids = [ObjectId(mid) for mid in materias_ids if mid]
        materias = await materias_collection.find({"_id": {"$in": materias_ids}}).to_list(None)
        resultados[i]["materias_asignadas"] = [
            {
                "_id": str(materia["_id"]), 
                "nombre": materia.get("nombre", "Sin nombre"),
                "descripcion": materia.get("descripcion", "Sin descripción")
            } for materia in materias
        ]
    return resultados


@app.get("/materias/", tags=["Materias"])
async def get_materias():
    resultados = dict()
    materias = await materias_collection.find().to_list(None)  # Obtener todas las materias de la DB

    for i, materia in enumerate(materias):
        resultados[i] = dict()
        resultados[i]["nombre"] = materia["nombre"]
        resultados[i]["descripcion"] = materia["descripcion"]

       # Resolver referencia al profesor
        profesor_id = materia.get("profesor_id")
        if profesor_id:
            try:
                profesor = await profesores_collection.find_one({"_id": ObjectId(profesor_id)})
                if profesor:
                    resultados[i]["profesor"] = {
                        "_id": str(profesor["_id"]), 
                        "nombre": profesor.get("nombre", "Sin nombre"),
                        "apellido": profesor.get("apellido", "Sin apellido"),
                        "especialidad": profesor.get("especialidad", "Sin especialidad")
                    }
            except Exception as e:
                # Manejar cualquier error de conversión de ID
                print(f"Error al recuperar profesor: {e}")
                resultados[i]["profesor"] = None
      

              # Resolver referencias de materias asignadas
        alumnos_ids = materia.get("alumnos_id", [])
# Convertir los IDs a ObjectId
        alumnos_ids = [ObjectId(id) for id in alumnos_ids if id]
        alumnos = await alumnos_collection.find({"_id": {"$in":alumnos_ids}}).to_list(None)
        resultados[i]["malumnos_asignados"] = [
    {
        "_id": str(alumno["_id"]), 
        "nombre": alumno.get("nombre", "Sin nombre"),
        "apellido": alumno.get("apellido", "Sin descripción")
    } for alumno in alumnos 
]

    return resultados


@app.get("/profesores/", tags=["Profesores"])
async def get_profesores():
    resultados = dict()
    profesores = await profesores_collection.find().to_list(None)  # Obtener todos los profesores de la DB

    for i, profesor in enumerate(profesores):
        #materias_ids= profesor.get("materias_profesor_id", [])
        resultados[i] = dict()
        resultados[i]["nombre"] = profesor["nombre"]
        resultados[i]["apellido"] = profesor["apellido"]
        resultados[i]["fecha_nacimiento"] = profesor["fecha_nacimiento"]
        resultados[i]["direccion"] = profesor["direccion"]
        resultados[i]["especialidad"] = profesor["especialidad"]

      # Resolver referencias de materias asignadas
        materias_ids = profesor.get("materias_profesor_id", [])
# Convertir los IDs a ObjectId
        materias_ids = [ObjectId(id) for id in materias_ids if id]
        materias = await materias_collection.find({"_id": {"$in": materias_ids}}).to_list(None)
        resultados[i]["materias_asignadas"] = [
    {
        "_id": str(materia["_id"]), 
        "nombre": materia.get("nombre", "Sin nombre"),
        "descripcion": materia.get("descripcion", "Sin descripción")
    } for materia in materias 
]

    return resultados

@app.get("/calificaciones/", tags=["Calificaciones"])
async def get_calificaciones():
    resultados = dict()
    calificaciones = await calificaciones_collection.find().to_list(None)  # Obtener todas las calificaciones de la DB

    for i, calificacion in enumerate(calificaciones):
        resultados[i] = dict()
        resultados[i]["_id"] = str(calificacion["_id"])
        resultados[i]["calificacion"] = calificacion["calificacion"]

        # Resolver referencia al alumno
        alumno_id = calificacion.get("alumno_id")  # Ajustado a alumno_id
        if alumno_id:
            try:
                alumno = await alumnos_collection.find_one({"_id": ObjectId(alumno_id)})
                if alumno:
                    resultados[i]["alumno"] = {
                        "_id": str(alumno["_id"]),
                        "nombre": alumno.get("nombre", "Sin nombre"),
                        "apellido": alumno.get("apellido", "Sin apellido"),
                        "direccion": alumno.get("direccion", "Sin dirección")
                    }
            except Exception as e:
                print(f"Error al recuperar alumno: {e}")
                resultados[i]["alumno"] = None

        # Resolver referencia a la materia
        materia_id = calificacion.get("materia_id")  # Ajustado a materia_id
        if materia_id:
            try:
                materia = await materias_collection.find_one({"_id": ObjectId(materia_id)})
                if materia:
                    resultados[i]["materia"] = {
                        "_id": str(materia["_id"]),
                        "nombre": materia.get("nombre", "Sin nombre"),
                        "descripcion": materia.get("descripcion", "Sin descripción")
                    }
            except Exception as e:
                print(f"Error al recuperar materia: {e}")
                resultados[i]["materia"] = None

    return resultados


#---------------------------------------------------------GET BY ID-----------------------------------------------------
@app.get("/alumnos/{id}", tags=["Alumnos"] )
async def get_alumno_by_id(id: str):
   alumno = await alumnos_collection.find_one({"_id": ObjectId(id)})
   if not alumno:
       return {"error": "Alumno no encontrado"}

   resultado = {
       "_id": str(alumno["_id"]),
       "nombre": alumno.get("nombre", "Sin nombre"),
       "apellido": alumno.get("apellido", "Sin apellido"),
       "fecha_nacimiento": alumno.get("fecha_nacimiento", "Fecha no especificada"),
       "direccion": alumno.get("direccion", "Dirección no especificada"),
       "fotografia": alumno.get("fotografia", None)
   }

   # Resolver referencias de materias
   materias_ids = alumno.get("materias_alumno_id", [])
   if materias_ids:
       try:
           # Convertir IDs a ObjectId y buscar materias
           materias_obj_ids = [ObjectId(mid) for mid in materias_ids if mid]
           materias = await materias_collection.find({"_id": {"$in": materias_obj_ids}}).to_list(None)
           
           resultado["materias"] = [
               {
                   "_id": str(materia["_id"]),
                   "nombre": materia.get("nombre", "Sin nombre"),
                   "descripcion": materia.get("descripcion", "Sin descripción")
               } for materia in materias
           ]
       except Exception as e:
           print(f"Error al recuperar materias: {e}")
           resultado["materias"] = []
   else:
       resultado["materias"] = []

   return resultado


@app.get("/profesores/{id}", tags=["Profesores"])
async def get_profesor_by_id(id: str):
    profesor = await profesores_collection.find_one({"_id": ObjectId(id)})
    if not profesor:
        return {"error": "Profesor no encontrado"}

    resultado = {
        "_id": str(profesor["_id"]),
        "nombre": profesor.get("nombre", "Sin nombre"),
        "apellido": profesor.get("apellido", "Sin apellido"),
        "fecha_nacimiento": profesor.get("fecha_nacimiento", "Fecha no especificada"),
        "direccion": profesor.get("direccion", "Dirección no especificada"),
        "especialidad": profesor.get("especialidad", "Sin especialidad")
    }

    # Resolver referencias de materias asignadas
    materias_ids = profesor.get("materias_profesor_id", [])
    if materias_ids:
        try:
            # Convertir IDs a ObjectId y buscar materias
            materias_obj_ids = [ObjectId(mid) for mid in materias_ids if mid]
            materias = await materias_collection.find({"_id": {"$in": materias_obj_ids}}).to_list(None)
            
            resultado["materias_asignadas"] = [
                {
                    "_id": str(materia["_id"]),
                    "nombre": materia.get("nombre", "Sin nombre"),
                    "descripcion": materia.get("descripcion", "Sin descripción")
                } for materia in materias
            ]
        except Exception as e:
            print(f"Error al recuperar materias: {e}")
            resultado["materias_asignadas"] = []
    else:
        resultado["materias_asignadas"] = []

    return resultado



@app.get("/materias/{id}", tags=["Materias"])
async def get_materia_by_id(id: str):
    materia = await materias_collection.find_one({"_id": ObjectId(id)})
    if not materia:
        return {"error": "Materia no encontrada"}

    resultado = {
        "_id": str(materia["_id"]),
        "nombre": materia.get("nombre", "Sin nombre"),
        "descripcion": materia.get("descripcion", "Sin descripción")
    }

    # Resolver referencia al profesor
    profesor_id = materia.get("profesor_id")
    if profesor_id:
        try:
            profesor = await profesores_collection.find_one({"_id": ObjectId(profesor_id)})
            if profesor:
                resultado["profesor"] = {
                    "_id": str(profesor["_id"]),
                    "nombre": profesor.get("nombre", "Sin nombre"),
                    "apellido": profesor.get("apellido", "Sin apellido"),
                    "especialidad": profesor.get("especialidad", "Sin especialidad")
                }
        except Exception as e:
            print(f"Error al recuperar profesor: {e}")
            resultado["profesor"] = None

    # Resolver referencias de alumnos
    alumnos_ids = materia.get("alumnos_id", [])
    if alumnos_ids:
        try:
            # Convertir IDs a ObjectId y buscar alumnos
            alumnos_obj_ids = [ObjectId(aid) for aid in alumnos_ids if aid]
            alumnos = await alumnos_collection.find({"_id": {"$in": alumnos_obj_ids}}).to_list(None)
            
            resultado["alumnos"] = [
                {
                    "_id": str(alumno["_id"]),
                    "nombre": alumno.get("nombre", "Sin nombre"),
                    "apellido": alumno.get("apellido", "Sin apellido")
                } for alumno in alumnos
            ]
        except Exception as e:
            print(f"Error al recuperar alumnos: {e}")
            resultado["alumnos"] = []
    else:
        resultado["alumnos"] = []

    return resultado


@app.get("/calificaciones/{id}", tags=["Calificaciones"])
async def get_calificacion_by_id(id: str):
    calificacion = await calificaciones_collection.find_one({"_id": ObjectId(id)})
    if not calificacion:
        return {"error": "Calificación no encontrada"}

    resultado = {
        "_id": str(calificacion["_id"]),
        "calificacion": calificacion.get("calificacion", "Sin calificación")
    }

    # Resolver referencia al alumno
    alumno_id = calificacion.get("alumno_id")
    if alumno_id:
        try:
            alumno = await alumnos_collection.find_one({"_id": ObjectId(alumno_id)})
            if alumno:
                resultado["alumno"] = {
                    "_id": str(alumno["_id"]),
                    "nombre": alumno.get("nombre", "Sin nombre"),
                    "apellido": alumno.get("apellido", "Sin apellido"),
                    "direccion": alumno.get("direccion", "Sin dirección")
                }
        except Exception as e:
            print(f"Error al recuperar alumno: {e}")
            resultado["alumno"] = None

    # Resolver referencia a la materia
    materia_id = calificacion.get("materia_id")
    if materia_id:
        try:
            materia = await materias_collection.find_one({"_id": ObjectId(materia_id)})
            if materia:
                resultado["materia"] = {
                    "_id": str(materia["_id"]),
                    "nombre": materia.get("nombre", "Sin nombre"),
                    "descripcion": materia.get("descripcion", "Sin descripción")
                }
        except Exception as e:
            print(f"Error al recuperar materia: {e}")
            resultado["materia"] = None

    return resultado


#--------------------------------------------------------------POST-----------------------------------------------------
@app.post("/alumnos/", tags=["Alumnos"])
async def create_alumno(alumno: Alumno):
    nuevo_alumno = alumno.dict()  # Convertir el modelo Pydantic a un diccionario
    resultado = await alumnos_collection.insert_one(nuevo_alumno)  # Insertar en la base de datos
    return {"mensaje": "Alumno creado exitosamente", "id": str(resultado.inserted_id)}

@app.post("/profesores/", tags=["Profesores"])
async def create_profesor(profesor: Profesor):
    nuevo_profesor = profesor.dict()  # Convertir el modelo Pydantic a un diccionario
    resultado = await profesores_collection.insert_one(nuevo_profesor)  # Insertar en la base de datos
    return {"mensaje": "Profesor creado exitosamente", "id": str(resultado.inserted_id)}

@app.post("/materias/", tags=["Materias"])
async def create_materia(materia: Materia):
    nueva_materia = materia.dict()  # Convertir el modelo Pydantic a un diccionario
    resultado = await materias_collection.insert_one(nueva_materia)  # Insertar en la base de datos
    return {"mensaje": "Materia creada exitosamente", "id": str(resultado.inserted_id)}

@app.post("/calificaciones/", tags=["Calificaciones"])
async def create_calificacion(calificacion: Calificacion):
    nueva_calificacion = calificacion.dict()  # Convertir el modelo Pydantic a un diccionario

 

    # Insertar en la base de datos
    resultado = await calificaciones_collection.insert_one(nueva_calificacion)
    return {"mensaje": "Calificación creada exitosamente", "id": str(resultado.inserted_id)}

#------------------------------------------------------DELETE------------------------------------------------------------
@app.delete("/alumnos/{id}", tags=["Alumnos"])
async def delete_alumno(id: str):
    alumno = await alumnos_collection.find_one({"_id":ObjectId(id)})
    if not alumno:
        return {"error": "Alumno no encontrado"}

    # Eliminar el alumno
    await alumnos_collection.delete_one({"_id": ObjectId(id)})
    return {"mensaje": "Alumno eliminado exitosamente"}


@app.delete("/profesores/{id}", tags=["Profesores"])
async def delete_profesor(id: str):
    profesor = await profesores_collection.find_one({"_id": ObjectId(id)})
    if not profesor:
        return {"error": "Profesor no encontrado"}

    # Eliminar el profesor
    await profesores_collection.delete_one({"_id": ObjectId(id)})
    return {"mensaje": "Profesor eliminado exitosamente"}


@app.delete("/materias/{id}", tags=["Materias"])
async def delete_materia(id: str):
    materia = await materias_collection.find_one({"_id": ObjectId(id)})
    if not materia:
        return {"error": "Materia no encontrada"}

    # Eliminar la materia
    await materias_collection.delete_one({"_id": ObjectId(id)})
    return {"mensaje": "Materia eliminada exitosamente"}


@app.delete("/calificaciones/{id}", tags=["Calificaciones"])
async def delete_calificacion(id: str):
    calificacion = await calificaciones_collection.find_one({"_id": ObjectId(id)})
    if not calificacion:
        return {"error": "Calificación no encontrada"}

    # Eliminar la calificación
    await calificaciones_collection.delete_one({"_id": ObjectId(id)})
    return {"mensaje": "Calificación eliminada exitosamente"}

#--------------------------------------------------------------PUT----------------------------------------------------
@app.put("/alumnos/{id}", tags=["Alumnos"])
async def update_alumno(id: str, alumno: UpdateAlumnoModel):
    datos_actualizados = {k: v for k, v in alumno.dict().items() if v is not None}

    if not datos_actualizados:
        return {"error": "No se proporcionaron datos para actualizar"}

    resultado = await alumnos_collection.update_one({"_id": ObjectId(id)}, {"$set": datos_actualizados})
    if resultado.matched_count == 0:
        return {"error": "Alumno no encontrado"}

    return {"mensaje": "Alumno actualizado exitosamente"}


@app.put("/profesores/{id}", tags=["Profesores"])
async def update_profesor(id: str, profesor: UpdateProfesorModel):
    datos_actualizados = {k: v for k, v in profesor.dict().items() if v is not None}

    if not datos_actualizados:
        return {"error": "No se proporcionaron datos para actualizar"}

    resultado = await profesores_collection.update_one({"_id": ObjectId(id)}, {"$set": datos_actualizados})
    if resultado.matched_count == 0:
        return {"error": "Profesor no encontrado"}

    return {"mensaje": "Profesor actualizado exitosamente"}



@app.put("/materias/{id}", tags=["Materias"])
async def update_materia(id: str, materia: UpdateMateriaModel):
    datos_actualizados = {k: v for k, v in materia.dict().items() if v is not None}

    if not datos_actualizados:
        return {"error": "No se proporcionaron datos para actualizar"}

    resultado = await materias_collection.update_one({"_id": ObjectId(id)}, {"$set": datos_actualizados})
    if resultado.matched_count == 0:
        return {"error": "Materia no encontrada"}

    return {"mensaje": "Materia actualizada exitosamente"}


@app.put("/calificaciones/{id}", tags=["Calificaciones"])
async def update_calificacion(id: str, calificacion: UpdateCalificacionModel):
    datos_actualizados = {k: v for k, v in calificacion.dict().items() if v is not None}

    if not datos_actualizados:
        return {"error": "No se proporcionaron datos para actualizar"}

    # Validar referencias si se cambia el alumno o la materia
    if "alumno" in datos_actualizados:
        alumno = await alumnos_collection.find_one({"_id": datos_actualizados["alumno"]})
        if not alumno:
            return {"error": "Alumno no encontrado"}

    if "materia" in datos_actualizados:
        materia = await materias_collection.find_one({"_id": datos_actualizados["materia"]})
        if not materia:
            return {"error": "Materia no encontrada"}

    resultado = await calificaciones_collection.update_one({"_id": ObjectId(id)}, {"$set": datos_actualizados})
    if resultado.matched_count == 0:
        return {"error": "Calificación no encontrada"}

    return {"mensaje": "Calificación actualizada exitosamente"}
#--------------------------------------------------------LOGIN-------------------------------------
#creamos ruta para login
@app.post('/login',tags=['Usuario'])
def login(usuario:Usuario):
    if usuario.email == 'admin@administrador.com' and usuario.clave == '1234':
        # obtenemos el token con la funcion pasandole el diccionario de usuario
        token:str=dame_token(usuario.dict())
        return JSONResponse(status_code=200,content=token)
    else:
        return JSONResponse(content={'mensaje':'Acceso denegado'}, status_code=404)
