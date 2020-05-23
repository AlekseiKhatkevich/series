from django.contrib.auth.tokens import default_token_generator
from djoser import utils
from djoser.conf import settings as djoser_settings

from templated_mail.mail import BaseEmailMessage


class SlaveActivationEmail(BaseEmailMessage):
    """
    Sends email to slave with a link to confirm that slave is agreed to switch his(hers) account
    as a slave account.
    """
    template_name = 'slave_activation.html'

    def get_context_data(self):
        context = super().get_context_data()

        master = context['master']
        slave = context['slave']

        context['master_name'] = master.get_full_name()
        context['master_email'] = master.email

        context['master_uid'] = utils.encode_uid(master.pk)
        context['slave_uid'] = utils.encode_uid(slave.pk)

        context['token'] = default_token_generator.make_token(slave)
        context['url'] = djoser_settings.SLAVE_ACTIVATION_URL.format(**context)

        return context


class UserUndeleteEmail(BaseEmailMessage):
    """
    Sends emails to user who want to restore their soft-deleted accounts.
    """
    template_name = 'undelete_account.html'

    def get_context_data(self):
        context = super().get_context_data()
        soft_deleted_user = context['soft_deleted_user']

        context['uid'] = utils.encode_uid(soft_deleted_user.pk)
        context['token'] = default_token_generator.make_token(soft_deleted_user)
        context['url'] = djoser_settings.USER_UNDELETE_URL.format(**context)

        return context