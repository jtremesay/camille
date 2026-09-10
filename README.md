# Camille

## DB

Django-RLS-tenats refuse to use a superuser for database connections, so we use a dedicated Postgres user.

```shell
echo 'CREATE ROLE camille LOGIN PASSWORD \'camille\'; ALTER DATABASE camille OWNER TO camille;' | psql -h localhost -U admin -d camille
```