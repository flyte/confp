confp
=====

A configuration management tool, very similar to https://github.com/kelseyhightower/confd using
Python and the Jinja2 templating language.

Configuration files are created as Jinja2 templates, pulling values from one or more backends, and
can be run continuously as a daemon or as a single-execution application.

Installation
------------

```bash
pip install confp
```

Configuration
-------------

Configuration of confp is done in one YAML file. The file contains a `backends` section which
handles the retrieval of configuration values used in templates from the backend(s), and a
`templates` section which specifies how and where to deploy templates.

It's also possible to use this file for the Python logging configuration. Refer to the `logging`
section in `config.example.yml` for an example of this.

#### `backends` section

Each of the keys in the `backends` dictionary is your name for a backend. They must contain
a `type` key, plus whichever configuration keys the specific backend requires. For example, the
`redis` backend optionally takes `host` and `port` keys (among others).

Another example is the `env` backend which pulls values from environment variables. It optionally
takes a `prefix` key which all of the values will have at the beginning.

Here's an example using both:

```yaml
backends:
  my_redis:
    type: redis
    host: redis.example.com
    port: 6379
  my_env:
    type: env
    prefix: MY_SERVICE_  # Will be removed when specifying keys in templates
```

#### `templates` section

The `templates` list specifies one or more templates to render. Each of the dictionaries must
contain values for the `src` and `dest` keys. You may optionally specify the following:

- `owner` - The owner of the rendered template (only when running as root).
- `mode` - The file mode of the rendered template.
- `check_cmd` - The command to run in order to check that the rendered template is valid. Exit
code 0 means OK, >0 means it's invalid and we'll roll back to the existing version of the template.
- `restart_cmd` - The command to run which will either restart the daemon, or tell it to reload its
config.

You may also include a `vars` key, which contains a dictionary where keys are the names for global
values within templates and the value dict contains `backend` and `key` to specify where its value
comes from:

```yaml
templates:
  - src: /templates/nginx-mysite.conf.j2
    dest: /etc/nginx/sites-available/mysite.conf
    owner: nginx
    mode: '0664'
    check_cmd: /usr/sbin/nginx -t -c {{ dest }}
    restart_cmd: /usr/sbin/service nginx reload
    vars:
      FQDN:
        backend: my_redis  # The name we gave to our redis backend
        key: server/fqdn
      WWW_ROOT:
        backend: my_env
        key: WWW_ROOT  # Pulls the value from env var MY_SERVICE_WWW_ROOT (see prefix above)
```

Templates
---------

These are standard [Jinja2 templates](http://jinja.pocoo.org/docs/latest/templates/) which define
your config files and where to pull the variables from. You may pull values from one or more
backends within the template, or leave the source of the values up to the configuration (see the
template `vars` section above).

In order to pull values from a specific backend, use the syntax `{{ my_redis('server/fqdn') }}`
where `my_redis` is the name you gave your backend and the `server/fqdn` value is the key.

To use values which have been set globally with the above `vars` configuration, simply use the
name you assigned such as `{{ FQDN }}`.

Here's an example using both methods:

```
upstream backend {
    server {{ my_redis('backend/server/host') }}:{{ my_redis('backend/server/port') }};
}
server {
    listen 80;
    server_name {{ my_env('FQDN') }};
    return 301 https://$server_name$request_uri;
}
server {
    listen 443 ssl;
    server_name {{ my_redis('server/fqdn') }};

    ssl_certificate /etc/letsencrypt/live/{{ FQDN }}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{ FQDN }}/privkey.pem;

    root {{ WWW_ROOT }};

    location / {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

All Jinja2 features such as conditionals and loops are supported.
