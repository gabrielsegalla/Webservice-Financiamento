#
# Conteudo do arquivo `wsgi.py`
#
import sys

sys.path.insert(0, "/home/gabriel/projetos/Webservice-Financiamento")

from server.server import app as application