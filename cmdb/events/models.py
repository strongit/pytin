from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_init, pre_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from cmdb.settings import logger
from resources.models import Resource, ResourceOption

RESOURCE_HISTORY_FIELDS = ['parent_id', 'name', 'type', 'status']


class HistoryEvent(models.Model):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'

    TYPES = (
        (CREATE, 'create'),
        (UPDATE, 'update'),
        (DELETE, 'delete'),
    )

    resource = models.ForeignKey(Resource)
    type = models.CharField(max_length=64, choices=TYPES, db_index=True)
    field_name = models.CharField(max_length=155, db_index=True, null=True)
    field_old_value = models.CharField(max_length=255, db_index=True, null=True)
    field_new_value = models.CharField(max_length=255, db_index=True, null=True)
    created_at = models.DateTimeField(null=False, db_index=True)

    class Meta:
        db_table = "resource_history"

    @staticmethod
    def add_create(resource):
        assert isinstance(resource, Resource)

        event = HistoryEvent(resource=resource, type=HistoryEvent.CREATE)
        event.save()

    @staticmethod
    def add_update(resource, field_name, field_old_value, field_new_value):
        assert isinstance(resource, Resource)
        assert field_name

        event = HistoryEvent(resource=resource, type=HistoryEvent.UPDATE, field_name=field_name,
                             field_old_value=field_old_value, field_new_value=field_new_value)
        event.save()

    @staticmethod
    def add_delete(resource):
        assert isinstance(resource, Resource)

        event = HistoryEvent(resource=resource, type=HistoryEvent.DELETE)
        event.save()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = timezone.now()

        super(HistoryEvent, self).save(*args, **kwargs)


####### Attach history models to the resources #######

@receiver(post_init)
def resource_post_init(sender, instance, **kwargs):
    if not issubclass(sender, Resource):
        return

    for field in RESOURCE_HISTORY_FIELDS:
        value = getattr(instance, field)
        setattr(instance, '_original_%s' % field, value)
        logger.debug("POST INIT: %s %s %s" % (instance, field, value))


@receiver(post_save)
def resource_post_save(sender, instance, created, **kwargs):
    if not issubclass(sender, Resource):
        return

    if created:
        HistoryEvent.add_create(instance)
    else:
        for field in RESOURCE_HISTORY_FIELDS:
            value = getattr(instance, field)
            history_field = '_original_%s' % field

            logger.debug("POST SAVE: %s %s %s" % (instance, field, value))

            if hasattr(instance, history_field):
                orig_value = getattr(instance, history_field)

                logger.debug("    original value: %s" % orig_value)

                if unicode(value) != unicode(orig_value):
                    HistoryEvent.add_update(instance, field, orig_value, value)
                    setattr(instance, '_original_%s' % field, value)


@receiver(pre_delete)
def resource_post_delete(sender, instance, using, **kwargs):
    if not issubclass(sender, Resource):
        return

    HistoryEvent.add_delete(instance)


@receiver(post_init, sender=ResourceOption)
def resource_option_post_init(sender, instance, **kwargs):
    setattr(instance, '_original_value', instance.value)


@receiver(post_save, sender=ResourceOption)
def resource_option_post_save(sender, instance, created, **kwargs):
    field_name = instance.name
    field_new_value = instance.value

    # ability to ignore some fields (such as heartbeat), to prevent event table flooding.
    if not instance.journaling:
        return

    history_field = '_original_value'
    if hasattr(instance, history_field):
        field_old_value = getattr(instance, history_field)
        if unicode(field_new_value) != unicode(field_old_value) or created:
            field_old_value = None if created else field_old_value
            HistoryEvent.add_update(instance.resource, field_name, field_old_value, field_new_value)
