import sqlite3

DB_NAME = "db.sqlite"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def crear_tablas():
    conn = get_connection()
    cursor = conn.cursor()

    # -------------------------------
    # TABLA: encabezado_transaccion
    # -------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS encabezado_transaccion (
        id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        transaccion INTEGER,          -- 1 venta, 2 compra, 3 transferencia
        no_envio TEXT,
        tipo_venta TEXT,
        metodo_pago TEXT,
        bodega1 TEXT,
        bodega2 TEXT,
        id_cliente TEXT,
        proveedor TEXT,
        total REAL
    )
    """)

    # -------------------------------
    # TABLA: detalle_transaccion
    # -------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalle_transaccion (
        id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
        id_transaccion INTEGER,
        fecha TEXT,
        sku TEXT,
        cantidad INTEGER,
        precio REAL,
        subtotal REAL,
        FOREIGN KEY (id_transaccion)
            REFERENCES encabezado_transaccion (id_transaccion)
    )
    """)

    conn.commit()
    conn.close()
