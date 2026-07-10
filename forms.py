from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileAllowed, FileField

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
    NumberRange,
)

csrf = CSRFProtect()


class KajianForm(FlaskForm):
    judul = StringField(
        "Judul Kajian",
        validators=[DataRequired()]
    )

    tahun = IntegerField(
        "Tahun",
        validators=[
            DataRequired(),
            NumberRange(
                min=2000,
                max=2100
            )
        ]
    )

    deskripsi = TextAreaField(
        "Deskripsi Kajian",
        validators=[DataRequired()]
    )

    hasil = TextAreaField(
        "Hasil Kajian",
        validators=[DataRequired()]
    )

    submit = SubmitField(
        "Simpan"
    )


class DokumenForm(FlaskForm):
    judul = StringField(
        "Judul Dokumen",
        validators=[DataRequired()]
    )

    file = FileField(
        "File",
        validators=[
            DataRequired(),
            FileAllowed(
                ["pdf", "png", "jpg", "jpeg"],
                "File harus berupa PDF atau gambar."
            )
        ]
    )

    urutan = IntegerField(
        "Urutan",
        default=1,
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )

    submit = SubmitField(
        "Upload"
    )


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired()],
        render_kw={
            "autocomplete": "username"
        }
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()],
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
