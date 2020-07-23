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


models.CharField.register_lookup(Length)

HStoreField.register_lookup(CheckEpisodes)

