from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TaskViewSet, CommentViewSet
from .views import RegisterUserView, LoginUserView, UserDetailsView, UserUpdateView, UserDeleteView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
    path('users/register/', RegisterUserView.as_view(), name='register'),
    path('users/login/', LoginUserView.as_view(), name='login'),
    path('users/<int:pk>/', UserDetailsView.as_view(), name='user-details'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),
]

#Custom url
project_tasks = TaskViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
task_detail = TaskViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

task_comments = CommentViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
comment_detail = CommentViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns += [
    path('projects/<int:project_id>/tasks/', project_tasks, name='project-task-list-create'),
    path('tasks/<int:id>/', task_detail, name='task-detail'),
    path('tasks/<int:task_id>/comments/', task_comments, name='task-comment-list-create'),
    path('comments/<int:id>/', comment_detail, name='comment-detail'),
]
