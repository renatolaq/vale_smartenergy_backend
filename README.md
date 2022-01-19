# SmartEnergy-backend

* Requerimento: Python 3.7

* vale solicitou usar pacote django-mssql para o banco. Ainda precisa ser confirmado se o pacote funciona no Linux e se o deploy será em linux.

* para instalar requerimentos: pip install -r requirements.txt

* para salvar novos pacores nos requirimentos: pip freeze -l > requirements.txt

* para gerarmos os PDFs é necessário instalar [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html) e colocar ele em nosso Path da seguinte maneira
```
C:\Program Files\wkhtmltopdf\bin
```


# Referencias de pacotes:

https://pypi.org/project/django-pyodbc-azure/

Para funcionar é necessário o ODBC 13 mínimo: ODBC Driver 13 for SQL Server

https://www.microsoft.com/en-us/download/confirmation.aspx?id=53339


https://www.django-rest-framework.org/


# Documentação API / Swagger:

http://<host>:<port>/api-docs/
  
 
# Admin:

* user/pass: dxcadmin/dxcadmin



# Referencias de testes unitários

feito utilizando o coverage (pip/python package)

* Dependencias:

É necessário ter dados pré selecionaveis, como no caso deste exemplo utilizar fixtures para cada aplicação. Em cada caso de teste, é necessário popular na sequencia os dados das tabelas de relacionamentos.

app_name/fixtures/fixture_name.json

Para gerar o fixture, criar a pasta na aplication fixtures e executar o comando reverso do jango, exemplificado abaixo:

```$ python manage.py dumpdata company --indent=4 > .\company\fixtures\initial_data.json```

O comando vai gerar um JSON de todas as classes declaradas no MODELS da aplicação. Note que pode ser gerado grande numero de inserts e uma massa muito grande pode elevar o tempo de load durante o teste. Neste caso, os dados de logs, por exemplo, são descartaveis.


Para um banco de dados Legancy, o processo de migration não cria um banco de dados temporário ou in memory. Neste ponto, utilizamos um banco de dados clone "vazio". O processo de fixture popula o banco e faz o rollback ao final dos testes.

* Entretanto é importante que o banco não seja removido. E para tal, a flag <b>--keepdb deve estar sempre presente no comando de teste ou o banco será removido!</b>.

O banco de dados de teste é selecionado no settings.py ou em arquivo de local_settings.py, à escolha da arquitetura.

```
DATABASES = {
    'default': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'hostname',
        'PORT': '1433',

        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
        # only for test
        'TEST': {
            'NAME': 'test_smartenergy',
        },
    },
}
```


```$ coverage run manage.py test -v 2 --keepdb```

Então com o converage pode-se preparar o relatorio em HTML que pode ser acessado pelo index.html na pasta ./htmlcov .Esta pasta e .coverage estão inibidos no .gitignore

Para gerar o report HTML:

```$ coverage html```

