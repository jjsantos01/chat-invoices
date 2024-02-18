import os
import xml.etree.ElementTree as ET
import sqlite3
import dotenv

dotenv.load_dotenv()

def check_factura_exists(conn, uuid):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM comprobantes WHERE uuid = ?", (uuid,))
    return cursor.fetchone() is not None

# Función para insertar un comprobante en la base de datos
def insert_comprobante(conn, comprobante_data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO comprobantes (
            uuid, version, fecha, sub_total, moneda, total, tipo_de_comprobante,
            exportacion, metodo_pago, lugar_expedicion, rfc_emisor, nombre_emisor,
            regimen_fiscal_emisor, rfc_receptor, nombre_receptor, regimen_fiscal_receptor,
            domicilio_fiscal_receptor, uso_cfdi
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', comprobante_data)
    conn.commit()
    return cursor.lastrowid

# Función para insertar un concepto en la base de datos
def insert_concepto(conn, concepto_data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conceptos (
            comprobante_id, clave_prod_serv, cantidad, clave_unidad,
            unidad, descripcion, valor_unitario, importe
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', concepto_data)
    conn.commit()
    return cursor.lastrowid

# Función para insertar un impuesto trasladado en la base de datos
def insert_impuesto_trasladado(conn, impuesto_data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO impuestos_trasladados (
            concepto_id, base, impuesto, tipo_factor, tasa_o_cuota, importe
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', impuesto_data)
    conn.commit()

# Función para insertar un impuesto retenido en la base de datos
def insert_impuesto_retenido(conn, impuesto_data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO impuestos_retenidos (
            concepto_id, base, impuesto, tipo_factor, tasa_o_cuota, importe
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', impuesto_data)
    conn.commit()

# Función para insertar los totales de impuestos en la base de datos
def insert_impuestos_total(conn, impuestos_total_data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO impuestos_total (
            comprobante_id, total_impuestos_trasladados, total_impuestos_retenidos
        ) VALUES (?, ?, ?)
    ''', impuestos_total_data)
    conn.commit()

# Función principal para procesar la factura electrónica
def process_factura_electronica(xml_file_path, database_name):
    # Conectar a la base de datos
    conn = sqlite3.connect(database_name)

    # Parsear el archivo XML
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
    uuid = root.find('.//cfdi:Complemento', namespaces=namespaces).find('{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital').get('UUID')
    if check_factura_exists(conn, uuid):
        print(f"La factura con UUID {uuid} ya está registrada en la base de datos.")
        conn.close()
        return
    # Obtener datos del comprobante
    comprobante_data = [
        uuid,
        root.get('Version'),
        root.get('Fecha'),
        float(root.get('SubTotal', 0)),
        root.get('Moneda'),
        float(root.get('Total', 0)),
        root.get('TipoDeComprobante'),
        root.get('Exportacion'),
        root.get('MetodoPago'),
        root.get('LugarExpedicion'),
        root.find('.//cfdi:Emisor', namespaces=namespaces).get('Rfc'),
        root.find('.//cfdi:Emisor', namespaces=namespaces).get('Nombre'),
        root.find('.//cfdi:Emisor', namespaces=namespaces).get('RegimenFiscal'),
        root.find('.//cfdi:Receptor', namespaces=namespaces).get('Rfc'),
        root.find('.//cfdi:Receptor', namespaces=namespaces).get('Nombre'),
        root.find('.//cfdi:Receptor', namespaces=namespaces).get('RegimenFiscalReceptor'),
        root.find('.//cfdi:Receptor', namespaces=namespaces).get('DomicilioFiscalReceptor'),
        root.find('.//cfdi:Receptor', namespaces=namespaces).get('UsoCFDI'),
    ]

    # Insertar comprobante en la base de datos
    comprobante_id = insert_comprobante(conn, comprobante_data)

    # Procesar los conceptos
    for concepto in root.findall('.//cfdi:Concepto', namespaces=namespaces):
        concepto_data = [
            comprobante_id,
            concepto.get('ClaveProdServ'),
            float(concepto.get('Cantidad', 0)),
            concepto.get('ClaveUnidad'),
            concepto.get('Unidad'),
            concepto.get('Descripcion'),
            float(concepto.get('ValorUnitario', 0)),
            float(concepto.get('Importe', 0))
        ]

        # Insertar concepto en la base de datos
        concepto_id = insert_concepto(conn, concepto_data)

        # Procesar impuestos trasladados
        for impuesto_trasladado in concepto.findall('.//cfdi:Traslado', namespaces=namespaces):
            impuesto_data = [
                concepto_id,
                float(impuesto_trasladado.get('Base', 0)),
                impuesto_trasladado.get('Impuesto'),
                impuesto_trasladado.get('TipoFactor'),
                float(impuesto_trasladado.get('TasaOCuota', 0)),
                float(impuesto_trasladado.get('Importe', 0))
            ]

            # Insertar impuesto trasladado en la base de datos
            insert_impuesto_trasladado(conn, impuesto_data)

        # Procesar impuestos retenidos
        for impuesto_retenido in concepto.findall('.//cfdi:Retencion', namespaces=namespaces):
            impuesto_data = [
                concepto_id,
                float(impuesto_retenido.get('Base', 0)),
                impuesto_retenido.get('Impuesto'),
                impuesto_retenido.get('TipoFactor'),
                float(impuesto_retenido.get('TasaOCuota', 0)),
                float(impuesto_retenido.get('Importe', 0))
            ]

            # Insertar impuesto retenido en la base de datos
            insert_impuesto_retenido(conn, impuesto_data)

    # Obtener datos de impuestos totales
    impuestos_element = root.find('cfdi:Impuestos', namespaces=namespaces)
    impuestos_total_data = [comprobante_id]
    if impuestos_element:
        impuestos_total_data.append(impuestos_element.get('TotalImpuestosTrasladados', 0)),
        impuestos_total_data.append(impuestos_element.get('TotalImpuestosRetenidos', 0))
    else:
        impuestos_total_data += [None, None]

    # Insertar impuestos totales en la base de datos
    insert_impuestos_total(conn, impuestos_total_data)

    # Cerrar la conexión
    conn.close()

def process_facturas(xml_folder_path, database_name):
    # Obtener la lista de archivos XML en el directorio
    xml_files = [file for file in os.listdir(xml_folder_path) if file.endswith('.xml')]

    # Iterar sobre cada archivo XML
    for xml_file in xml_files:
        # Construir la ruta completa del archivo
        xml_file_path = os.path.join(xml_folder_path, xml_file)

        # Llamar a la función process_factura_electronica para procesar cada archivo
        process_factura_electronica(xml_file_path, database_name)

# Ruta del archivo XML de la factura electrónica
xml_folder_path = os.environ["XML_FOLDER"]
database_name = os.environ["DATABASE_FILE"]

process_facturas(xml_folder_path, database_name)
