
# TeamCollab API

TeamCollab is a project management tool that allows teams to collaborate on projects. It helps to manage users, projects, tasks, and comments. This API can be consumed by the front-end web app and mobile app.



## Features

- JWT Authentication
- Custom User Model
- Full CRUD functionality
- API Doc by Swagger
- And many more.


## Tech Stack

**Programming Language:** Python

**Database:** SQLite

**Framework:** Django, DRF


## Installation

Clone the repository:

```bash
  git clone https://github.com/fahadfoysal/TeamCollab.git

```
Install dependencies:
```bash
  pip install -r requirements.txt

``` 
Apply database migrations:

```bash
  python manage.py migrate

```
Run the development server:
```bash
  python manage.py runserver

``` 
## Usage/Examples

```
Access the Django admin panel at http://localhost:8000/admin/ to manage everything.

Access Swagger UI for better API doc at http://127.0.0.1:8000/swagger/


## API Endpoints for Users

- Register User (POST /api/users/register/): Create a new user.
- Login User (POST /api/users/login/): Authenticate a user and return a token.
- Get User Details (GET /api/users/{id}/): Retrieve details of a specific user.
- Update User (PUT/PATCH /api/users/{id}/): Update user details.
- Delete User (DELETE /api/users/{id}/): Delete a user account.

## Authentication

Token-based authentication is used for API endpoints. After logging in, obtain a token and include it in the header of subsequent requests as follows:

## API Endpoints for Projects

- List Projects (GET /api/projects/): Retrieve a list of all projects.
- Create Project (POST /api/projects/): Create a new project.
- Retrieve Project (GET /api/projects/{id}/): Retrieve details of a specific project.
- Update Project (PUT/PATCH /api/projects/{id}/): Update project details.
- Delete Project (DELETE /api/projects/{id}/): Delete a project.

## API Endpoints for Task

- List Tasks (GET /api/projects/{project_id}/tasks/): Retrieve a list of all tasks in
a project.
- Create Task (POST /api/projects/{project_id}/tasks/): Create a new task in a
project.
- Retrieve Task (GET /api/tasks/{id}/): Retrieve details of a specific task.
- Update Task (PUT/PATCH /api/tasks/{id}/): Update task details.
- Delete Task (DELETE /api/tasks/{id}/): Delete a task.

## API Endpoints for Comments

- List Comments (GET /api/tasks/{task_id}/comments/): Retrieve a list of all
comments on a task.
- Create Comment (POST /api/tasks/{task_id}/comments/): Create a new
comment on a task.
- Retrieve Comment (GET /api/comments/{id}/): Retrieve details of a specific
comment.
- Update Comment (PUT/PATCH /api/comments/{id}/): Update comment
details.
- Delete Comment (DELETE /api/comments/{id}/): Delete a comment.
