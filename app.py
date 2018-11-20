# from server.server import app, db, host, port, debug, ma
from flask_migrate import Migrate, MigrateCommand
from flask import request, jsonify
from flask_script import Manager
from datetime import datetime
from sqlalchemy import desc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
#from flasgger import Swagger
from flask import Flask, jsonify
from flasgger import Swagger
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost/webservice-financiamento'
CORS(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)

host = "localhost"
debug = True
port = 8081

SQLALCHEMY_ECHO = False


manager = Manager(app)
manager.add_command('db', MigrateCommand)
migrate = Migrate(app, db)
swagger = Swagger(app)

class UsuarioController():
    def novo_usuario(
        self, salario_usuario,taxa_anual,percentual_entrada,nome_completo,cpf,
        data_nascimento,valor_fgts, tem_fgts,email
    ):
        usuario = Usuario(
            salario_usuario=salario_usuario,
            taxa_anual=taxa_anual,
            percentual_entrada=percentual_entrada,
            valor_maximo_parcelas=float(salario_usuario) / 100 * 30 ,
            nome_completo=nome_completo,
            cpf=cpf,
            data_nascimento=data_nascimento,
            email=email
        )
        if tem_fgts:
            novo_fgts = FGTS(valor_total=valor_fgts)
            db.session.add(novo_fgts)
            db.session.commit()
            usuario.fgts_id = novo_fgts.id
        db.session.add(usuario)
        db.session.commit()
        return usuario

    def usuario_por_id(self,user_id):
        return Usuario.query.filter_by(id=user_id).first()

    def usuarios(self, offset, limit):
        return Usuario.query.order_by(desc(Usuario.data_criacao)).offset(offset).limit(limit).all()

class EmailController():

    def send_mail(self, content,to):
        msg = MIMEMultipart()
        msg['From'] = "No-Reply Financiamento <no-reply@financiamento.com>"
        msg['Subject'] = "Sua cotação de parcelamento"
        body = "Segue sua cotação de parcelamento \n \n {}".format(content)
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login("consulta.publica.agrosatelite", "02HxINUu")
        text = msg.as_string()
        server.sendmail("grodriguessegalla@gmail.com", to, text)    

class FinanciamentoController():

    def gerar_parcelas(self, valor_imovel, taxa_juro, percentual_entrada, qt_parcelas):
        valor_imovel = float(valor_imovel) - (float(percentual_entrada) * 100)
        amortizacao = float(valor_imovel) / float(qt_parcelas)
        response = []
        primeira_parcela = {}
        primeira_parcela['id'] = 0
        primeira_parcela['saldo_total'] = valor_imovel
        response.append(primeira_parcela)
        for i in range(1,int(qt_parcelas)):
            obj_parcela = {}    
            valor_imovel = valor_imovel #- (percentual_entrada * 100)
            juros = valor_imovel * (float(taxa_juro) / 100)
            valor_imovel = valor_imovel - amortizacao
            parcela = amortizacao + juros
            obj_parcela['id'] = i
            obj_parcela['saldo_devedor'] = valor_imovel
            obj_parcela['juros'] = juros
            obj_parcela['amortizacao'] = amortizacao
            obj_parcela['prestacao'] = parcela
            response.append(obj_parcela)
        return response

    def verifica_condicoes_para_parcelar(self, user_id, valor_imovel, prazo_financiamento):
        if int(prazo_financiamento) <= 45:
            usuario = UsuarioController().usuario_por_id(user_id)
            response = []
            response_obj = {}
            parcelas = self.gerar_parcelas(
                float(valor_imovel), usuario.taxa_anual, usuario.percentual_entrada,
                int(prazo_financiamento)*12
            )
            primeira_parcela = parcelas[1]
            valor_maximo_usuario = usuario.valor_maximo_parcelas
            if primeira_parcela.get('prestacao') <= valor_maximo_usuario:
                response_obj['tem_situacao'] = True 
            else:
                response_obj['tem_situacao'] = False
            response_obj['valor_maximo_p_parcela'] = valor_maximo_usuario
            response_obj['parcelas'] = parcelas
            response.append(response_obj)
            if usuario.email:
                EmailController().send_mail(response, usuario.email)
            return response
        else:
            raise Exception('Valor limite para o prazo de financiamento é de 45 Anos')

