# Camille

Create dedicated postgres role (RLS is unhappy if the role is superuser):

```shell
echo 'CREATE ROLE camille LOGIN PASSWORD \'camille\'; ALTER DATABASE camille OWNER TO camille;' | psql -h localhost -U admin -d camille
```