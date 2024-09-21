from flask import Flask, render_template, redirect, request, session, flash, url_for, make_response
from flask_mysqldb import MySQL
import database as bd
import pandas as pd
from flask import send_file
import os
from werkzeug.utils import secure_filename
import tempfile
from openpyxl import load_workbook
from openpyxl.styles import NamedStyle
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fpdf import FPDF
import mysql.connector

app = Flask(__name__, template_folder='../template')
app.secret_key = "luisito.16"

mysql = MySQL(app)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sistema_registro_notas'
app.config['MYSQL_PORT'] = 3306

@app.route('/')
def home():
    return render_template('inicio.html')

@app.route('/ingreso')
def ingreso():
    return render_template('paginaprincipal.html')


from flask import redirect, url_for, session

from flask import redirect, url_for, session, request, flash

@app.route('/acceso-login', methods=["POST"])
def login():
    if 'txtusuario' in request.form and 'txtcontraseña' in request.form:
        usuario = request.form['txtusuario']
        contraseña = request.form['txtcontraseña']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE Nombre_usuario=%s AND Contraseña=%s', (usuario, contraseña))
        account = cursor.fetchone()  # Aquí se obtiene la cuenta del usuario

        if account:
            session['logeado'] = True
            session['id'] = account[0]  # Índice numérico para el campo 'id'
            session['id_rol'] = account[6]  # Índice numérico para el campo 'id_rol'

            id_rol = session['id_rol']
            if id_rol == 1:
                print("Rol de usuario: Administrador")
                return redirect(url_for('admin_dashboard'))  # Redirigir al panel de administrador
            elif id_rol == 2:
                print("Rol de usuario: Usuario normal")
                return render_template("paginaprincipal.html")  # Redirigir a la página principal del usuario normal
            else:
                print("Rol de usuario desconocido")
                return render_template('paginaprincipal.html')  # Redirigir a la página principal
        else:
            flash("Usuario o contraseña incorrectos.", "error")
            return redirect('/')
    else:
        return "Error: Debes proporcionar usuario y contraseña"

##MOSTRAR USUARIOS
@app.route('/admin_dashboard')
def admin_dashboard():
    # Obtener los datos de los usuarios y pasarlos a la plantilla
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM usuarios")
    myresult = cursor.fetchall()

    insetObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insetObject.append(dict(zip(columnNames, record)))
    cursor.close()

    return render_template('admin.html', data=insetObject)

##GUARDAR USUARIOS
@app.route('/agregarusuario', methods=['POST'])
def agregar_usuario():
    id = request.form.get('id_usuario')
    nombre = request.form.get('Nombre')
    apellido = request.form.get('Apellido')
    email = request.form.get('email')
    contraseña = request.form.get('Contraseña')
    nombre_usuario = request.form.get('Nombre_usuario')
    id_rol = request.form.get('id_rol')
    cedula_profesor = request.form.get('cedula_profesor')

    if id and nombre and apellido and email and contraseña and nombre_usuario and id_rol and cedula_profesor:
        try:
            cursor = mysql.connection.cursor()

            # Verificar si ya existe un usuario con el mismo ID
            cursor.execute("SELECT id FROM usuarios WHERE id = %s", (id,))
            existing_user_with_id = cursor.fetchone()

            if existing_user_with_id:
                flash('Error: Ya existe un usuario con este ID.', 'error')
            else:
                # Verificar si ya existe un usuario con la misma cédula de profesor y el mismo rol
                cursor.execute("SELECT id FROM usuarios WHERE cedula_profesor = %s AND id_rol = %s", (cedula_profesor, id_rol))
                existing_user_with_cedula_rol = cursor.fetchone()

                if existing_user_with_cedula_rol:
                    flash('Error: Ya existe un usuario con esta cédula de profesor y rol.', 'error')
                else:
                    # Verificar si la cédula del profesor existe en la tabla de profesores
                    cursor.execute("SELECT cedula FROM profesores WHERE cedula = %s", (cedula_profesor,))
                    existing_professor = cursor.fetchone()

                    if not existing_professor:
                        flash('Error: La cédula del profesor no existe en la base de datos.', 'error')
                    else:
                        # Insertar el nuevo usuario en la tabla de usuarios
                        sql = "INSERT INTO usuarios (id, Nombre, Apellido, Email, Contraseña, Nombre_usuario, id_rol, cedula_profesor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                        data = (id, nombre, apellido, email, contraseña, nombre_usuario, id_rol, cedula_profesor)
                        cursor.execute(sql, data)
                        mysql.connection.commit()
                        cursor.close()
                        flash('Usuario agregado correctamente', 'success')

        except Exception as e:
            flash(f'Error al agregar usuario: {str(e)}', 'error')
    else:
        flash('Error: Debes completar todos los campos', 'error')
    
    return redirect(url_for('admin_dashboard'))