class FGTS(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    valor_total = db.Column(db.Float)

    def __init__(self, valor_total):
        self.valor_total = valor_total

    def __repr__(self):
        return '<FGTS %r>' % self.id

class FGTSSchema(ma.ModelSchema):
    """Class Schema responsable for FGTS model"""
    class Meta:
        model = FGTS

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    salario_usuario = db.Column(db.Float)
    taxa_anual = db.Column(db.Float)
    percentual_entrada = db.Column(db.Float)
    valor_maximo_parcelas = db.Column(db.Float)
    nome_completo = db.Column(db.String(120))
    cpf = db.Column(db.String(11))
    data_nascimento = db.Column(db.DateTime, nullable=False)
    fgts_id = db.Column(db.Integer, db.ForeignKey('FGTS.id'))
    fgts = db.relationship('FGTS', backref=db.backref('fgts', lazy=True))
    data_criacao = db.Column(db.DateTime, nullable=False,default=datetime.utcnow)
    email = db.Column(db.String(120))

    def __init__(
        self, salario_usuario,taxa_anual,percentual_entrada,
        valor_maximo_parcelas,nome_completo,cpf,data_nascimento,email
    ):
        self.salario_usuario = salario_usuario
        self.taxa_anual = taxa_anual
        self.percentual_entrada = percentual_entrada
        self.valor_maximo_parcelas = valor_maximo_parcelas
        self.nome_completo = nome_completo
        self.cpf = cpf
        self.data_nascimento = data_nascimento
        self.email=email

    def __repr__(self):
        return '<Usuario %r>' % self.nome_completo

class UsuarioSchema(ma.ModelSchema):
    """Class Schema responsable for Usuario model"""
    class Meta:
        model = Usuario

    
@app.route("/calcular/prestacoes", methods=['POST'])
def Prestacoes():
    """Recebe o valor do imóvel, a taxa de juro, o percentual de entrada, a quantidade de parcelas, 
    e retorne uma lista de parcelas, contendo sua data de vencimento e o 
    valor da parcela na data de vencimento utilizando a metodologia SAC..
    ---
    parameters:
      - name: valor_imovel
        in: path
        type: integer
        required: true
      - name: taxa_juros
        in: path
        type: integer
        required: true
      - name: percentual_entrada
        in: path
        type: integer
        required: true
      - name: qt_parcelas
        in: path
        type: integer
        required: true    
    responses:
      200:
        description: Uma lista de parcelas, contendo sua data de vencimento e o  valor da parcela na data de vencimento utilizando a metodologia SAC
        examples:
          data: [
            {
                "id": 0,
                "saldo_total": 27000
            },
            {
                "amortizacao": 9000,
                "id": 1,
                "juros": 2700,
                "prestacao": 11700,
                "saldo_devedor": 18000
            },
            {
                "amortizacao": 9000,
                "id": 2,
                "juros": 1800,
                "prestacao": 10800,
                "saldo_devedor": 9000
            }
          ]

    """
    response = FinanciamentoController().gerar_parcelas(
        request.values.get('valor_imovel'),
        request.values.get('taxa_juros'),
        request.values.get('percentual_entrada'), 
        request.values.get('qt_parcelas')
    )
    return jsonify(data = response)

@app.route("/calcular/possibilidade/compra/usuario/<int:user_id>", methods=['POST'])
def PossibilidadeCompra(user_id):
    response = FinanciamentoController().verifica_condicoes_para_parcelar(
        user_id,
        request.values.get('valor_imovel'),
        request.values.get('prazo_financiamento_anos')
    )
    return jsonify(data = response)

@app.route("/novo/usuario", methods=['POST'])
def NovoUsuario():
    response = UsuarioController().novo_usuario(
        request.values.get('salario_usuario'),
        request.values.get('taxa_anual'),
        request.values.get('percentual_entrada'),
        request.values.get('nome_completo'),
        request.values.get('cpf'),
        request.values.get('data_nascimento'),
        request.values.get('valor_fgts'),
        request.values.get('tem_fgts'),
        request.values.get('email')
    )
    return UsuarioSchema(many=False).jsonify(response)

@app.route("/usuarios", methods=['GET'])
def Usuarios():
    response = UsuarioController().usuarios(
        request.values.get('offset'),
        request.values.get('limit')
    )
    return UsuarioSchema(many=True).jsonify(response)

@app.route("/")
def Index():
    return "API FUNCIONANDO"

@manager.command
def runserver():
    """Method for run project."""
    app.run(
        host=(host),
        port=int(port),
        debug=bool(debug)
    )

if __name__ == "__main__":
    manager.run()


# app.run(
#         host=(host),
#         port=int(port),
#         debug=bool(debug)
#     )