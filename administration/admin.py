import ipaddress

from django import forms
from django.contrib import admin
from django.db.models import F, Func, GenericIPAddressField, Q
from django.db.models.expressions import RawSQL
from django.db.models.functions import Cast, Now

from administration.helpers import validators as admin_validators
from administration.models import IpBlacklist


class IpBlacklistAdminForm(forms.ModelForm):
    """
    Form for 'BlackListAdmin'.
    """
    ip = forms.CharField(
        max_length=43,
        validators=[admin_validators.ValidateIpAddressOrNetwork(8), ]
    )

    class Meta:
        model = IpBlacklist
        fields = ('ip', 'stretch', )


class IsActiveFilter(admin.SimpleListFilter):
    """
    Segregates IP blacklist entries into active and expired ones.
    """
    title = 'Is blacklisting active?'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('true', 'Active'),
            ('false', 'Expired'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.only_active()
        elif self.value() == 'false':
            return queryset.exclude(record_time__gt=Now() - F('stretch'))
        else:
            return queryset


class IpOrNetworkFilter(admin.SimpleListFilter):
    """
    Segregates IP blacklist entries into plain ips or networks.
    """
    title = 'ip or network?'
    parameter_name = 'ip_or_network'

    def lookups(self, request, model_admin):
        return (
            ('ip', 'IP'),
            ('network', 'Network'),
        )

    def queryset(self, request, queryset):
        condition = Q(ip=Cast(Func(F('ip'), function='HOST'), output_field=GenericIPAddressField()))
        if self.value() == 'ip':
            return queryset.filter(condition)
        elif self.value() == 'network':
            return queryset.exclude(condition)
        else:
            return queryset


@admin.register(IpBlacklist)
class BlackListAdmin(admin.ModelAdmin):
    """
    Admin for 'IpBlacklist' model in administration app.
    """
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
    list_filter = (IsActiveFilter, IpOrNetworkFilter,)
    ordering = ('-record_time',)
    save_as = True
    search_fields = ('^ip',)
    form = IpBlacklistAdminForm

    def get_search_results(self, request, queryset, search_term):
        """
        Uses 'startswith' lookup when non valid search_term is provided.
        For example 127.0.0
        Uses combination of <<= or >>= (equals or contained by or equals or contains)
        when fully qualified ipv4 or ipv6 address or network is provided.
        """
        try:
            ipaddress.ip_network(search_term, strict=False)
            qualified_ip_condition = Q(ip__net_contains_or_equals=search_term) | \
                                     Q(ip__net_contained_or_equal=search_term)
            return queryset.filter(qualified_ip_condition), False
        except ValueError:
            main_condition = Q(ip__startswith=search_term)
            return queryset.filter(main_condition), False

    def get_readonly_fields(self, request, obj=None):
        """
        Forbids 'ip' field to get changed on entry data update in admin.
        """
        if obj:
            return self.readonly_fields + ('ip',)
        return self.readonly_fields

    def ip_version(self, obj: IpBlacklist) -> int:
        """
        Returns ip protocol version of blacklisted ip entry.
        """
        return ipaddress.ip_network(obj.ip, strict=False).version

    def is_network_or_ip(self, obj: IpBlacklist) -> str:
        """
        Defines whether ip blacklist entry is a plain ip or network.
        """
        ip_obj = ipaddress.ip_network(obj.ip, strict=False)

        return 'IP' if ip_obj.prefixlen == ip_obj.max_prefixlen else 'Network'

    def get_form(self, request, obj=None, change=False, **kwargs):
        return super().get_form(request, obj, change, **kwargs)

    ip_version.short_description = 'IP protocol version'
    ip_version.admin_order_field = F('ip__family')

    is_network_or_ip.short_description = 'IP or Network'
    is_network_or_ip.admin_order_field = RawSQL("ip = Cast(HOST(ip) as inet)", params=())
