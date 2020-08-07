from django.db.models import BooleanField, Func, JSONField


class IpCount(Func):
    """
    Returns True if count of entries with same user_id less then limit,
     other way returns False.

    create or replace function count_ips(v_user_id int, v_limit int)
                            returns boolean as $$
                            select count(*) <= v_limit
                            from {db_table_name}
                            where user_id = v_user_id
                            $$ language sql;
    """
    function = 'count_ips'
    arity = 2
    output_field = BooleanField()


class JSONDiff(Func):
    """

    """
    function = 'json_diff'
    arity = 2
    output_field = JSONField


