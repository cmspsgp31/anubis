[![Code Climate](https://codeclimate.com/github/cmspsgp31/anubis/badges/gpa.svg)](https://codeclimate.com/github/cmspsgp31/anubis)

# Anubis

## User-friendly database querying tool for Django-based apps

**Anubis** is a [Django](https://www.djangoproject.com) extension created with
the purpose of easing the work of binding databases to user-friendly interfaces,
without giving up the ability to access advanced features from said databases.
It's intended primarily for high-read, low-write databases - i.e., databases in
which accessing information is more important and frequent than updating it.

### Features

* [React.js](https://facebook.github.io/react/)-based built-in search front-end
  that comes with boolean logic compositing for free. You just write your Django
  models, then when you write your views, you inherit from the provided
  front-end *mixins*, and **Anubis** will generate a fully-featured search
  interface automatically.

* [PostgreSQL](https://www.postgresql.org/)'s
  [Functions](https://www.postgresql.org/docs/current/static/sql-createfunction.html)
  built-in support, allowing you to define and modify functions directly in your
  Django project, streamlined with Django's migration framework workflow.

* Allows you to easily define basic search units for your database, based either
  in Django's QuerySets, PostgreSQL's [full-text
  search](https://www.postgresql.org/docs/current/static/textsearch-intro.html)
  functionality or Functions. There is no need to write code for getting this
  feature, although it's flexible enough for it to possible when needed.

* Simple integration with
  [Elasticsearch](https://www.elastic.co/products/elasticsearch)-based full text
  search for when PostgreSQL's is not enough.

### Requirements

* [PostgreSQL](https://www.postgresql.org/download/) 9.3+, with the
  [unaccent](https://www.postgresql.org/docs/current/static/unaccent.html)
  extension installed.

* [Stack](https://docs.haskellstack.org/en/stable/install_and_upgrade/) 1.2+
  (for the boolean-logic library).

* [Node.js](https://nodejs.org/en/download/) with [npm](https://www.npmjs.com/)
  installed for building the search interface. If a
  [yarn](https://code.facebook.com/posts/1840075619545360) executable is found
  during installation, it will be used instead (yarn's speed is currently vastly
  superior to npm's.)

* [Python](https://www.python.org/downloads/) 3.4+ for the web application.

* A WSGI server (such as
  [uWSGI](http://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html) or
  [Gunicorn](http://gunicorn.org/)), and, if you have a public-facing app, it's
  highly recommended running it behind a more robust server such as
  [nginx](http://nginx.org/en/download.html) or
  [Apache](https://httpd.apache.org/download.cgi). Please note that currently
  **it is not advisable to run Anubis in Internet-facing environments**.

* A [Linux](https://distrowatch.com/dwres.php?resource=major) distribution. It
  may be possible to run Anubis under a Windows server (specially since the
  release of [Bash for
  Windows](https://msdn.microsoft.com/en-us/commandline/wsl/install_guide)), but
  **using Anubis in Windows-based environments is not currently supported or
  tested by the Anubis development team**.