#EDITAR USUARIO
@app.route('/editarusuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if request.method == 'GET':
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
            user = cursor.fetchone()
            cursor.close()
            if user:
                return render_template('editar_usuario.html', user=user)
            else:
                flash('Usuario no encontrado', 'error')
                return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f'Error al obtener usuario: {str(e)}', 'error')
            return redirect(url_for('admin_dashboard'))
    elif request.method == 'POST':
        nuevo_id = request.form.get('id_usuario')
        nombre = request.form.get('Nombre')
        apellido = request.form.get('Apellido')
        email = request.form.get('email')
        contraseña = request.form.get('Contraseña')
        nombre_usuario = request.form.get('Nombre_usuario')
        id_rol = request.form.get('id_rol')
        cedula_profesor = request.form.get('cedula_profesor')

        if  nuevo_id and nombre and apellido and email and contraseña and nombre_usuario and id_rol and cedula_profesor:
            try:
                cursor = mysql.connection.cursor()

                # Verificar si ya existe un usuario con el nuevo ID
                cursor.execute("SELECT id FROM usuarios WHERE id = %s AND id != %s", (nuevo_id, id))
                existing_user_with_id = cursor.fetchone()

                # Verificar si ya existe un usuario con la misma cédula de profesor y el mismo rol
                cursor.execute("SELECT id FROM usuarios WHERE cedula_profesor = %s AND id_rol = %s AND id != %s", (cedula_profesor, id_rol, id))
                existing_user_with_cedula_rol = cursor.fetchone()

                if existing_user_with_id:
                    flash('Error: Ya existe un usuario con este ID.', 'error')
                elif existing_user_with_cedula_rol:
                    flash('Error: Ya existe un usuario con esta cédula de profesor y rol.', 'error')
                else:
                    # Verificar si la cédula del profesor existe en la tabla de profesores
                    cursor.execute("SELECT cedula FROM profesores WHERE cedula = %s", (cedula_profesor,))
                    existing_professor = cursor.fetchone()

                    if not existing_professor:
                        flash('Error: La cédula del profesor no existe en la base de datos.', 'error')
                    else:
                        # Actualizar los datos del usuario en la tabla de usuarios
                        sql = "UPDATE usuarios SET id=%s, Nombre=%s, Apellido=%s, Email=%s, Contraseña=%s, Nombre_usuario=%s, id_rol=%s, cedula_profesor=%s WHERE id=%s"
                        data = (nuevo_id, nombre, apellido, email, contraseña, nombre_usuario, id_rol, cedula_profesor, id)
                        cursor.execute(sql, data)
                        mysql.connection.commit()
                        cursor.close()
                        flash('Usuario actualizado correctamente', 'success')
                        return redirect(url_for('admin_dashboard'))

            except Exception as e:
                flash(f'Error al actualizar usuario: {str(e)}', 'error')
        else:
            flash('Error: Debes completar todos los campos', 'error')

    return redirect(url_for('admin_dashboard'))

