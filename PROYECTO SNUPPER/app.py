from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret123'

db = SQLAlchemy(app)

# ======================
# MODELO
# ======================
class Perfume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    mililitros = db.Column(db.Integer, nullable=False)
    capacidad = db.Column(db.Integer, default=250)

from datetime import datetime

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    perfume_id = db.Column(db.Integer, db.ForeignKey('perfume.id'))
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    perfume = db.relationship('Perfume')



# ======================
# RUTAS
# ======================
@app.route('/')
def index():
    perfumes = Perfume.query.all()

    total = len(perfumes)
    ok = 0
    bajo = 0
    critico = 0

    for p in perfumes:
        capacidad = p.capacidad if p.capacidad else 1000
        porcentaje = (p.mililitros / capacidad) * 100

        if porcentaje <= 10:
            critico += 1
        elif porcentaje <= 50:
            bajo += 1
        else:
            ok += 1

    return render_template(
        'index.html',
        perfumes=perfumes,
        total=total,
        ok=ok,
        bajo=bajo,
        critico=critico
    )


@app.route('/agregar', methods=['GET', 'POST'])
def agregar_perfume():
    if request.method == 'POST':
        nombre = request.form['nombre']
        ml = int(request.form['mililitros'])

        perfume = Perfume(nombre=nombre, mililitros=ml)
        db.session.add(perfume)
        db.session.commit()

        flash('Perfume agregado correctamente')
        return redirect(url_for('index'))

    return render_template('agregar_perfume.html')

from datetime import datetime

@app.route('/vender', methods=['GET', 'POST'])
def vender():
    perfumes = Perfume.query.all()

    if request.method == 'POST':
        perfume_id = int(request.form['perfume'])
        cantidad = int(request.form['cantidad'])

        perfume = Perfume.query.get(perfume_id)

        if perfume.mililitros >= cantidad:
            perfume.mililitros -= cantidad

            # GUARDAR VENTA
            venta = Venta(
                perfume_id=perfume.id,
                cantidad=cantidad,
                fecha=datetime.utcnow()
            )
            db.session.add(venta)

            db.session.commit()
            flash('Venta registrada correctamente')
        else:
            flash('No hay suficiente inventario')

        return redirect(url_for('index'))

    return render_template('vender.html', perfumes=perfumes)



from datetime import date

@app.route('/reporte', methods=['GET'])
def reporte():
    inicio = request.args.get('inicio')
    fin = request.args.get('fin')

    query = Venta.query

    if inicio and fin:
        query = query.filter(
            Venta.fecha.between(inicio, fin)
        )

    ventas = query.order_by(Venta.fecha.desc()).all()

    total_ml = sum(v.cantidad for v in ventas)

    return render_template(
        'reporte.html',
        ventas=ventas,
        total_ml=total_ml
    )


@app.route('/rellenar/<int:id>', methods=['GET', 'POST'])
def rellenar(id):
    perfume = Perfume.query.get_or_404(id)

    if request.method == 'POST':
        ml_rellenar = int(request.form['mililitros'])

        perfume.mililitros += ml_rellenar

        # Evitar pasar la capacidad máxima
        if perfume.mililitros > perfume.capacidad:
            perfume.mililitros = perfume.capacidad

        db.session.commit()
        flash('Perfume rellenado correctamente')
        return redirect(url_for('index'))

    return render_template('rellenar.html', perfume=perfume)



if __name__ == '__main__':
    with app.app_context():
     db.create_all()

  
