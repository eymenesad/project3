from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_manager = models.BooleanField(default=False)
    is_player = models.BooleanField(default=False)
    is_coach = models.BooleanField(default=False)
    is_jury = models.BooleanField(default=False)

    class Meta:
        # Adding unique related_names to avoid clashes
        db_table = 'custom_user'
        swappable = 'AUTH_USER_MODEL'
        permissions = (
            ('view_user', 'Can view user'),
        )

User._meta.get_field('groups').related_query_name = 'customuser_groups'
User._meta.get_field('groups').related_name = 'customuser_groups'

User._meta.get_field('user_permissions').related_query_name = 'customuser_permissions'
User._meta.get_field('user_permissions').related_name = 'customuser_permissions'
