from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect

from flask_wtf.file import (
    FileAllowed,
    FileField,
    FileRequired,
)

from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)

from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
)


ALLOWED_DOCUMENT_EXTENSIONS = (
    "pdf",
    "png",
    "jpg",
    "jpeg",
)


csrf = CSRFProtect()


class KajianForm(FlaskForm):
    judul = StringField(
        "Judul Kajian",
        validators=[
            DataRequired(
                message="Judul wajib diisi."
            ),
            Length(max=255),
        ]
    )

    tahun = IntegerField(
        "Tahun",
        validators=[
            DataRequired(
                message="Tahun wajib diisi."
            ),
            NumberRange(
                min=2000,
                max=2100,
            ),
        ]
    )

    deskripsi = TextAreaField(
        "Deskripsi Kajian",
        validators=[
            DataRequired(
                message="Deskripsi wajib diisi."
            )
        ],
        render_kw={
            "rows": 5
        }
    )

    hasil = TextAreaField(
        "Hasil Kajian",
        validators=[
            DataRequired(
                message="Hasil wajib diisi."
            )
        ],
        render_kw={
            "rows": 5
        }
    )

    submit = SubmitField(
        "Simpan"
    )


class DokumenForm(FlaskForm):
    judul = StringField(
        "Judul Dokumen",
        validators=[
            DataRequired(
                message="Judul dokumen wajib diisi."
            ),
            Length(max=255),
        ]
    )

    file = FileField(
        "File",
        validators=[
            FileRequired(),
            FileAllowed(
                ALLOWED_DOCUMENT_EXTENSIONS,
                "File harus berupa PDF atau gambar."
            )
        ]
    )

    submit = SubmitField(
        "Upload"
    )


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(
                message="Username wajib diisi."
            )
        ],
        render_kw={
            "autocomplete": "username"
        }
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(
                message="Password wajib diisi."
            )
        ],
        render_kw={
            "autocomplete": "current-password"
        }
    )

    remember_me = BooleanField(
        "Remember Me"
    )

    submit = SubmitField(
        "Login"
    )


class EmptyForm(FlaskForm):
    pass
