import ipaddress

from django.contrib import admin
from django.db.models import F, Func
from django.db.models.expressions import RawSQL

from administration.models import IpBlacklist


class IsActiveFilter(admin.SimpleListFilter):
    title = 'Is blacklisting active?'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):

@admin.register(IpBlacklist)
class BlackListAdmin(admin.ModelAdmin):
    date_hierarchy = 'record_time'
    list_display = (
        'ip',
        'ip_version',
        'is_network_or_ip',
        'record_time',
        'stretch',
        'is_active',
        'stretch_remain',
    )
    #list_filter = ('stretch__gte=0', )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('ip', )
        return self.readonly_fields

    def ip_version(self, obj):
        """
        Returns ip protocol version of blacklisted ip entry.
        """
        return ipaddress.ip_network(obj.ip, strict=False).version

    def is_network_or_ip(self, obj):
        """
        Defines whether ip blacklist entry is a plain ip or network.
        """
        ip_obj = ipaddress.ip_network(obj.ip, strict=False)

        return 'IP' if ip_obj.prefixlen == ip_obj.max_prefixlen else 'Network'

    ip_version.short_description = 'IP protocol version'
    ip_version.admin_order_field = Func(F('ip'), function='FAMILY')

    is_network_or_ip.short_description = 'IP or Network'
    is_network_or_ip.admin_order_field = RawSQL("ip = Cast(host(ip) as inet)", params=())











