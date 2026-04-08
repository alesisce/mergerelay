from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
import bcrypt
import time

class Database:
    def __init__(self, host, user, password, database):
        self.pool = MySQLConnectionPool(
            pool_name="irc_pool",
            pool_size=10,
            host=host,
            user=user,
            password=password,
            database=database,
            autocommit=True
        )

        self.setup_tables()

    def get_connection(self):
        return self.pool.get_connection()

    def get_cursor(self, dictionary=True):
        conn = self.get_connection()
        return conn, conn.cursor(dictionary=dictionary)

    def setup_tables(self):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    last_online INT,
                    staff BOOLEAN DEFAULT FALSE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    short_description TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    channel_id INT NOT NULL,
                    user_id INT NOT NULL,
                    role ENUM('member','mod','owner') DEFAULT 'member',

                    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

                    UNIQUE(channel_id, user_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bans (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    channel_id INT NOT NULL,
                    user_id INT NOT NULL,
                    banned_by INT NOT NULL,
                    reason TEXT,
                    created_at INT,

                    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (banned_by) REFERENCES users(id) ON DELETE CASCADE,

                    UNIQUE(channel_id, user_id)
                )
            """)

        finally:
            cursor.close()
            conn.close()

    def create_user(self, name, password):
        conn, cursor = self.get_cursor()
        try:
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            now = int(time.time())

            cursor.execute(
                "INSERT INTO users (name,password,last_online) VALUES (%s,%s,%s)",
                (name, hashed_pw, now)
            )
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print("Error creando usuario:", e)
            return None
        finally:
            cursor.close()
            conn.close()

    def verify_user_login(self, name, password):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute("SELECT id,password FROM users WHERE name=%s", (name,))
            user = cursor.fetchone()

            if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
                return user["id"]

            return None
        finally:
            cursor.close()
            conn.close()

    def get_channel_participants(self, channel_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute("""
                SELECT u.id,u.name,u.last_online,p.role
                FROM users u
                JOIN participants p ON u.id=p.user_id
                WHERE p.channel_id=%s
            """, (channel_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def is_channel_participant(self, channel_id, user_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM participants WHERE channel_id=%s AND user_id=%s LIMIT 1",
                (channel_id,user_id)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conn.close()

    def add_channel_participant(self, channel_id, user_id, role="member"):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "INSERT INTO participants (channel_id,user_id,role) VALUES (%s,%s,%s)",
                (channel_id,user_id,role)
            )
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print("Error añadiendo participante:", e)
            return None
        finally:
            cursor.close()
            conn.close()

    def remove_channel_participant(self, channel_id, user_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "DELETE FROM participants WHERE channel_id=%s AND user_id=%s",
                (channel_id,user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()

    def leave_channel(self, channel_id, user_id):
        return self.remove_channel_participant(channel_id, user_id)

    def has_participants(self, channel_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM participants WHERE channel_id=%s LIMIT 1",
                (channel_id,)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conn.close()
    
    def get_channel_by_id(self, channel_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "SELECT id,name,short_description FROM channels WHERE id=%s LIMIT 1",
                (channel_id,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def get_channel_by_name(self, name):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "SELECT id,name,short_description FROM channels WHERE name=%s LIMIT 1",
                (name,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def get_user_channels(self, user_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute("""
                SELECT c.id,c.name,c.short_description
                FROM channels c
                JOIN participants p ON c.id=p.channel_id
                WHERE p.user_id=%s
            """, (user_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def get_user_role(self, channel_id, user_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "SELECT role FROM participants WHERE channel_id=%s AND user_id=%s",
                (channel_id,user_id)
            )
            r = cursor.fetchone()
            return r["role"] if r else None
        finally:
            cursor.close()
            conn.close()

    def ban_user(self, channel_id, user_id, banned_by, reason=None):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute("""
                INSERT INTO bans (channel_id,user_id,banned_by,reason,created_at)
                VALUES (%s,%s,%s,%s,%s)
            """, (channel_id,user_id,banned_by,reason,int(time.time())))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    def unban_user(self, channel_id, user_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "DELETE FROM bans WHERE channel_id=%s AND user_id=%s",
                (channel_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()

    def is_banned(self, channel_id, user_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM bans WHERE channel_id=%s AND user_id=%s LIMIT 1",
                (channel_id, user_id)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conn.close()

    def get_ban(self, channel_id, user_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute("""
                SELECT 
                    b.id,
                    b.channel_id,
                    b.user_id,
                    b.reason,
                    b.created_at,
                    u.name AS banned_by_name
                FROM bans b
                JOIN users u ON b.banned_by = u.id
                WHERE b.channel_id=%s AND b.user_id=%s
                LIMIT 1
            """, (channel_id, user_id))

            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def delete_channel(self, channel_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "DELETE FROM channels WHERE id=%s",
                (channel_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()
    
    def delete_user(self, user_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "DELETE FROM users WHERE id=%s",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()
        
    def get_user_by_id(self, user_id):
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(
                "SELECT id, name, last_online, staff FROM users WHERE id=%s LIMIT 1",
                (user_id,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def create_channel(self, name, description):
        conn, cursor = self.get_cursor()
        try:
            sql = "INSERT INTO channels (name, short_description) VALUES (%s, %s)"
            cursor.execute(sql, (name, description))
            return cursor.lastrowid
        except Error as e:
            print(f"Error creando canal: {e}")
            return None
        finally:
            cursor.close()
            conn.close()