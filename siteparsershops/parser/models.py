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
        ("DEL", "Удалили самостоятельно"),
    )

    CHOICES_GOOD = (
        ("TAKE", "Берем в работу"),
        ("ALREADY", "Уже есть договор"),
        ("NOTNEED", "Договор не нужен"),
        ("DOESNOT", "Не подходит"),
    )

    date = models.TextField(null=False)
    domain_for_parsing = models.TextField(null=False)
    domain = models.TextField(null=False)
    phone = models.TextField(null=True)
    email = models.TextField(null=True)
    inn = models.TextField(null=True)
    ooo = models.TextField(null=True)
    ip = models.TextField(null=True)
    is_check = models.BooleanField(default=False, null=True)
    is_showing = models.BooleanField(default=False, null=True)
    it_was_good = models.BooleanField(default=False, null=True)
    status = models.CharField(max_length=5, null=True, choices=CHOICES)
    status_good = models.CharField(max_length=7, null=True, choices=CHOICES_GOOD)

    def __str__(self):
        return self.domain

class DateForCalendar(models.Model):
    CHOICES = (
        ("NTH", "Даты загружены, но не спаршены"),
        ("SCF", "Даты спаршены"),
    )

    status = models.CharField(max_length=5, null=True, default="NTH", choices=CHOICES)
    date = models.TextField(null=False)