
README: Sistema de Gestión Escolar API
Descripción del Proyecto
Este proyecto consiste en el desarrollo de una API RESTful para la gestión de información de estudiantes, profesores y materias en la UPIIZ. La aplicación permite realizar operaciones CRUD (Crear, Leer, Actualizar y Eliminar) en registros de estudiantes, profesores y materias. También incluye funcionalidades como la asignación de materias a profesores y estudiantes, registro de calificaciones, validación de datos y documentación de la API.

El sistema está diseñado para ser robusto, seguro y escalable, utilizando FastAPI como framework principal, MongoDB como base de datos NoSQL y AWS S3 para el almacenamiento de archivos. Sin embargo, debido a un problema en las dependencias relacionadas con la implementación de seguridad, no se logró integrar funcionalidades de autenticación y autorización.

-->Características Principales
1.Gestión de Estudiantes
  *Crear, leer, actualizar y eliminar registros de estudiantes.
  *Cada estudiante tiene:
    *ID único
    *Nombre y apellido
    *Fecha de nacimiento
    *Dirección
    *Foto (almacenada en AWS S3)
    *Materias inscritas (lista)

2.Gestión de Profesores
  *Crear, leer, actualizar y eliminar registros de profesores.
  *Cada profesor tiene:
    *ID único
    *Nombre y apellido
    *Fecha de nacimiento
    *Dirección
    *Especialidad
    *Materias impartidad (lista)
  
3.Gestión de Materias
  *Crear, leer, actualizar y eliminar registros de materias.
  *Cada materia tiene:
    *ID único
    *Nombre
    *Descripción
    *Profesores que imparten la materia (lista)
    *Alumnos incritos en la materia (lista)

4.Registrar calificaciones de estudiantes por materia.
  *Las calificaciones están asociadas a un estudiante y a una materia específica.
5.Validación de Datos
  *Garantizar que los datos ingresados sean correctos y consistentes.
6. Documentación
  * Generación automática de documentación interactiva utilizando FastAPI. 

->imitaciones
  *Falta de Seguridad: No se logró implementar autenticación y autorización debido a un problema en las dependencias relacionadas. Se intentó encontrar una solución durante el desarrollo, pero no fue posible resolverlo en esta versión del proyecto.

->Tecnologías Utilizadas
  *Framework: FastAPI
  *Base de Datos: MongoDB (NoSQL)
  *Almacenamiento de Archivos: AWS S3
  *Lenguaje de Programación: Python

-->Instalación y Uso
1.Clona el repositorio:
    git clone <https://github.com/SebastianColin27/SisDis_ProyectoII_JSCB.git>
    cd <ProyectoII>
    cd <app>
2. Instala las dependencias:
    pip install -r requirements.txt
3.Configura las variables de entorno:
    *Configura la conexión a MongoDB.
4.Ejecuta el servidor:
    uvicorn main:app --reload
5.Accede a la documentación interactiva:
    *Swagger UI: http://127.0.0.1:8000/docs# 


----->Link de Video explicando su funcionamineto 
<https://www.youtube.com/watch?v=QoJNldORTPw>