##ELIMINAR USUARIO
@app.route('/eliminarusuario/<int:id>', methods=['GET', 'POST'])
def eliminar_usuario(id):
    try:
        cursor = mysql.connection.cursor()

        # Verificar si existe un usuario con el ID especificado
        cursor.execute("SELECT id FROM usuarios WHERE id = %s", (id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Eliminar el usuario de la tabla de usuarios
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
            mysql.connection.commit()
            cursor.close()
            flash('Usuario eliminado correctamente', 'success')
        else:
            flash('Error: No existe un usuario con este ID.', 'error')
    except Exception as e:
        flash(f'Error al eliminar usuario: {str(e)}', 'error')

    return redirect(url_for('admin_dashboard'))
#EXCEL USUARIOS
@app.route('/generar_excel_usuarios')
def generar_excel_usuarios():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuarios")
        datos = cursor.fetchall()
        cursor.close()
        
        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(datos, columns=["ID", "Nombre", "Apellido", "Email", "Contraseña", "Nombre_usuario", "ID_Rol", "Cedula_Profesor"])
        
        # Obtener la fecha actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
        
        # Crear el nombre del archivo Excel
        nombre_archivo = f"usuarios_{fecha_actual}.xlsx"
        
        # Crear un directorio temporal para almacenar el archivo
        directorio_temporal = tempfile.mkdtemp()
        
        # Combinar el directorio temporal con el nombre del archivo
        ruta_guardado = os.path.join(directorio_temporal, nombre_archivo)
        
        # Crear el archivo Excel
        with pd.ExcelWriter(ruta_guardado, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Usuarios')
            
            # Ajustar el ancho de las columnas
            worksheet = writer.sheets['Usuarios']
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(i, i, column_len + 2)
                
        # Enviar el archivo Excel como respuesta
        return send_file(ruta_guardado, as_attachment=True)
    
    except Exception as e:
        flash(f'Error al generar el archivo Excel: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

#MOSTRAR ESTUDIANTES
@app.route('/estudiantes')
def estudiantes():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM estudiantes")
    myresult = cursor.fetchall()

    # Convertir a diccionario
    insetObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insetObject.append(dict(zip(columnNames, record)))
    cursor.close()

    return render_template('estudiantes.html', data=insetObject)



   # ELIMINAR ESTUDIANTE
@app.route('/eliminarestudiante/<string:cedula>')
def eliminarEstudiante(cedula):
    try:
        cursor = mysql.connection.cursor()

        # Eliminar registros de notas asociadas al estudiante
        sql_delete_notas = "DELETE FROM notas WHERE cedula_estudiante = %s"
        cursor.execute(sql_delete_notas, (cedula,))
        mysql.connection.commit()

        # Eliminar al estudiante
        sql_delete_estudiante = "DELETE FROM estudiantes WHERE cedula = %s"
        cursor.execute(sql_delete_estudiante, (cedula,))
        mysql.connection.commit()

        cursor.close()
        flash('Estudiante y registros de notas asociadas eliminados correctamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar estudiante: {str(e)}', 'error')

    return redirect(url_for('estudiantes'))

# EDITAR ESTUDIANTES
@app.route('/editarestudiante/<string:cedula>', methods=['POST'])
def editarestudiante(cedula):
    if request.method == 'POST':
        nueva_cedula = request.form.get('cedula')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        edad = request.form.get('edad')
        direccion = request.form.get('direccion')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')
        seccion = request.form.get('seccion')
        fecha_inscripcion = request.form.get('fecha_inscripcion')

        if nueva_cedula and nombre and apellido and edad and direccion and correo and telefono and seccion and fecha_inscripcion:
            try:
                cursor = mysql.connection.cursor()

                # Verificar si hay registros en la tabla 'notas' que hagan referencia a la nueva cédula
                sql_check = "SELECT COUNT(*) FROM notas WHERE cedula_estudiante = %s"
                cursor.execute(sql_check, (cedula,))
                count = cursor.fetchone()[0]

                if count > 0:
                    # Si hay registros en 'notas', mostrar un mensaje de error
                    flash('Error: El estudiante tiene datos relacionados con la tabla de notas. Primero elimine las dependencias en esa tabla.', 'error')
                else:
                    # Si no hay registros en 'notas', actualizar la información del estudiante
                    sql_update = "UPDATE estudiantes SET cedula = %s, nombre = %s, apellido = %s, edad = %s, direccion = %s, correo = %s, telefono = %s, seccion = %s, fecha_inscripcion = %s WHERE cedula = %s"
                    data = (nueva_cedula, nombre, apellido, edad, direccion, correo, telefono, seccion, fecha_inscripcion, cedula)
                    cursor.execute(sql_update, data)
                    mysql.connection.commit()
                    flash('Estudiante actualizado correctamente', 'success')

                cursor.close()
            except Exception as e:
                flash(f'Error al actualizar estudiante: {str(e)}', 'error')

    return redirect(url_for('estudiantes'))



# GUARDAR ESTUDIANTES
@app.route('/gestudiante', methods=['POST'])
def addEstudiante():
    cedula = request.form.get('cedula')
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    edad = request.form.get('edad')
    direccion = request.form.get('direccion')
    correo = request.form.get('correo')
    telefono = request.form.get('telefono')
    seccion = request.form.get('seccion')
    fecha_inscripcion = request.form.get('fecha_inscripcion')

    if cedula and nombre and apellido and edad and direccion and correo and telefono and seccion and fecha_inscripcion:
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT cedula FROM estudiantes WHERE cedula = %s", (cedula,))
            existing_cedula = cursor.fetchone()

            if not existing_cedula:
                sql = "INSERT INTO estudiantes (cedula, nombre, apellido, edad, direccion, correo, telefono, seccion, fecha_inscripcion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                data = (cedula, nombre, apellido, edad, direccion, correo, telefono, seccion, fecha_inscripcion)
                cursor.execute(sql, data)
                mysql.connection.commit()
                cursor.close()
                flash('Estudiante añadido de manera exitosa', 'success')
            else:
                flash('Error: La cédula ya existe en la base de datos.', 'error')
        except Exception as e:
            flash(f'Error al agregar estudiante: {str(e)}', 'error')
    else:
        flash('Error: Debes completar todos los campos', 'error')
    
    return redirect(url_for('estudiantes'))



##EXCEL TABLA ESTUDIANTES

@app.route('/generar_excel')
def generar_excel():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM estudiantes")
        datos = cursor.fetchall()
        cursor.close()
        
        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(datos, columns=["Cedula", "Nombre", "Apellido", "Edad", "Dirección", "Correo", "Teléfono", "Sección", "Fecha de Inscripción"])
        
        # Ajustar el formato de la columna 'Cedula' para evitar notación científica
        df['Cedula'] = df['Cedula'].astype(str)  # Convertir a tipo cadena
        df['Cedula'] = df['Cedula'].apply(lambda x: f"'{x}")  # Agregar comilla simple
        
        # Formatear la columna 'Fecha de Inscripción'
        df['Fecha de Inscripción'] = pd.to_datetime(df['Fecha de Inscripción']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Obtener la fecha actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
        
        # Crear el archivo Excel
        nombre_archivo = f"datos_estudiantes_{fecha_actual}.xlsx"
        
        # Crear un directorio temporal para almacenar el archivo
        directorio_temporal = tempfile.mkdtemp()
        
        # Combinar el directorio temporal con el nombre del archivo
        ruta_guardado = os.path.join(directorio_temporal, nombre_archivo)
        
        # Crear el archivo Excel
        with pd.ExcelWriter(ruta_guardado, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Estudiantes')
            
            # Ajustar el ancho de las columnas
            worksheet = writer.sheets['Estudiantes']
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(i, i, column_len + 2)
                
        return send_file(ruta_guardado, as_attachment=True)
    
    except Exception as e:
        flash(f'Error al generar el archivo Excel: {str(e)}', 'error')
        return redirect(url_for('estudiantes'))
    


####PROFESORES
    
@app.route('/profesores')
def profesores():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM profesores")
    myresult = cursor.fetchall()

    # Convertir a diccionario
    insetObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insetObject.append(dict(zip(columnNames, record)))
    cursor.close()
    return render_template('profesores.html', data=insetObject)


#GUARDAR PROFESORES
@app.route('/gprofesor', methods=['POST'])
def addProfesor():
    cedula = request.form.get('cedula')
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    edad = request.form.get('edad')
    direccion = request.form.get('direccion')
    correo = request.form.get('correo')
    telefono = request.form.get('telefono')

    if cedula and nombre and apellido and edad and direccion and correo and telefono:
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT cedula FROM profesores WHERE cedula = %s", (cedula,))
            existing_cedula = cursor.fetchone()

            if not existing_cedula:
                sql = "INSERT INTO profesores (cedula, nombre, apellido, edad, direccion, correo, telefono) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                data = (cedula, nombre, apellido, edad, direccion, correo, telefono)
                cursor.execute(sql, data)
                mysql.connection.commit()
                cursor.close()
                flash('Profesor añadido de manera exitosa', 'success')
            else:
                flash('Error: La cédula ya existe en la base de datos.', 'error')
        except Exception as e:
            flash(f'Error al agregar profesor: {str(e)}', 'error')
    else:
        flash('Error: Debes completar todos los campos', 'error')
    
    return redirect(url_for('profesores'))

#ELIMINAR PROFESORES

@app.route('/eliminarprofesor/<string:cedula>')
def eliminarProfesor(cedula):
    try:
        cursor = mysql.connection.cursor()

        # Verificar si hay registros en la tabla 'usuarios' que hagan referencia a la cédula del profesor
        sql_check_usuarios = "SELECT COUNT(*) FROM usuarios WHERE cedula_profesor = %s"
        cursor.execute(sql_check_usuarios, (cedula,))
        count_usuarios = cursor.fetchone()[0]

        # Verificar si hay registros en la tabla 'materias' que hagan referencia a la cédula del profesor
        sql_check_materias = "SELECT COUNT(*) FROM materias WHERE cedula_profesor = %s"
        cursor.execute(sql_check_materias, (cedula,))
        count_materias = cursor.fetchone()[0]

        if count_usuarios > 0 or count_materias > 0:
            # Si hay registros en 'usuarios' o 'materias', mostrar un mensaje de error
            flash('Error: Este profesor está relacionado con usuarios o materias. No se puede eliminar.', 'error')
        else:
            # Si no hay registros en 'usuarios' ni 'materias', eliminar al profesor y sus materias asociadas
            sql_delete_materias = "DELETE FROM materias WHERE cedula_profesor = %s"
            cursor.execute(sql_delete_materias, (cedula,))
            mysql.connection.commit()

            sql_delete_profesor = "DELETE FROM profesores WHERE cedula = %s"
            cursor.execute(sql_delete_profesor, (cedula,))
            mysql.connection.commit()

            flash('Profesor y materias asociadas eliminados correctamente', 'success')

    except Exception as e:
        flash(f'Error al eliminar profesor: {str(e)}', 'error')
    finally:
        cursor.close()

    return redirect(url_for('profesores'))
#EDITAR PROFESORES

@app.route('/editarprofesor/<string:cedula>', methods=['POST'])
def editarProfesor(cedula):
    if request.method == 'POST':
        nueva_cedula = request.form.get('cedula')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        edad = request.form.get('edad')
        direccion = request.form.get('direccion')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')

        try:
            cursor = mysql.connection.cursor()

            # Verificar si hay registros en la tabla 'usuarios' que hagan referencia a la cédula del profesor
            sql_check_usuarios = "SELECT COUNT(*) FROM usuarios WHERE cedula_profesor = %s"
            cursor.execute(sql_check_usuarios, (cedula,))
            count_usuarios = cursor.fetchone()[0]

            # Verificar si hay registros en la tabla 'materias' que hagan referencia a la cédula del profesor
            sql_check_materias = "SELECT COUNT(*) FROM materias WHERE cedula_profesor = %s"
            cursor.execute(sql_check_materias, (cedula,))
            count_materias = cursor.fetchone()[0]

            if count_usuarios > 0 or count_materias > 0:
                # Si hay registros en 'usuarios' o 'materias', mostrar un mensaje de error
                flash('Error: Este profesor está relacionado con usuarios o materias. No se pueden realizar cambios.', 'error')
            else:
                # Si no hay registros en 'usuarios' ni 'materias', actualizar la información del profesor, incluida la cédula
                sql_update = "UPDATE profesores SET cedula = %s, nombre = %s, apellido = %s, edad = %s, direccion = %s, correo = %s, telefono = %s WHERE cedula = %s"
                data = (nueva_cedula, nombre, apellido, edad, direccion, correo, telefono, cedula)
                cursor.execute(sql_update, data)
                mysql.connection.commit()
                flash('Profesor actualizado correctamente', 'success')

            cursor.close()
        except Exception as e:
            flash(f'Error al actualizar profesor: {str(e)}', 'error')

    return redirect(url_for('profesores'))


#EXCEL PROFESORES
@app.route('/generar_excel_profesores')
def generar_excel_profesores():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM profesores")
        datos = cursor.fetchall()
        cursor.close()
        
        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(datos, columns=["Cedula", "Nombre", "Apellido", "Edad", "Dirección", "Correo", "Teléfono"])
        
        # Ajustar el formato de la columna 'Cedula' para evitar notación científica
        df['Cedula'] = df['Cedula'].astype(str)  # Convertir a tipo cadena
        df['Cedula'] = df['Cedula'].apply(lambda x: f"'{x}")  # Agregar comilla simple
        
        # Obtener la fecha actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
        
        # Crear el nombre del archivo Excel
        nombre_archivo = f"datos_profesores_{fecha_actual}.xlsx"
        
        # Crear un directorio temporal para almacenar el archivo
        directorio_temporal = tempfile.mkdtemp()
        
        # Combinar el directorio temporal con el nombre del archivo
        ruta_guardado = os.path.join(directorio_temporal, nombre_archivo)
        
        # Crear el archivo Excel
        with pd.ExcelWriter(ruta_guardado, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Profesores')
            
            # Ajustar el ancho de las columnas
            worksheet = writer.sheets['Profesores']
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(i, i, column_len + 2)
                
        return send_file(ruta_guardado, as_attachment=True)
    
    except Exception as e:
        flash(f'Error al generar el archivo Excel: {str(e)}', 'error')
        return redirect(url_for('profesores'))

##MATERIAS
    
    #MOSTRAR MATERIAS

@app.route('/materias')
def materias():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM materias")  # Reemplaza 'materias' con el nombre de tu tabla
    myresult = cursor.fetchall()

    # Convertir a diccionario
    insetObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insetObject.append(dict(zip(columnNames, record)))
    cursor.close()
    return render_template('materias.html', data=insetObject)  # Asegúrate de que el nombre del archivo HTML sea correcto

#GUARDAR MATERIAS
@app.route('/gmateria', methods=['POST'])
def addMateria():
    id_materia = request.form.get('id_materia')
    nombre = request.form.get('nombre')
    cedula_profesor = request.form.get('cedula_profesor')

    if id_materia and nombre and cedula_profesor:
        try:
            cursor = mysql.connection.cursor()
            # Verificar si ya existe una materia con el mismo ID en la base de datos
            cursor.execute("SELECT id_materia FROM materias WHERE id_materia = %s", (id_materia,))
            existing_id = cursor.fetchone()

            if existing_id:
                flash('Error: Ya existe una materia con el mismo ID en la base de datos', 'error')
            else:
                # Verificar si la cédula del profesor existe en la tabla de profesores
                cursor.execute("SELECT cedula FROM profesores WHERE cedula = %s", (cedula_profesor,))
                existing_cedula = cursor.fetchone()

                if existing_cedula:
                    # Insertar la materia si la cédula del profesor existe
                    sql = "INSERT INTO materias (id_materia, nombre, cedula_profesor) VALUES (%s, %s, %s)"
                    data = (id_materia, nombre, cedula_profesor)
                    cursor.execute(sql, data)
                    mysql.connection.commit()
                    cursor.close()
                    flash('Materia añadida correctamente', 'success')
                else:
                    flash('Error: La cédula del profesor no existe en la base de datos', 'error')
        except Exception as e:
            flash(f'Error al agregar materia: {str(e)}', 'error')
    else:
        flash('Error: Debes completar todos los campos', 'error')
    
    return redirect(url_for('materias'))

#EDITAR MATERIAS
@app.route('/editmateria/<string:id_materia>', methods=['GET', 'POST'])
def editMateria(id_materia):
    if request.method == 'GET':
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM materias WHERE id_materia = %s", (id_materia,))
            materia = cursor.fetchone()
            cursor.close()

            if materia:
                return render_template('edit_materia.html', materia=materia)
            else:
                flash('Error: La materia no existe', 'error')
                return redirect(url_for('materias'))
        except Exception as e:
            flash(f'Error al obtener la materia: {str(e)}', 'error')
            return redirect(url_for('materias'))
    elif request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            cedula_profesor = request.form.get('cedula_profesor')
            nuevo_id_materia = request.form.get('id_materia')

            if nombre and cedula_profesor and nuevo_id_materia:
                cursor = mysql.connection.cursor()
                # Verificar si se intenta cambiar el ID de la materia
                if nuevo_id_materia != id_materia:
                    # Verificar si hay notas asociadas a la materia que se está intentando editar
                    cursor.execute("SELECT * FROM notas WHERE id_materia = %s", (id_materia,))
                    notas_asociadas = cursor.fetchall()

                    if notas_asociadas:
                        flash('Error: Existen notas asociadas a esta materia. Elimina las notas antes de cambiar el ID de la materia.', 'error')
                        return redirect(url_for('materias'))

                # Verificar si la cédula del profesor existe en la tabla de profesores
                cursor.execute("SELECT cedula FROM profesores WHERE cedula = %s", (cedula_profesor,))
                existing_cedula = cursor.fetchone()

                if existing_cedula:
                    # Actualizar la materia si la cédula del profesor existe
                    cursor.execute("UPDATE materias SET id_materia = %s, nombre = %s, cedula_profesor = %s WHERE id_materia = %s", (nuevo_id_materia, nombre, cedula_profesor, id_materia))
                    mysql.connection.commit()
                    cursor.close()
                    flash('Materia actualizada correctamente', 'success')
                else:
                    flash('Error: La cédula del profesor no existe en la base de datos', 'error')
            else:
                flash('Error: Debes completar todos los campos', 'error')

            return redirect(url_for('materias'))
        except Exception as e:
            flash(f'Error al editar materia: {str(e)}', 'error')
            return redirect(url_for('materias'))
#ELIMINAR MATERIAS
#
@app.route('/eliminarmateria/<string:id_materia>', methods=['GET'])
def deleteMateria(id_materia):
    try:
        cursor = mysql.connection.cursor()

        # Eliminar notas asociadas a la materia
        cursor.execute("DELETE FROM notas WHERE id_materia = %s", (id_materia,))

        # Eliminar la materia
        cursor.execute("DELETE FROM materias WHERE id_materia = %s", (id_materia,))
        
        mysql.connection.commit()
        cursor.close()
        flash('Materia y notas asociadas eliminadas correctamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar materia: {str(e)}', 'error')

    return redirect(url_for('materias'))
#EXCEL MATERIAS
@app.route('/generar_excel_materias')
def generar_excel_materias():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM materias")
        datos = cursor.fetchall()
        cursor.close()
        
        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(datos, columns=["ID Materia", "Nombre", "Cedula Profesor"])
        
        # Ajustar el formato de la columna 'ID Materia' para evitar notación científica
        df['ID Materia'] = df['ID Materia'].astype(str)  # Convertir a tipo cadena
        df['ID Materia'] = df['ID Materia'].apply(lambda x: f"'{x}")  # Agregar comilla simple
        
        # Obtener la fecha actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
        
        # Crear el nombre del archivo Excel
        nombre_archivo = f"datos_materias_{fecha_actual}.xlsx"
        
        # Crear un directorio temporal para almacenar el archivo
        directorio_temporal = tempfile.mkdtemp()
        
        # Combinar el directorio temporal con el nombre del archivo
        ruta_guardado = os.path.join(directorio_temporal, nombre_archivo)
        
        # Crear el archivo Excel
        with pd.ExcelWriter(ruta_guardado, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Materias')
            
            # Ajustar el ancho de las columnas
            worksheet = writer.sheets['Materias']
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(i, i, column_len + 2)
                
        return send_file(ruta_guardado, as_attachment=True)
    
    except Exception as e:
        flash(f'Error al generar el archivo Excel: {str(e)}', 'error')
        return redirect(url_for('materias'))
    
    ## NOTAS 
@app.route('/notas')
def notas():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM notas")  # Reemplaza 'notas' con el nombre de tu tabla
    myresult = cursor.fetchall()

    # Convertir a diccionario
    notaObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        notaObject.append(dict(zip(columnNames, record)))
    cursor.close()
    return render_template('notas.html', data=notaObject)

#GUARDAR NOTAS
@app.route('/guardar_nota', methods=['POST'])
def guardar_nota():
    try:
        cedula_estudiante = request.form.get('cedula_estudiante')
        id_materia = request.form.get('id_materia')
        nota = request.form.get('nota')

        if not cedula_estudiante or not id_materia or not nota:
            flash('Error: Debes completar todos los campos', 'error')
            return redirect(url_for('notas'))

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT cedula FROM estudiantes WHERE cedula = %s", (cedula_estudiante,))
        existing_cedula = cursor.fetchone()

        if not existing_cedula:
            flash('Error: La cédula del estudiante no existe en la base de datos', 'error')
            cursor.close()
            return redirect(url_for('notas'))

        cursor.execute("SELECT id_materia FROM materias WHERE id_materia = %s", (id_materia,))
        existing_id = cursor.fetchone()

        if not existing_id:
            flash('Error: El ID de la materia no existe en la base de datos', 'error')
            cursor.close()
            return redirect(url_for('notas'))

        sql = "INSERT INTO notas (cedula_estudiante, id_materia, nota) VALUES (%s, %s, %s)"
        data = (cedula_estudiante, id_materia, nota)
        cursor.execute(sql, data)
        mysql.connection.commit()
        cursor.close()
        
        flash('Nota guardada correctamente', 'success')
    except Exception as e:
        flash(f'Error al guardar la nota: {str(e)}', 'error')
    
    return redirect(url_for('notas'))

# EDITAR NOTAS
@app.route('/editarnota/<int:id_nota>', methods=['GET', 'POST'])
def editar_nota(id_nota):
    if request.method == 'POST':
        cedula_estudiante = request.form.get('cedula_estudiante')
        id_materia = request.form.get('id_materia')
        nota = request.form.get('nota')

        try:
            cursor = mysql.connection.cursor()

            # Verificar si la cédula del estudiante existe en la tabla de estudiantes
            cursor.execute("SELECT cedula FROM estudiantes WHERE cedula = %s", (cedula_estudiante,))
            existing_cedula_estudiante = cursor.fetchone()

            if not existing_cedula_estudiante:
                flash('Error: La cédula del estudiante no existe en la base de datos', 'error')
                return redirect(url_for('notas'))

            # Verificar si el ID de la materia existe en la tabla de materias
            cursor.execute("SELECT id_materia FROM materias WHERE id_materia = %s", (id_materia,))
            existing_id_materia = cursor.fetchone()

            if not existing_id_materia:
                flash('Error: El ID de la materia no existe en la base de datos', 'error')
                return redirect(url_for('notas'))

            # Actualizar la nota
            cursor.execute("UPDATE notas SET cedula_estudiante = %s, id_materia = %s, nota = %s WHERE id_nota = %s",
                           (cedula_estudiante, id_materia, nota, id_nota))
            mysql.connection.commit()
            cursor.close()

            flash('Nota actualizada correctamente', 'success')
        except Exception as e:
            flash(f'Error al actualizar la nota: {str(e)}', 'error')

        return redirect(url_for('notas'))
    else:
        try:
            cursor = mysql.connection.cursor()

            # Obtener la nota existente para mostrarla en el formulario de edición
            cursor.execute("SELECT * FROM notas WHERE id_nota = %s", (id_nota,))
            nota = cursor.fetchone()

            cursor.close()

            if not nota:
                flash('Error: La nota no existe', 'error')
                return redirect(url_for('notas'))

            return render_template('editar_nota.html', nota=nota)
        except Exception as e:
            flash(f'Error al cargar la página de edición de notas: {str(e)}', 'error')
            return redirect(url_for('notas'))

#ELIMINAR NOTA
@app.route('/DeleteNota/<int:id_nota>', methods=['GET'])
def DeleteNota(id_nota):
    try:
        cursor = mysql.connection.cursor()
        
        # Verificar si la nota existe
        cursor.execute("SELECT * FROM notas WHERE id_nota = %s", (id_nota,))
        existing_nota = cursor.fetchone()

        if not existing_nota:
            flash('Error: La nota que intentas eliminar no existe', 'error')
            return redirect(url_for('notas'))

        # Eliminar la nota
        cursor.execute("DELETE FROM notas WHERE id_nota = %s", (id_nota,))
        mysql.connection.commit()
        cursor.close()

        flash('Nota eliminada correctamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar la nota: {str(e)}', 'error')

    return redirect(url_for('notas'))

#EXCEL NOTAS
@app.route('/generar_excel_notas')
def generar_excel_notas():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id_nota, cedula_estudiante, id_materia, nota FROM notas")
        datos = cursor.fetchall()
        cursor.close()
        
        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(datos, columns=["ID Nota", "Cedula Estudiante", "ID Materia", "Nota"])
        
        # Obtener la fecha actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
        
        # Crear el nombre del archivo Excel
        nombre_archivo = f"datos_notas_{fecha_actual}.xlsx"
        
        # Crear un directorio temporal para almacenar el archivo
        directorio_temporal = tempfile.mkdtemp()
        
        # Combinar el directorio temporal con el nombre del archivo
        ruta_guardado = os.path.join(directorio_temporal, nombre_archivo)
        
        # Crear el archivo Excel
        with pd.ExcelWriter(ruta_guardado, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Notas')
            
            # Ajustar el ancho de las columnas
            worksheet = writer.sheets['Notas']
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(i, i, column_len + 2)
                
        return send_file(ruta_guardado, as_attachment=True)
    
    except Exception as e:
        flash(f'Error al generar el archivo Excel: {str(e)}', 'error')
        return redirect(url_for('notas'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
