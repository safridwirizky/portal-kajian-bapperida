from datetime import datetime
import os

from flask import current_app, Flask, flash, redirect, render_template, request, send_file, url_for
from flask.typing import ResponseReturnValue
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, login_required
from sqlalchemy import or_

from auth import auth_bp
from forms import DokumenForm, EmptyForm, KajianForm, csrf
from models import Dokumen, Kajian, User, db
from services import DriveFile, drive


DEFAULT_ADMIN_USERNAME = os.getenv(
    "DEFAULT_ADMIN_USERNAME"
)
DEFAULT_ADMIN_PASSWORD = os.getenv(
    "DEFAULT_ADMIN_PASSWORD"
)

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

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Buat folder instance jika belum ada
os.makedirs(app.instance_path, exist_ok=True)

db_path = os.path.join(app.instance_path, "kajian.db")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{db_path}"
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

def get_dokumen(id: int) -> Dokumen:
    """Mengambil data dokumen berdasarkan ID."""
    return db.get_or_404(
        Dokumen,
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

    search = request.args.get(
        "search",
        "",
    ).strip()

    query = Kajian.query

    if search:

        keyword = f"%{search}%"

        filters = [
            Kajian.judul.ilike(keyword),
            Kajian.deskripsi.ilike(keyword),
            Kajian.hasil.ilike(keyword),
        ]

        if search.isdigit():
            filters.append(
                Kajian.tahun == int(search)
            )

        query = query.filter(
            or_(*filters)
        )

    kajian_list = (
        query
        .order_by(
            Kajian.tahun.desc(),
            Kajian.judul.asc(),
        )
        .all()
    )

    form = EmptyForm()

    return render_template(
        "index.html",
        kajian_list=kajian_list,
        form=form,
        search=search,
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
            kajian=kajian,
        )

    old_judul = kajian.judul
    old_tahun = kajian.tahun

    tahun_changed = (
        form.tahun.data != old_tahun
    )

    judul_changed = (
        form.judul.data != old_judul
    )

    try:

        if tahun_changed:

            drive.move_kajian_folder(
                kajian.drive_folder_id,
                form.tahun.data,
            )

        if judul_changed:

            drive.rename_folder(
                kajian.drive_folder_id,
                form.judul.data,
            )

        save_kajian(
            kajian=kajian,
            form=form,
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        current_app.logger.exception(
            "Gagal memperbarui kajian."
        )

        flash(
            "Kajian gagal diperbarui.",
            "danger",
        )

    else:

        flash(
            "Kajian berhasil diperbarui.",
            "success",
        )

    return redirect(
        url_for(
            "detail_kajian",
            id=kajian.id,
        )
    )


# ==============================================================================
# UPLOAD FILE KAJIAN
# ==============================================================================

@app.post("/kajian/<int:kajian_id>/dokumen")
@login_required
def upload(kajian_id: int) -> ResponseReturnValue:
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
        drive_file_id = drive.upload(
            folder_id=kajian.drive_folder_id,
            file=uploaded,
        )

        dokumen = Dokumen(
            kajian=kajian,
            judul=form.judul.data,
            nama_file=uploaded.filename,
            mime_type=uploaded.mimetype,
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
# DOWNLOAD FILE KAJIAN
# ==============================================================================

@app.get("/dokumen/<int:id>/download")
def download(
    id: int,
) -> ResponseReturnValue:

    dokumen = db.get_or_404(
        Dokumen,
        id,
    )

    stream = drive.download(
        dokumen.drive_file_id,
    )

    return send_file(
        stream,
        mimetype=dokumen.mime_type,
        as_attachment=True,
        download_name=dokumen.nama_file,
    )

# ==============================================================================
# HAPUS KAJIAN
# ==============================================================================

@app.post("/kajian/<int:id>/hapus")
@login_required
def hapus_kajian(id: int) -> ResponseReturnValue:

    kajian = get_kajian(id)

    try:

        drive.delete_folder(
            kajian.drive_folder_id,
        )

        db.session.delete(
            kajian,
        )

        db.session.commit()

        flash(
            "Kajian berhasil dihapus.",
            "success",
        )

    except Exception:

        db.session.rollback()

        flash(
            "Kajian gagal dihapus.",
            "danger",
        )

    return redirect(
        url_for("home")
    )

# ==============================================================================
# HAPUS DOKUMEN
# ==============================================================================

@app.post("/dokumen/<int:id>/hapus")
@login_required
def hapus_dokumen(id: int) -> ResponseReturnValue:

    dokumen = get_dokumen(id)
    kajian_id = dokumen.kajian_id

    try:

        drive.delete_file(
            dokumen.drive_file_id,
        )

        db.session.delete(
            dokumen,
        )

        db.session.commit()

        flash(
            "Dokumen berhasil dihapus.",
            "success",
        )

    except Exception:

        db.session.rollback()

        flash(
            "Dokumen gagal dihapus.",
            "danger",
        )

    return redirect(
        url_for(
            "detail_kajian",
            id=kajian_id,
        )
    )

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    app.run()
