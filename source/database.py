import mysql.connector
from mysql.connector import Error
import bcrypt
import time
import hashlib

class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.connect()
        self.setup_tables()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            # Para que los INSERT/UPDATE se guarden automáticamente
            self.connection.autocommit = True
        except Error as e:
            print(f"Error conectando a MySQL: {e}")

    def get_cursor(self, dictionary=True):
        # Reconectar si la conexión se ha perdido
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=dictionary)

    def setup_tables(self):
        cursor = self.get_cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    last_online INT,
                    token VARCHAR(255)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    short_description TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    channel_id INT NOT NULL,
                    user_id INT NOT NULL,
                    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
        except Error as e:
            print(f"Error creando tablas: {e}")
        finally:
            cursor.close()

    def create_user(self, name, password):
        cursor = self.get_cursor()
        try:
            # Hasheamos la contraseña con bcrypt
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            current_time = int(time.time())
            sql = "INSERT INTO users (name, password, last_online) VALUES (%s, %s, %s)"
            cursor.execute(sql, (name, hashed_pw, current_time))
            return cursor.lastrowid
        except Error as e:
            print(f"Error creando usuario: {e}")
            return None
        finally:
            cursor.close()

    def verify_user_login(self, name, password):
        cursor = self.get_cursor()
        try:
            sql = "SELECT id, password FROM users WHERE name = %s"
            cursor.execute(sql, (name,))
            user = cursor.fetchone()
            if user:
                # Verificamos la contraseña ingresada contra el hash guardado
                if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    return user['id']
            return None
        except Error as e:
            print(f"Error verificando login: {e}")
            return None
        finally:
            cursor.close()

    def get_user_by_id(self, user_id):
        cursor = self.get_cursor()
        try:
            sql = "SELECT * FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error obteniendo usuario completo: {e}")
            return None
        finally:
            cursor.close()

    def get_user_details(self, user_id):
        cursor = self.get_cursor()
        try:
            # Solo devuelve atributos no sensibles (excluimos password y token)
            sql = "SELECT id, name, last_online FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error obteniendo detalles del usuario: {e}")
            return None
        finally:
            cursor.close()

    def _hash_token(self, token):
        # Dado que necesitamos recuperar un token y hacer búsquedas, SHA-256 es lo apropiado
        # a diferencia de bcrypt que es demasiado lento para verificaciones por índice.
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def set_user_token(self, user_id, plain_token):
        cursor = self.get_cursor()
        try:
            hashed_token = self._hash_token(plain_token)
            sql = "UPDATE users SET token = %s WHERE id = %s"
            cursor.execute(sql, (hashed_token, user_id))
            return True
        except Error as e:
            print(f"Error guardando token: {e}")
            return False
        finally:
            cursor.close()

    def verify_token(self, plain_token):
        cursor = self.get_cursor()
        try:
            hashed_token = self._hash_token(plain_token)
            sql = "SELECT id FROM users WHERE token = %s"
            cursor.execute(sql, (hashed_token,))
            result = cursor.fetchone()
            if result:
                return result['id']
            return None
        except Error as e:
            print(f"Error verificando token: {e}")
            return None
        finally:
            cursor.close()

    def create_channel(self, name, description):
        cursor = self.get_cursor()
        try:
            sql = "INSERT INTO channels (name, short_description) VALUES (%s, %s)"
            cursor.execute(sql, (name, description))
            return cursor.lastrowid
        except Error as e:
            print(f"Error creando canal: {e}")
            return None
        finally:
            cursor.close()

    def delete_channel(self, channel_id):
        cursor = self.get_cursor()
        try:
            sql = "DELETE FROM channels WHERE id = %s"
            cursor.execute(sql, (channel_id,))
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error eliminando canal: {e}")
            return False
        finally:
            cursor.close()

    def delete_user(self, user_id):
        cursor = self.get_cursor()
        try:
            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error eliminando usuario: {e}")
            return False
        finally:
            cursor.close()

    def get_channel_participants(self, channel_id):
        cursor = self.get_cursor()
        try:
            sql = """
                SELECT u.id, u.name, u.last_online 
                FROM users u
                JOIN participants p ON u.id = p.user_id
                WHERE p.channel_id = %s
            """
            cursor.execute(sql, (channel_id,))
            return cursor.fetchall()  # Retorna lista de dicts sin token ni password
        except Error as e:
            print(f"Error obteniendo participantes del canal: {e}")
            return []
        finally:
            cursor.close()

    def is_channel_participant(self, channel_id, user_id):
        cursor = self.get_cursor()
        try:
            sql = "SELECT id FROM participants WHERE channel_id = %s AND user_id = %s"
            cursor.execute(sql, (channel_id, user_id))
            return cursor.fetchone() is not None
        except Error as e:
            print(f"Error comprobando si es participante: {e}")
            return False
        finally:
            cursor.close()

    def add_channel_participant(self, channel_id, user_id):
        cursor = self.get_cursor()
        try:
            if self.is_channel_participant(channel_id, user_id):
                return True
                
            sql = "INSERT INTO participants (channel_id, user_id) VALUES (%s, %s)"
            cursor.execute(sql, (channel_id, user_id))
            return cursor.lastrowid
        except Error as e:
            print(f"Error añadiendo participante: {e}")
            return None
        finally:
            cursor.close()

    def remove_channel_participant(self, channel_id, user_id):
        cursor = self.get_cursor()
        try:
            sql = "DELETE FROM participants WHERE channel_id = %s AND user_id = %s"
            cursor.execute(sql, (channel_id, user_id))
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error eliminando participante: {e}")
            return False
        finally:
            cursor.close()

    def get_user_channels(self, user_id):
        cursor = self.get_cursor()
        try:
            sql = """
                SELECT c.id, c.name, c.short_description 
                FROM channels c
                JOIN participants p ON c.id = p.channel_id
                WHERE p.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error obteniendo canales del usuario: {e}")
            return []
        finally:
            cursor.close()
