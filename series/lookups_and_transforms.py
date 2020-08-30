from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.db.models.functions import Length


@HStoreField.register_lookup
class CheckEpisodes(models.Transform):
    """
        Based on function in migration 0057:

        create or replace function check_episodes(hstore)
        returns boolean language sql as $$
        select array_agg(key order by key::int) = array_agg(key order by value::date)
        from each($1)
        $$;
    """
    lookup_name = 'check_episodes'
    function = 'check_episodes'

    @property
    def output_field(self):
        return models.BooleanField()


@models.CharField.register_lookup
class ToInteger(models.Transform):
    """
    Casts text to integer.
    """
    lookup_name = 'int'
    function = '::int'
    template = '%(expressions)s%(function)s'


@models.GenericIPAddressField.register_lookup
class NetContainsOrEquals(models.Lookup):
    """
    Address equals or inside range.
    inet '192.168.1/24' >>= inet '192.168.1/24'
    """
    lookup_name = 'net_contains_or_equals'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        return '%s >>= %s' % (lhs, rhs), params


@models.GenericIPAddressField.register_lookup
class NetContainedOrEqual(models.Lookup):
    """
    Address equals or contained in range.
    inet '192.168.1/24' <<= inet '192.168.1/24'
    """
    lookup_name = 'net_contained_or_equal'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        return '%s <<= %s' % (lhs, rhs), params


@models.GenericIPAddressField.register_lookup
class Family(models.Transform):
    """
    Returns integer of ip address protocol version.
    """
    lookup_name = 'family'

    def as_sql(self, compiler, connection, *args, **kwargs):
        lhs, params = compiler.compile(self.lhs)
        return "family(%s)" % lhs, params

    @property
    def output_field(self):
        return models.IntegerField()


@models.GenericIPAddressField.register_lookup
class Masklen(models.Transform):
    """
    Returns ip address or network net mask length.
    """
    lookup_name = 'masklen'

    def as_sql(self, compiler, connection, *args, **kwargs):
        lhs, params = compiler.compile(self.lhs)
        return "masklen(%s)" % lhs, params

    @property
    def output_field(self):
        return models.IntegerField()


models.CharField.register_lookup(Length)




