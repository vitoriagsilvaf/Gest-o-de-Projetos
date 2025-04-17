from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'kanban_seguro'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projetos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Projeto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    status = db.Column(db.String(20), default='pendente')
    inicio_andamento = db.Column(db.DateTime, nullable=True)
    fim_conclusao = db.Column(db.DateTime, nullable=True)
    arquivado = db.Column(db.Boolean, default=False)

class Historico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projeto.id'))
    status = db.Column(db.String(20))
    data = db.Column(db.DateTime, default=datetime.now)

@app.route('/')
def home():
    pendentes = Projeto.query.filter_by(status='pendente', arquivado=False).all()
    andamento = Projeto.query.filter_by(status='andamento', arquivado=False).all()
    concluidos = Projeto.query.filter_by(status='concluido', arquivado=False).all()
    return render_template('kanban.html', pendentes=pendentes, andamento=andamento, concluidos=concluidos)

@app.route('/criar_projeto', methods=['POST'])
def criar_projeto():
    nome = request.form['nome']
    descricao = request.form['descricao']
    novo = Projeto(nome=nome, descricao=descricao, status='pendente')
    db.session.add(novo)
    db.session.commit()
    historico = Historico(projeto_id=novo.id, status='pendente')
    db.session.add(historico)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/mover_projeto/<int:projeto_id>/<string:novo_status>')
def mover_projeto(projeto_id, novo_status):
    projeto = Projeto.query.get_or_404(projeto_id)
    if novo_status == 'andamento':
        projeto.inicio_andamento = datetime.now()
    elif novo_status == 'concluido':
        projeto.fim_conclusao = datetime.now()
    projeto.status = novo_status
    db.session.add(Historico(projeto_id=projeto.id, status=novo_status))
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/projeto/<int:projeto_id>')
def ver_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    historico = Historico.query.filter_by(projeto_id=projeto.id).order_by(Historico.data).all()
    return render_template('ver_projeto.html', projeto=projeto, historico=historico)

@app.route('/projeto/<int:projeto_id>/editar', methods=['GET', 'POST'])
def editar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    if request.method == 'POST':
        projeto.nome = request.form['nome']
        projeto.descricao = request.form['descricao']
        db.session.commit()
        return redirect(url_for('ver_projeto', projeto_id=projeto.id))
    return render_template('editar_projeto.html', projeto=projeto)

@app.route('/projeto/<int:projeto_id>/excluir')
def excluir_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    Historico.query.filter_by(projeto_id=projeto.id).delete()
    db.session.delete(projeto)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/projeto/<int:projeto_id>/arquivar')
def arquivar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    projeto.arquivado = True
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/projeto/<int:projeto_id>/desarquivar')
def desarquivar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    projeto.arquivado = False
    db.session.commit()
    return redirect(url_for('arquivados'))

@app.route('/arquivados')
def arquivados():
    termo = request.args.get("busca", "")
    if termo:
        projetos = Projeto.query.filter(Projeto.arquivado==True, Projeto.nome.ilike(f"%{termo}%")).all()
    else:
        projetos = Projeto.query.filter_by(arquivado=True).all()
    return render_template("arquivados.html", projetos=projetos)

if __name__ == '__main__':
    if not os.path.exists('projetos.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True, port=3000)
