
# WebService para Financiamento

Demo do Projeto : https://webservice-financiamento.herokuapp.com/apidocs/

## Descrição do Projeto

1. Construa uma aplicação WebService REST que receba o valor do imóvel, a taxa de juro, o percentual de entrada, a quantidade de parcelas, e retorne uma lista de parcelas, contendo sua data de vencimento e o valor da parcela na data de vencimento utilizando a metodologia SAC.  

2. Construa uma interface web que consulte essa API REST.

3. Construa uma aplicação WebService REST que receba o valor do imóvel, o salário do indivíduo, o prazo de financiamento com no máximo 45 anos, e consulte o WebService construído na etapa 1 informando uma entrada de 20% e uma taxa de 10% ao ano, e retorne as parcelas informando se a renda do individuo é suficiente para pagar a parcela, considerando que a parcela deve ter um valor máximo de 30% dos rendimentos do indivíduo.  

4. Construa uma interface web que consulte essa API REST.  

5. Com o webservice do exercício 3, modifique a aplicação para que o percentual de entrada, a taxa anual, e o valor máximo da parcela em relação ao salário do indivíduo seja consultado em banco de dados relacional.

6. Receba na API REST do exercício anterior o CPF, Nome Completo, data de nascimento, se tem FGTS e quanto tem no FGTS e armazene esses dados em base de dados, bem como os dados da simulação.  

7. Modifique a interface web do exercício 4 para receber esses parâmetros.  

8. Crie um webservice que retorne os dados de simulações, recebendo o "offset" (índice do primeiro resultado) e o "limit" (quantidade de registros que tem que trazer. Ordenado por data de inserção.  

9. Crie uma tela que acesse o webservice do exercício 8.  

10. No webservice do exercício 6 e na tela do exercício 7, adicione um campo para o e-mail (opcional) e se o usuário informar o e-mail, enviar um e-mail com a simulação para o endereço informado.

11. Apresentar o que estiver funcionando no dia 27/11/2018 - Não será possível entrega atrasada.

  
## Como usar
Clone o projeto:
> $ git clone

Crie uma virtualenv e ative (Exemplo com o virtualenvwrapper)
> $ mkvirtualenv env
> $ workon env

Instale as bibliotecas necessárias :
> $ (env) pip install -r requirements.txt

Execute o projeto :
> $ (env) python run.py 

A documentação do Sistema ficará disponivel na url [http://localhost:5000/apidocs/](http://localhost:5000/apidocs/)
