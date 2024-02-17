import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# Función para crear la tabla 'comprobantes'
def create_comprobantes_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comprobantes (
            id INTEGER PRIMARY KEY,
            uuid TEXT UNIQUE,
            version TEXT,
            fecha TEXT,
            sub_total REAL,
            moneda TEXT,
            total REAL,
            tipo_de_comprobante TEXT,
            exportacion TEXT,
            metodo_pago TEXT,
            lugar_expedicion TEXT,
            rfc_emisor TEXT,
            nombre_emisor TEXT,
            regimen_fiscal_emisor TEXT,
            rfc_receptor TEXT,
            nombre_receptor TEXT,
            regimen_fiscal_receptor TEXT,
            domicilio_fiscal_receptor TEXT,
            uso_cfdi TEXT
        )
    ''')
    conn.commit()

# Función para crear la tabla 'conceptos'
def create_conceptos_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conceptos (
            id INTEGER PRIMARY KEY,
            comprobante_id INTEGER,
            clave_prod_serv TEXT,
            cantidad REAL,
            clave_unidad TEXT,
            unidad TEXT,
            descripcion TEXT,
            valor_unitario REAL,
            importe REAL,
            FOREIGN KEY (comprobante_id) REFERENCES comprobantes(id)
        )
    ''')
    conn.commit()

# Función para crear la tabla 'impuestos_trasladados'
def create_impuestos_trasladados_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS impuestos_trasladados (
            id INTEGER PRIMARY KEY,
            concepto_id INTEGER,
            base REAL,
            impuesto TEXT,
            tipo_factor TEXT,
            tasa_o_cuota REAL,
            importe REAL,
            FOREIGN KEY (concepto_id) REFERENCES conceptos(id)
        )
    ''')
    conn.commit()

# Función para crear la tabla 'impuestos_retenidos'
def create_impuestos_retenidos_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS impuestos_retenidos (
            id INTEGER PRIMARY KEY,
            concepto_id INTEGER,
            base REAL,
            impuesto TEXT,
            tipo_factor TEXT,
            tasa_o_cuota REAL,
            importe REAL,
            FOREIGN KEY (concepto_id) REFERENCES conceptos(id)
        )
    ''')
    conn.commit()

# Función para crear la tabla 'impuestos_total'
def create_impuestos_total_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS impuestos_total (
            id INTEGER PRIMARY KEY,
            comprobante_id INTEGER,
            total_impuestos_trasladados REAL,
            total_impuestos_retenidos REAL,
            FOREIGN KEY (comprobante_id) REFERENCES comprobantes(id)
        )
    ''')
    conn.commit()

# Función principal para crear la base de datos
def create_database(database_name):
    conn = sqlite3.connect(database_name)

    # Crear las tablas
    create_comprobantes_table(conn)
    create_conceptos_table(conn)
    create_impuestos_trasladados_table(conn)
    create_impuestos_retenidos_table(conn)
    create_impuestos_total_table(conn)

    # Cerrar la conexión
    conn.close()

# Nombre de la base de datos
database_name = os.environ["DATABASE_FILE"]

# Crear la base de datos
create_database(database_name)
