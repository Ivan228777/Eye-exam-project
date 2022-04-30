from django.contrib import admin
from .models import Question, Test, Student, Test_result, Subject, Answer
import nested_admin

class AnswerInline(nested_admin.NestedTabularInline):
    model = Answer
    extra = 0


class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    inlines = [AnswerInline]
    extra = 0

class TestAdmin(nested_admin.NestedModelAdmin):
    list_display = ['text', 'subject', 'test_grade_num', 'test_grade_letter', 'created_by', 'printed_version','excel_stats', 'published_date']
    inlines = [QuestionInline]
    exclude = ['printed_version', 'test_correct_answers', 'test_code', 'slug']
    list_filter = (('created_by', admin.RelatedOnlyFieldListFilter), ('subject', admin.RelatedOnlyFieldListFilter))
    autocomplete_fields = ['created_by']


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def get_changeform_initial_data(self, request):
        get_data = super(TestAdmin, self).get_changeform_initial_data(request)
        get_data['created_by'] = request.user.pk
        return get_data

class StudentsAdmin(admin.ModelAdmin):
    list_display = ['surname', 'name', 'grade_num', 'grade_letter']
    list_filter = (('grade_num','grade_letter'))

class TestResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'test', 'grade', 'score', 'max_score']
    exclude = ['stats', 'slug']
    list_filter = (('grade', 'test', 'student'))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(teacher=request.user)


admin.site.register(Test, TestAdmin)
admin.site.register(Student, StudentsAdmin)
admin.site.register(Test_result, TestResultAdmin)
admin.site.register(Subject)
