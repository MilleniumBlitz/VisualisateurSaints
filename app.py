from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

DB = "saints.db"

# Dossier où les images seront stockées
UPLOAD_FOLDER = "static"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Extensions autorisées
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def query(sql, params=(), one=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    result = cur.fetchall()
    conn.commit()
    conn.close()
    return (result[0] if result else None) if one else result

@app.route("/")
def mois():

    mois = request.args.get("mois", "01")

    saints = query("SELECT id, nom, titre, jour, mois, description, source, image FROM saints WHERE mois=? ORDER BY jour", (mois,))

    jours = {}
    for saint in saints:
        jours.setdefault(saint['jour'], []).append(saint)

    return render_template("mois.html", mois=mois, saints=saints)

@app.route("/<mois>/<jour>")
def saints(mois, jour):
    saints = query("SELECT * FROM saints WHERE mois=? AND jour=? ORDER BY nom", (mois, jour))
    return render_template("saints.html", saints=saints, mois=mois, jour=jour)

@app.route("/<mois>/saints")
def saints_du_mois(mois):
    saints = query("""
        SELECT id, nom, titre, jour, date_naissance, description, source, image
        FROM saints
        WHERE mois=?
        ORDER BY CAST(jour AS INT), nom
    """, (mois,))
    return render_template("saints_mois.html", saints=saints, mois=mois)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if request.method == "POST":

        file = request.files["image"]

        if file and allowed_file(file.filename):
            filename = request.form["jour"] + "-" + request.form["mois"] + "-" + secure_filename(file.filename)

            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

        query("""
            UPDATE saints SET nom=?, titre=?, date_naissance=?, description=?, source=?, image=?
            WHERE id=?
        """, (
            request.form["nom"],
            request.form["titre"],
            request.form["date_naissance"],
            request.form["description"],
            request.form["source"],
            filename,
            id
        ))
        return redirect(url_for("mois"))

    saint = query("SELECT * FROM saints WHERE id=?", (id,), one=True)
    return render_template("edit.html", saint=saint)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        query("""
            INSERT INTO saints (nom, titre, mois, jour, date_naissance, description, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["nom"],
            request.form["titre"],
            request.form["mois"],
            request.form["jour"],
            request.form["date_naissance"],
            request.form["description"],
            request.form["source"]
        ))
        return redirect(url_for("mois"))
    return render_template("add.html")

if __name__ == "__main__":
    app.run(debug=True)
