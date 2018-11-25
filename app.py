# from server.server import app, db, host, port, debug, ma
from flask_migrate import Migrate, MigrateCommand
from flask import request, jsonify, render_template
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

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://dbjyuqkkswmlua:d2bdf2092bf8f2005e8959e67bd9deb1292c25613a4ce748918d5a201212c438@ec2-54-163-230-178.compute-1.amazonaws.com:5432/d9cbksrafidfrv'                                                                                       
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
        msg['From'] = "No-Reply Financiamento <webservice.financiamento.segalla@gmail.com>"
        msg['Subject'] = "Sua cotação de parcelamento"
        body = "Segue sua cotação de parcelamento \n \n {}".format(content)
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login("webservice.financiamento.segalla", "Lu17031975")
        text = msg.as_string()
        server.sendmail("webservice.financiamento.segalla@gmail.com", to, text)    

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

    fgts = ma.Nested(FGTSSchema, many=True)

    
@app.route("/calcular/prestacoes", methods=['POST'])
def Prestacoes():
    """Recebe o valor do imóvel, a taxa de juro, o percentual de entrada, a quantidade de parcelas, 
    e retorne uma lista de parcelas, contendo sua data de vencimento e o 
    valor da parcela na data de vencimento utilizando a metodologia SAC..
    ---
    tags:
        - Calculo
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
    """Recebe o valor do imóvel, o salário do indivíduo, o prazo de financiamento com no máximo 45 anos, e consulte o WebService construído na etapa 1 informando uma entrada de 20% e uma taxa de 10% ao ano, e retorne as parcelas informando se a renda do individuo é suficiente para pagar a parcela, considerando que a parcela deve ter um valor máximo de 30% dos rendimentos do indivíduo.
    ---
    tags:
        - Calculo
    parameters:
      - name: valor_imovel
        in: path
        type: integer
        required: true
      - name: prazo_financiamento_anos
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Retorna as parcelas informando se a renda do individuo é suficiente para pagar a parcela.
        examples:
          data: [
            {
                "parcelas": [
                    {
                        "id": 0,
                        "saldo_total": 25000
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 1,
                        "juros": 2500,
                        "prestacao": 4583.333333333334,
                        "saldo_devedor": 22916.666666666668
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 2,
                        "juros": 2291.666666666667,
                        "prestacao": 4375,
                        "saldo_devedor": 20833.333333333336
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 3,
                        "juros": 2083.3333333333335,
                        "prestacao": 4166.666666666667,
                        "saldo_devedor": 18750.000000000004
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 4,
                        "juros": 1875.0000000000005,
                        "prestacao": 3958.333333333334,
                        "saldo_devedor": 16666.66666666667
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 5,
                        "juros": 1666.6666666666672,
                        "prestacao": 3750.000000000001,
                        "saldo_devedor": 14583.333333333338
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 6,
                        "juros": 1458.333333333334,
                        "prestacao": 3541.6666666666674,
                        "saldo_devedor": 12500.000000000004
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 7,
                        "juros": 1250.0000000000005,
                        "prestacao": 3333.333333333334,
                        "saldo_devedor": 10416.66666666667
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 8,
                        "juros": 1041.666666666667,
                        "prestacao": 3125.0000000000005,
                        "saldo_devedor": 8333.333333333336
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 9,
                        "juros": 833.3333333333336,
                        "prestacao": 2916.666666666667,
                        "saldo_devedor": 6250.000000000002
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 10,
                        "juros": 625.0000000000002,
                        "prestacao": 2708.333333333334,
                        "saldo_devedor": 4166.666666666668
                    },
                    {
                        "amortizacao": 2083.3333333333335,
                        "id": 11,
                        "juros": 416.6666666666668,
                        "prestacao": 2500.0000000000005,
                        "saldo_devedor": 2083.3333333333344
                    }
                ],
                "tem_situacao": false,
                "valor_maximo_p_parcela": 720
            }
          ]

    """
    response = FinanciamentoController().verifica_condicoes_para_parcelar(
        user_id,
        request.values.get('valor_imovel'),
        request.values.get('prazo_financiamento_anos')
    )
    return jsonify(data = response)

@app.route("/novo/usuario", methods=['POST'])
def NovoUsuario():
    """CPF, Nome Completo, data de nascimento, se tem FGTS e quanto tem no FGTS e armazene esses dados em base de dados, bem como os dados da simulação.
    ---
    tags:
        - Usuários
    parameters:
      - name: salario_usuario
        in: path
        type: integer
        required: true
      - name: taxa_anual
        in: path
        type: integer
        required: true
      - name: percentual_entrada
        in: path
        type: integer
        required: true
      - name: nome_completo
        in: path
        type: string
        required: true
      - name: taxa_anual
        in: cpf
        type: integer
        required: true
      - name: data_nascimento
        in: path
        type: string
        required: true
      - name: valor_fgts
        in: path
        type: integer
        required: true
      - name: tem_fgts
        in: path
        type: boolean
        required: true
      - name: email
        in: path
        type: string
        required: true
    responses:
      200:
        description: Retorna o usuário inserido.
        examples:
          data: [
            {
                "cpf": "00000000000",
                "data_criacao": "2018-11-20T14:30:18.830557+00:00",
                "data_nascimento": "1997-02-01T00:00:00+00:00",
                "email": "grsegalla@hotmail.com",
                "fgts": 1,
                "id": 1,
                "nome_completo": "Gabriel Rodrigues Segalla",
                "percentual_entrada": 50,
                "salario_usuario": 2400,
                "taxa_anual": 10,
                "valor_maximo_parcelas": 720
            }
          ]

    """
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
    """Endpoint para retornar os usuarios
    ---
    tags:
        - Usuários
    parameters:
      - name: offset
        in: path
        type: integer
        required: true
      - name: limit
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Retorna a lista de usuários.
        examples:
          data: [
            {
                "cpf": "00000000000",
                "data_criacao": "2018-11-20T14:30:18.830557+00:00",
                "data_nascimento": "1997-02-01T00:00:00+00:00",
                "email": "grsegalla@hotmail.com",
                "fgts": 1,
                "id": 1,
                "nome_completo": "Gabriel Rodrigues Segalla",
                "percentual_entrada": 50,
                "salario_usuario": 2400,
                "taxa_anual": 10,
                "valor_maximo_parcelas": 720
            }
          ]

    """
    response = UsuarioController().usuarios(
        request.values.get('offset'),
        request.values.get('limit')
    )
    return UsuarioSchema(many=True).jsonify(response)

@app.route("/")
def Index():
    return render_template('index.html')

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
