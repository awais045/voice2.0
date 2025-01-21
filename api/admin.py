from django.contrib import admin
from .models import Project, ProjectMember, Task, Comment, User

admin.site.register(Project)
admin.site.register(ProjectMember)
admin.site.register(Task)
admin.site.register(Comment)
admin.site.register(User)
