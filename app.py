import os

from flask import Flask, redirect, render_template, url_for
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, login_required

from auth import auth_bp
from forms import KajianForm, csrf
from models import Kajian, User, db
from services import DriveFile, drive


# ==============================================================================
# APP CONFIGURATION
# ==============================================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "Ini rahasia"

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

def seed_admin():
    admin = User.query.filter_by(username="admin").first()

    if admin is None:
        admin = User(
            username="admin",
            role="admin"
        )

        admin.set_password("admin123")

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
    return Kajian.query.get_or_404(id)


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
):
    """Mengisi model Kajian dari form."""

    kajian.judul = form.judul.data
    kajian.tahun = form.tahun.data
    kajian.deskripsi = form.deskripsi.data
    kajian.hasil = form.hasil.data


@app.context_processor
def inject_app_name():
    return {
        "APP_NAME": "Portal Kajian Bapperida Kabupaten Rote Ndao"
    }


# ==============================================================================
# TEMPLATE FILTERS
# ==============================================================================

@app.template_filter("format_tanggal")
def format_tanggal(dt):

    if dt is None:
        return "-"

    bulan = [
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
    ]

    return (
        f"{dt.day} "
        f"{bulan[dt.month - 1]} "
        f"{dt.year}"
    )


# ==============================================================================
# PUBLIC
# ==============================================================================

@app.get("/")
def home():

    kajian_list = (
    Kajian.query
    .order_by(
        Kajian.tahun.desc(),
        Kajian.judul.asc()
    )
    .all()
    )

    return render_template(
        "index.html",
        kajian_list=kajian_list
    )


@app.get("/kajian/<int:id>")
def detail_kajian(id):

    kajian = get_kajian(id)

    return render_template(
        "detail.html",
        kajian=kajian
    )


# ==============================================================================
# TAMBAH KAJIAN
# ==============================================================================

@app.get("/kajian/tambah")
@login_required
def tambah_kajian():

    form = KajianForm()

    return render_kajian_form(
        form=form,
        is_edit=False
    )


@app.post("/kajian/tambah")
@login_required
def simpan_kajian():

    form = KajianForm()

    if not form.validate_on_submit():
        return render_kajian_form(
            form=form,
            is_edit=False
        )

    kajian = Kajian()

    save_kajian(
        kajian=kajian,
        form=form
    )

    db.session.add(kajian)
    db.session.commit()

    return redirect(
        url_for(
            "detail_kajian",
            id=kajian.id
        )
    )


# ==============================================================================
# EDIT KAJIAN
# ==============================================================================

@app.get("/kajian/<int:id>/edit")
@login_required
def edit_kajian(id):

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
def update_kajian(id):

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

'''
# ==============================================================================
# UPLOAD FILE KAJIAN
# ==============================================================================

@app.post("/kajian/<int:id>/upload")
@login_required
def upload_file_kajian(id):

    kajian = get_kajian(id)

    if not kajian:
        abort(404)

    file = request.files.get("file")

    if not file:
        abort(400)

    upload_file = UploadFile(
        filename=file.filename,
        stream=file.stream,
        mimetype=file.content_type
    )

    file_id = drive.upload_file(
        folder_id=kajian.folder_id,
        file=upload_file
    )

    uploaded = DriveFile.from_upload(
        form.file.data
    )

    drive_file_id = drive.upload_file(
        folder_id=kajian.drive_folder_id,
        file=uploaded,
    )

    return redirect(
        url_for(
            "detail_kajian",
            id=kajian.id
        )
    )
'''

# ==============================================================================
# HAPUS KAJIAN
# ==============================================================================

@app.post("/kajian/<int:id>/hapus")
@login_required
def hapus_kajian(id):

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
