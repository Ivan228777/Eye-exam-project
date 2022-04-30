from django.db import models
from django.contrib.auth.models import User
from transliterate import slugify, translit

from django.utils.html import format_html

BASE_DIR = 'http://127.0.0.1:8000/tasks/'

class Subject(models.Model):
    text = models.CharField(max_length=100)

    def __str__(self):
        return self.text


class Test(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    text = models.CharField(max_length=100)
    published_date = models.DateTimeField(blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True)
    models.PositiveIntegerField(primary_key=True)
    test_grade_num = models.IntegerField(null=True)
    CHOICES = (
        ('А', 'А'),
        ('Б', 'Б'),
        ('В', 'В'),
        ('Г', 'Г'),
        ('Д', 'Д'),
    )
    test_grade_letter = models.CharField(max_length=1, choices=CHOICES)
    test_correct_answers = models.CharField(max_length=200, default='')
    slug = models.SlugField(null=True, blank=True)

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        value = str(self.test_grade_num) + ' ' + str(self.test_grade_letter) + ' ' + str(self.text)
        value = translit(value, 'ru')
        self.slug = slugify(value)
        super().save(*args, **kwargs)
        if self.slug is None:
            self.slug = slugify(value)
            self.save()

    @property
    def printed_version(self):
        url = BASE_DIR + str(self.id)
        return format_html('<a href="{}">Печать</a>', url)

    @property
    def excel_stats(self):
        url = BASE_DIR + str(self.slug) + '/' + 'excel'
        return format_html('<a href="{}">Скачать</a>', url)

class Question(models.Model):
    text = models.CharField(max_length=200)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)

    def __str__(self):
        return self.text

class Student(models.Model):
    surname = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True)
    grade_num = models.IntegerField()
    CHOICES = (
        ('А', 'А'),
        ('Б', 'Б'),
        ('В', 'В'),
        ('Г', 'Г'),
        ('Д', 'Д'),
    )
    grade_letter = models.CharField(max_length=1, choices=CHOICES, null=True)

    def __str__(self):
        return self.name + ' ' + self.surname


class Answer(models.Model):
    text = models.CharField(max_length=100)
    is_correct = models.BooleanField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return self.text

class Test_result(models.Model):
    student = models.CharField(max_length=120)
    student_id = models.IntegerField(null=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    score = models.IntegerField()
    max_score = models.IntegerField(null=True)
    grade = models.CharField(max_length=10, default='')
    stats = models.CharField(max_length=120, null=True)
    slug = models.CharField(max_length=120, null=True)


    def __str__(self):
        return self.student
