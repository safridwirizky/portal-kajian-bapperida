from datetime import datetime
import os

from flask import current_app, Flask, flash, redirect, render_template, url_for
from flask.typing import ResponseReturnValue
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, login_required

from auth import auth_bp
from forms import DokumenForm, KajianForm, csrf
from models import Dokumen, Kajian, User, db
from services import DriveFile, drive


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

BULAN = (
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
)


# ==============================================================================
# APP CONFIGURATION
# ==============================================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "development-secret",
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(app.instance_path, "kajian.db")
)

csrf.init_app(app)
db.init_app(app)

bootstrap = Bootstrap5(app)


# ==============================================================================
# LOGIN
# ==============================================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

app.register_blueprint(auth_bp)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ==============================================================================
# SEED
# ==============================================================================

def seed_admin() -> None:
    """Membuat akun admin default jika belum tersedia."""

    admin = User.query.filter_by(
        username=DEFAULT_ADMIN_USERNAME,
    ).first()

    if admin:
        return

    admin = User(
        username=DEFAULT_ADMIN_USERNAME,
        role="admin",
    )

    admin.set_password(DEFAULT_ADMIN_PASSWORD)

    db.session.add(admin)
    db.session.commit()

    print("✓ Default admin berhasil dibuat.")


with app.app_context():
    db.create_all()
    seed_admin()


# ==============================================================================
# HELPERS
# ==============================================================================

def get_kajian(id: int) -> Kajian:
    """Mengambil data kajian berdasarkan ID."""
    return db.get_or_404(
        Kajian,
        id,
    )


def render_kajian_form(
    form: KajianForm,
    *,
    is_edit: bool,
    kajian: Kajian | None = None,
):
    """Render halaman tambah/edit kajian."""
    return render_template(
        "kajian_form.html",
        form=form,
        is_edit=is_edit,
        kajian=kajian,
    )


def save_kajian(
    kajian: Kajian,
    form: KajianForm,
) -> None:
    """Mengisi model Kajian dari form."""

    kajian.judul = form.judul.data
    kajian.tahun = form.tahun.data
    kajian.deskripsi = form.deskripsi.data
    kajian.hasil = form.hasil.data


@app.context_processor
def inject_app_name() -> dict[str, str]:
    return {
        "APP_NAME": "Portal Kajian Bapperida Kabupaten Rote Ndao"
    }


# ==============================================================================
# TEMPLATE FILTERS
# ==============================================================================

@app.template_filter("format_tanggal")
def format_tanggal(
    dt: datetime | None,
) -> str:

    if dt is None:
        return "-"

    return (
        f"{dt.day} "
        f"{BULAN[dt.month - 1]} "
        f"{dt.year}"
    )


# ==============================================================================
# PUBLIC
# ==============================================================================

@app.get("/")
def home() -> str:

    kajian_list = (
        Kajian.query
        .order_by(
            Kajian.tahun.desc(),
            Kajian.judul.asc(),
        )
        .all()
    )

    return render_template(
        "index.html",
        kajian_list=kajian_list
    )


@app.get("/kajian/<int:id>")
def detail_kajian(id: int) -> str:

    kajian = get_kajian(id)

    form = DokumenForm()

    return render_template(
        "detail.html",
        kajian=kajian,
        form=form,
    )


# ==============================================================================
# TAMBAH KAJIAN
# ==============================================================================

@app.get("/kajian/tambah")
@login_required
def tambah_kajian() -> str:

    form = KajianForm()

    return render_kajian_form(
        form=form,
        is_edit=False
    )


@app.post("/kajian/tambah")
@login_required
def simpan_kajian() -> ResponseReturnValue:

    form = KajianForm()

    if not form.validate_on_submit():
        return render_kajian_form(
            form=form,
            is_edit=False,
        )

    kajian = Kajian()

    save_kajian(
        kajian=kajian,
        form=form,
    )

    kajian_folder_id = None

    try:
        kajian_folder_id = drive.create_kajian_folder(
            tahun=kajian.tahun,
            judul=kajian.judul,
        )

        kajian.drive_folder_id = kajian_folder_id

        db.session.add(kajian)
        db.session.commit()

    except Exception:
        db.session.rollback()

        if kajian_folder_id is not None:
            try:
                drive.delete(kajian_folder_id)
            except Exception:
                current_app.logger.exception(
                    "Gagal menghapus orphan folder."
                )

        current_app.logger.exception(
            "Gagal membuat kajian."
        )

        flash(
            "Kajian gagal ditambahkan.",
            "danger",
        )

        return render_kajian_form(
            form=form,
            is_edit=False,
        )

    else:

        flash(
            "Kajian berhasil ditambahkan.",
            "success",
        )

        return redirect(
            url_for(
                "detail_kajian",
                id=kajian.id,
            )
        )


# ==============================================================================
# EDIT KAJIAN
# ==============================================================================

@app.get("/kajian/<int:id>/edit")
@login_required
def edit_kajian(id: int) -> str:

    kajian = get_kajian(id)

    form = KajianForm(
        obj=kajian
    )

    return render_kajian_form(
        form=form,
        is_edit=True,
        kajian=kajian
    )


@app.post("/kajian/<int:id>/edit")
@login_required
def update_kajian(id: int) -> ResponseReturnValue:

    kajian = get_kajian(id)

    form = KajianForm()

    if not form.validate_on_submit():
        return render_kajian_form(
            form=form,
            is_edit=True,
            kajian=kajian
        )

    save_kajian(
        kajian=kajian,
        form=form
    )

    db.session.commit()

    return redirect(
        url_for(
            "detail_kajian",
            id=kajian.id
        )
    )


# ==============================================================================
# UPLOAD FILE KAJIAN
# ==============================================================================

@app.post("/kajian/<int:kajian_id>/dokumen")
@login_required
def upload_dokumen(kajian_id: int) -> ResponseReturnValue:
    kajian = get_kajian(kajian_id)

    form = DokumenForm()

    if not form.validate_on_submit():
        return render_template(
            "detail.html",
            kajian=kajian,
            form=form,
        )

    uploaded = DriveFile.from_upload(
        form.file.data,
    )

    drive_file_id = None

    try:
        drive_file_id = drive.upload_file(
            folder_id=kajian.drive_folder_id,
            file=uploaded,
        )

        dokumen = Dokumen(
            kajian=kajian,
            judul=form.judul.data,
            nama_file=uploaded.filename,
            mime_type=uploaded.mimetype,
            urutan=form.urutan.data,
            drive_file_id=drive_file_id,
        )

        db.session.add(dokumen)
        db.session.commit()

    except Exception:
        db.session.rollback()

        if drive_file_id is not None:
            try:
                drive.delete(drive_file_id)
            except Exception:
                current_app.logger.exception(
                    "Gagal menghapus orphan file."
                )

        current_app.logger.exception(
            "Gagal mengunggah dokumen."
        )

        flash(
            "Dokumen gagal diunggah.",
            "danger",
        )

    else:
        flash(
            "Dokumen berhasil diunggah.",
            "success",
        )

    return redirect(
        url_for(
            "detail_kajian",
            id=kajian.id,
        )
    )


# ==============================================================================
# HAPUS KAJIAN
# ==============================================================================

@app.post("/kajian/<int:id>/hapus")
@login_required
def hapus_kajian(id: int) -> ResponseReturnValue:

    kajian = get_kajian(id)

    db.session.delete(kajian)
    db.session.commit()

    return redirect(
        url_for("home")
    )


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    app.run(debug=True)
