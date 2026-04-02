import os, sys
import pymysql
import bcrypt
import yaml
from pymysql.err import MySQLError


def _load_db_config() -> dict:
    """Đọc cấu hình DB từ config.yaml (một cấp trên lib/)."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    config_path = os.path.join(base_path, "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Không tìm thấy config.yaml tại: {config_path}\n"
            "Sao chép config.yaml.example thành config.yaml và điền thông tin DB."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["database"]


def hash_password(plain: str) -> str:
    """Hash mật khẩu bằng bcrypt. Trả về chuỗi để lưu DB."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


def check_password(plain: str, hashed: str) -> bool:
    """Kiểm tra mật khẩu nhập vào so với hash đã lưu."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


class DatabaseConnection:
    """Quản lý kết nối MySQL với pymysql"""
    def __init__(self):
        try:
            cfg = _load_db_config()
            self.conn = pymysql.connect(
                host=cfg["host"],
                user=cfg["user"],
                password=cfg["password"],
                database=cfg["database"],
                cursorclass=pymysql.cursors.DictCursor,  # để trả về dict thay vì tuple
                autocommit=False                        # mình sẽ chủ động commit/rollback
            )
            self.cursor = self.conn.cursor()
        except MySQLError as e:
            print(f"Lỗi kết nối: {e}")
            raise

    def execute(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self.conn.commit()
        except MySQLError as e:
            print(f"Lỗi SQL: {e}")
            self.conn.rollback()
            raise

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

class BaseModel:
    """ORM mini base - classmethod version"""
    table_name = ""
    primary_key = "id"
    allowed_columns = []  # Subclass override với danh sách cột hợp lệ
    db: DatabaseConnection = None  # kết nối dùng chung cho mọi class

    @classmethod
    def _validate_column(cls, column: str):
        """Validate tên cột để chống SQL injection"""
        if cls.allowed_columns and column not in cls.allowed_columns:
            raise ValueError(f"Invalid column '{column}' for {cls.table_name}. Allowed: {cls.allowed_columns}")

    @classmethod
    def use_db(cls, db: DatabaseConnection):
        """Gán DB connection dùng chung"""
        cls.db = db

    @classmethod
    def insert(cls, data: dict):
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {cls.table_name} ({cols}) VALUES ({placeholders})"
        cls.db.execute(query, tuple(data.values()))

    @classmethod
    def get_all(cls):
        query = f"SELECT * FROM {cls.table_name}"
        cls.db.execute(query)
        return cls.db.fetchall()

    @classmethod
    def get_by(cls, column: str, value):
        """Lấy hang theo gia tri 1 cột bất kỳ"""
        cls._validate_column(column)
        query = f"SELECT * FROM {cls.table_name} WHERE {column}=%s"
        cls.db.execute(query, (value,))
        return cls.db.fetchall()

    @classmethod
    def get_column(cls, column: str):
        """
        Lấy toàn bộ giá trị của 1 cột trong bảng
        Trả về list
        """
        cls._validate_column(column)
        query = f"SELECT {column} FROM {cls.table_name}"
        cls.db.execute(query)
        rows = cls.db.fetchall()

        result = []
        for row in rows:
            if isinstance(row, dict):  # Nếu cursor trả về dict
                result.append(row[column])
            else:  # Nếu cursor trả về tuple
                result.append(row[0])
        return result
    
    @classmethod
    def get_columns_by(cls, select_cols: list, where: dict):
        """
        Lấy giá trị từ nhiều cột với điều kiện nhiều cột
        Ví dụ:
        BaseModel.get_columns_by(
            ["UserID", "UserName", "Role"],
            {"UserName": "abc", "PasswordHash": "xyz"}
        )
        """
        for col in select_cols + list(where.keys()):
            cls._validate_column(col)
        cols = ", ".join(select_cols)
        where_clause = " AND ".join([f"{col}=%s" for col in where.keys()])
        query = f"SELECT {cols} FROM {cls.table_name} WHERE {where_clause}"
        cls.db.execute(query, tuple(where.values()))
        return cls.db.fetchall()
    
    @classmethod
    def update(cls, column: str, value, updates: dict):
        # Validate cột where và cột update
        cls._validate_column(column)
        for col in updates.keys():
            cls._validate_column(col)
        set_clause = ", ".join([f"`{col}`=%s" for col in updates.keys()])
        query = f"UPDATE {cls.table_name} SET {set_clause} WHERE `{column}`=%s"
        values = list(updates.values()) + [value]
        cls.db.execute(query, tuple(values))

    @classmethod
    def delete(cls, column: str, value):
        cls._validate_column(column)
        query = f"DELETE FROM {cls.table_name} WHERE {column}=%s"
        cls.db.execute(query, (value,))

    @classmethod
    def insert_or_update(cls, data: dict):
        """
        Thêm bản ghi, nếu trùng khóa chính thì update
        """
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        updates = ", ".join([f"{col}=VALUES({col})" for col in data.keys()])

        query = f"""
            INSERT INTO {cls.table_name} ({cols})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {updates}
        """
        cls.db.execute(query, tuple(data.values()))

    

    @classmethod
    def update_by_two(cls, col1: str, val1, col2: str, val2, updates: dict):
        cls._validate_column(col1)
        cls._validate_column(col2)
        for col in updates.keys():
            cls._validate_column(col)
        set_clause = ", ".join([f"`{col}`=%s" for col in updates.keys()])
        query = f"UPDATE `{cls.table_name}` SET {set_clause} WHERE `{col1}`=%s AND `{col2}`=%s"
        values = list(updates.values()) + [val1, val2]
        cls.db.execute(query, tuple(values))

# db = DatabaseConnection()
# BaseModel.use_db(db)

# ===== Model Classes với Column Validation =====

class AuditTrial(BaseModel):
    table_name = "auditlog"
    allowed_columns = ["ID", "UserName", "Action", "Details", "CreatedAt"]

class Product(BaseModel):
    table_name = "product"
    allowed_columns = ["ID", "ProductName", "DefaultNumber", "Exposure", "ThresholdAccept", "ThresholdMns", "CreatedAt", "UpdatedAt"]

class ProductReport(BaseModel):
    table_name = "productreport"
    allowed_columns = []  # Định nghĩa sau khi có schema

class CameraSetting(BaseModel):
    table_name = "camerasettings"
    allowed_columns = []  # Định nghĩa sau khi có schema

class User(BaseModel):
    table_name = "users"
    allowed_columns = ["UserID", "UserName", "FullName", "Department", "No_id", "PasswordHash", "Role", "Active", "Attempt", "LastLoginAt", "CreatedAt", "UpdatedAt"]

class LoginAudit(BaseModel):
    table_name = "loginaudit"
    allowed_columns = ["ID", "UserID", "UserName", "EventType", "IPAddress", "CreatedAt"]

class CurrentSession(BaseModel):
    table_name = "current_session"
    allowed_columns = ["ID", "UserName", "ResultTime", "SleepTime", "ZoomFactor", "OffsetX", "OffsetY", "ImageWidth", "ImageHeight", "PLCIP", "PLCProtocol", "PLCPort", "ROIx1", "ROIx2", "ROIx3", "ROIx4", "ROIx5", "ROIy1", "ROIy2", "ROIy3", "ROIy4", "ROIy5", "Token", "ExpiresAt", "CreatedAt", "UpdatedAt"]