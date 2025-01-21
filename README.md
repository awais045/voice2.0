
# Voice2.2 API

Voice2.2 is a project management tool that allows teams to collaborate on projects. It helps to manage users, projects, tasks, and comments. This API can be consumed by the front-end web app and mobile app.



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

## Authentication

Token-based authentication is used for API endpoints. After logging in, obtain a token and include it in the header of subsequent requests as follows: