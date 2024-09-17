from django.db import models


class DateModel(models.Model):
    date = models.CharField(max_length=21)

class AgainShablonModel(models.Model):
    code = models.TextField(null=False)

class DeleteShablonModel(models.Model):
    code = models.TextField(null=False)

class FileModel(models.Model):
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")

class StatisticsModel(models.Model):
    good = models.IntegerField(null=False)
    bad = models.IntegerField(null=False)
    check_again = models.IntegerField(null=False)
    file = models.OneToOneField(FileModel, null=True, on_delete=models.SET_NULL)

class ShowDataModel(models.Model):
    domain = models.TextField(null=False)
    phone = models.CharField(max_length=20, null=True)
    email = models.EmailField(null=True)
    inn = models.CharField(max_length=15, null=True)
    ooo = models.TextField(null=True)
    ip = models.TextField(null=True)
    file = models.OneToOneField(FileModel, null=True, on_delete=models.SET_NULL)

class AgainDataModel(models.Model):
    domain = models.TextField(null=False)