from datetime import datetime
from pathlib import Path

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="admin",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.password_hash, password)


class Kajian(db.Model):
    __tablename__ = "kajian"

    id: Mapped[int] = mapped_column(primary_key=True)

    judul: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    tahun: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    deskripsi: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    hasil: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    drive_folder_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    dokumen: Mapped[list["Dokumen"]] = relationship(
        "Dokumen",
        back_populates="kajian",
        cascade="all, delete-orphan",
        order_by="Dokumen.urutan"
    )

    def __repr__(self):

        return f"<Kajian {self.id}: {self.judul}>"


class Dokumen(db.Model):
    __tablename__ = "dokumen"

    id: Mapped[int] = mapped_column(primary_key=True)

    kajian_id: Mapped[int] = mapped_column(
        ForeignKey("kajian.id"),
        nullable=False,
        index=True
    )

    judul: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    nama_file: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    urutan: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    drive_file_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    kajian: Mapped["Kajian"] = relationship(
        "Kajian",
        back_populates="dokumen"
    )

    def __repr__(self):

        return f"<Dokumen {self.id}: {self.nama_file}>"
    
    @property
    def ekstensi(self) -> str:

        return Path(
            self.nama_file
        ).suffix.lower()

    @property
    def is_pdf(self):

        return self.mime_type == "application/pdf"
    
    @property
    def is_image(self) -> bool:
        return self.mime_type.startswith("image/")
