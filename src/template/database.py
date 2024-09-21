import pymysql

try:
    # Establece la conexión con la base de datos
    database = pymysql.connect(
        host='localhost',  # Cambia esto al host correcto
        user='root',  # Cambia esto al usuario correcto
        password='',  # Cambia esto a la contraseña correcta
        db='sistema_registro_notas'  # Cambia esto al nombre de la base de datos correcto
        ,port=3306
    )

    print("Conexión exitosa")

    # Crea un objeto cursor para ejecutar consultas
    cursor = database.cursor()

    # Ejemplo: consulta para seleccionar todos los registros de la tabla "Usuarios"
    cursor.execute("SELECT * FROM usuarios")
    rows = cursor.fetchall()

    # Imprime los resultados
    for row in rows:
        print(row)

    # Cierra la conexión
    database.close()

except Exception as ex:
    print("Error:", ex)
