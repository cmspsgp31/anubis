[![Code Climate](https://codeclimate.com/github/cmspsgp31/anubis/badges/gpa.svg)](https://codeclimate.com/github/cmspsgp31/anubis)

# Anubis

## Extensão para Django especializada em pesquisa em banco de dados.

**Anubis** é uma extensão para Django que visa facilitar o trabalho com bancos
de dados voltados primariamente para pesquisa - ou seja, bancos em que a
pesquisa de registros é mais frequente e importante do que a inserção e/ou
alteração de registros.

### Recursos

* Front-end de pesquisa em [React.js](https://facebook.github.io/react/)
automatizado e de fácil implementação. Você escreve seu modelo, inclui os
*mixins* do front-end e tem uma interface de pesquisa instantânea, com suporte
a pesquis*mixins*as com lógica booleana.
* Definição de
[Functions](https://www.postgresql.org/docs/current/static/sql-createfunction.html)
do [PostgreSQL](https://www.postgresql.org/) diretamente nas migrações do
projeto Django, permitindo gerenciá-las diretamente do código do projeto em
Python.
* Definição simplificada de unidades de pesquisa baseadas em QuerySets,
pesquisas por texto completo e Functions, sem necessidade de programá-las
diretamente (mas com flexibilidade o suficiente quando necessário).
* Facilidades de integração com
[ElasticSearch](https://www.elastic.co/products/elasticsearch) para quando
pesquisas baseadas em texto completo do
[PostgreSQL](https://www.postgresql.org/docs/current/static/textsearch.html) não
forem suficientes.

### Requerimentos

* [PostgreSQL](https://www.postgresql.org/download/) 9.3+, com a extensão
[unaccent](https://www.postgresql.org/docs/current/static/unaccent.html)
instalada.
* [Stack](https://docs.haskellstack.org/en/stable/install_and_upgrade/) 1.2+
(para biblioteca de interpretação de pesquisas booleanas).
* [Node.js](https://nodejs.org/en/download/) com [npm]() para geração da
interface de pesquisa. Se, durante a instalação, um executável do
[yarn](https://code.facebook.com/posts/1840075619545360) for encontrado, ele
será utilizado (a velocidade de instalação de pacotes com o yarn é muito
superior à do npm atualmente).
* [Python](https://www.python.org/downloads/) 3.4+ para a aplicação Web.
* Um servidor WSGI (como
[uWSGI](http://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html) ou
[Gunicorn](http://gunicorn.org/)) e, para o caso de uma aplicação pública, é
altamente recomendável rodá-lo atrás de um servidor robusto como
[nginx](http://nginx.org/en/download.html) ou
[Apache](https://httpd.apache.org/download.cgi). Note que, no atual estágio de
desenvolvimento, **não é recomndável utilizar o Anubis em aplicações públicas
na Internet**.
* Uma distribuição do [Linux](https://distrowatch.com/dwres.php?resource=major).
Utilizar o Anubis em um servidor Windows pode ser possível (especialmente com o
advento do [Bash para
Windows](https://msdn.microsoft.com/en-us/commandline/wsl/install_guide)), mas
**a utilização em servidores Windows não é suportada nem testada pelos
desenvolvedores do Anubis**.
