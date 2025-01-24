from django.db import models

# Create your models here.

class Menu(models.Model):
    name = models.CharField(max_length=128)
    parent = models.ForeignKey(on_delete=models.CASCADE)

class Archive(models.Model):
    name = models.CharField(max_length=128)
    extension = models.CharField(max_length=32)
    description = models.CharField(max_length=256)
    # references missing

class Directory(models.Model):
    name = models.CharField(max_length=128)
