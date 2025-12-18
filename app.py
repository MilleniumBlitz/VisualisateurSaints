from flask import Flask, render_template, request, redirect, url_for, jsonify
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

@app.template_filter("date_fr")
def date_fr(jour, mois):
    jour = int(jour)
    mois = int(mois)

    mois_fr = [
        "", "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"
    ]

    if jour == 1:
        return f"1er {mois_fr[mois]}"
    return f"{jour} {mois_fr[mois]}"

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

@app.route("/vue/mois/")
def saints_du_mois_vue():
    mois = request.args.get('mois', '01')
    saints = query("""
        SELECT id, nom, titre, jour, mois, date_naissance, description, source, image
        FROM saints
        WHERE mois=?
        ORDER BY CAST(jour AS INT), nom
    """, (mois,))
    return render_template("bloc_mois.html", saints=saints)

@app.route("/saints/")
def saints_du_mois():
    mois = request.args.get('mois')
    if not mois:
        return redirect(url_for("saints_du_mois", mois="01"))
    # saints = query("""
    #     SELECT id, nom, titre, jour, date_naissance, description, source, image
    #     FROM saints
    #     WHERE mois=?
    #     ORDER BY CAST(jour AS INT), nom
    # """, (mois,))
    return render_template("saints_mois.html", mois=mois)


@app.route('/edit/', methods=["GET", "POST"])
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id = None):
    if request.method == "POST":
        
        nom_saint = request.form["nom"]
        titre_saint = request.form["titre"]
        date_naissance_saint = request.form["date_naissance"]
        description_saint = request.form["description"]
        source_saint = request.form["source"]
        jour_saint = request.form["jour"]
        mois_saint = request.form["mois"]

        file = request.files["image"]
            
        filename = None
        if file and allowed_file(file.filename):

            filename = request.form["jour"] + "-" + request.form["mois"] + "-" + secure_filename(nom_saint)

            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

        # Si il s'agit d'un ajout
        if id is None:
            query("""INSERT INTO saints
                (nom, titre, date_naissance, description, "source", jour, mois, image)
                VALUES(?,?,?,?,?,?,?,?);""", (
                nom_saint,
                titre_saint,
                date_naissance_saint,
                description_saint,
                source_saint,
                jour_saint,
                mois_saint,
                filename,
            ))
            return redirect(url_for("saints_du_mois", mois=mois_saint))

        else:

            query("""
                UPDATE saints SET nom=?, titre=?, date_naissance=?, description=?, source=?, image=?
                WHERE id=?
            """, (
                nom_saint,
                titre_saint,
                date_naissance_saint,
                description_saint,
                source_saint,
                filename,
                id
            ))
            return redirect(url_for("mois"))

    saint = query("SELECT * FROM saints WHERE id=?", (id,), one=True)
    return render_template("edit.html", saint=saint)

@app.route("/delete/<int:id>", methods=["DELETE"])
def delete(id):
    query("""DELETE FROM saints WHERE id=?""", (id,))
    return "", 200

@app.route("/")
def accueil():
    return render_template("accueil.html")

if __name__ == "__main__":
    app.run(debug=True)
