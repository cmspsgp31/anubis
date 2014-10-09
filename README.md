# Anubis

## Extensão para Django especializada em pesquisa em banco de dados.

**Anubis** é uma extensão para Django que visa facilitar o trabalho com bancos
de dados voltados primariamente para pesquisa - ou seja, bancos em que a
pesquisa de registros é mais frequente e importante do que a inserção de novos
registros e/ou alterações.

### Recursos

* Criação e acesso a Functions do PostgreSQL direto no projeto Django;
* Fácil definição de filtros e pesquisas baseadas em Functions, Texto Completo e
QuerySets simples;
* Biblioteca front-end em CoffeeScript para facilitar manutenção de URLs de
pesquisas feitas em AJAX.

### Requerimentos

* PostgreSQL 9.3+, com as seguintes extensões instaladas:
	- btree\_gist
	- unaccent
* GHC 7.8+
* Node.js com os seguintes pacotes instalados:
	- coffeescript
	- require.js
* (Para o browser) As seguintes bibliotecas JavaScript (devem ser baixadas
separadamente e colocadas na pasta ```anubis/app/frontend/build/lib```)
	- Backbone.js
	- require.js
	- jQuery
	- jQueryUI
	- Underscore.js
	- swig
