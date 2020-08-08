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
    Returns difference between 2 JSONs.

    CREATE OR REPLACE FUNCTION json_diff(left_json JSONB, right_json JSONB) RETURNS JSONB AS
    $json_diff$
    SELECT jsonb_object_agg(left_items.key, left_items.value) FROM
        ( SELECT key, value FROM jsonb_each(left_json) ) as left_items LEFT OUTER JOIN
        ( SELECT key, value FROM jsonb_each(right_json) ) as right_items using(key)
    WHERE left_items.value != right_items.value OR right_items.key IS NULL;
    $json_diff$
    LANGUAGE sql;
    """
    function = 'json_diff'
    arity = 2
    output_field = JSONField()


