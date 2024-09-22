from django.db import models


class DateModel(models.Model):
    date = models.CharField(max_length=21, null=False, blank=True)

class AgainShablonModel(models.Model):
    code = models.TextField(null=False)

class DeleteShablonModel(models.Model):
    code = models.TextField(null=False)

class FileModel(models.Model):
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")

class StatisticsModel(models.Model):
    CHOICES = (
        ("FULL", "Последняя фулл проверка"),
        ("AGAINDATA", "Последняя перепроверка"),
    )

    good = models.IntegerField(null=False)
    bad = models.IntegerField(null=False)
    check_again = models.IntegerField(null=False)
    count_domains = models.IntegerField(null=False)
    count_shop_store_domains = models.IntegerField(null=False)
    status = models.CharField(max_length=9, null=True, choices=CHOICES)


class UploadDataModel(models.Model):
    CHOICES = (
        ("GOOD", "Успешно спаршено"),
        ("BAD", "Невозможно спрасить"),
        ("AGAIN", "Отправлено на перепроверку"),
        ("NTH", "Файл пока что только загружен"),
    )

    date = models.TextField(null=False)
    domain_for_parsing = models.TextField(null=False)
    domain = models.TextField(null=False)
    phone = models.TextField(null=True)
    email = models.EmailField(null=True)
    inn = models.TextField(null=True)
    ooo = models.TextField(null=True)
    ip = models.TextField(null=True)
    is_check = models.BooleanField(default=False, null=True)
    is_showing = models.BooleanField(default=False, null=True)
    status = models.CharField(max_length=5, null=True, choices=CHOICES)

    def __str__(self):
        return self.domain

# class AgainDataModel(models.Model):
#     domain = models.TextField(null=False)