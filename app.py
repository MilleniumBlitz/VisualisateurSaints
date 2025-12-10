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

@app.route("/vue/mois/<mois>")
def saints_du_mois_vue(mois):
    saints = query("""
        SELECT id, nom, titre, jour, date_naissance, description, source, image
        FROM saints
        WHERE mois=?
        ORDER BY CAST(jour AS INT), nom
    """, (mois,))
    return render_template("bloc_mois.html", saints=saints)

@app.route("/")
@app.route("/<mois>")
def saints_du_mois(mois = "01"):
    saints = query("""
        SELECT id, nom, titre, jour, date_naissance, description, source, image
        FROM saints
        WHERE mois=?
        ORDER BY CAST(jour AS INT), nom
    """, (mois,))
    return render_template("saints_mois.html", saints=saints)


@app.route('/edit/', methods=["GET", "POST"])
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id = None):
    if request.method == "POST":
        
        file = request.files["image"]

        if file and allowed_file(file.filename):
            filename = request.form["jour"] + "-" + request.form["mois"] + "-" + secure_filename(file.filename)

            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

        # Si il s'agit d'un ajout
        if id is None:
            query("""INSERT INTO saints
                (nom, titre, date_naissance, description, "source", jour, mois, image)
                VALUES(?,?,?,?,?,?,?,?);""", (
                request.form["nom"],
                request.form["titre"],
                request.form["date_naissance"],
                request.form["description"],
                request.form["source"],
                request.form["jour"],
                request.form["mois"],
                filename,
            ))
            request.args.add("mois", request.form["mois"])
            return redirect(url_for("mois"))

        else:

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

if __name__ == "__main__":
    app.run(debug=True)
