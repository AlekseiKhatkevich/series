from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.db.models.functions import Length


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


class ToInteger(models.Transform):
    """
    Casts text to integer.
    """
    lookup_name = 'int'
    function = '::int'
    template = '%(expressions)s%(function)s'


class Family(models.Transform):
    """
    Extracts protocol version from ip address.
    """
    lookup_name = 'family'
    function = 'FAMILY'


class Masklen(models.Transform):
    """
    Extracts length of the mask from ip address.
    """
    lookup_name = 'masklen'
    function = 'MASKLEN'


models.CharField.register_lookup(Length)
models.CharField.register_lookup(ToInteger)

HStoreField.register_lookup(CheckEpisodes)

models.GenericIPAddressField.register_lookup(Family)
models.GenericIPAddressField.register_lookup(Masklen)