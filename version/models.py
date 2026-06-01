from django.db import models

class AppVersion(models.Model):
    version = models.CharField(max_length=20, unique=True)
    release_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'app_version'
        ordering = ['-release_date']

    def __str__(self):
        return self.version
