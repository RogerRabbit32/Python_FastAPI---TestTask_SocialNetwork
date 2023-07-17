# <i>FastAPI Social Network</i>
<br>

## Description

FastAPI Social Network is a simple social networking CRUD application built using FastAPI framework. It provides basic functionality to register and authenticate users, who can create, edit, delete, and view posts. Users can also like or dislike posts made by other users, but not their own posts.

## Table of Contents

- [Key Features](#key-features)
- [Set up project](#set-up-project)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Running Tests](#running-tests)
- [Technologies Used](#technologies-used)

## Key Features


Registration/Authorization: Users can sign up and login, using JWT tokens. There are also registration credentials requirements implemented, which disallow duplicate usernames and emails and restrict creation of too simple passwords and logins. 

<i><b>NOTE!</b> As additional features there are also email validation and user data enrichment in place. These features use external APIs (hunter.io and clearbit.com) and require API keys to be set up as project environment variables. Without them, the project will not work as expected.</i>

Post Management: Users can create, edit, delete, and view posts. Posts are stored in the PostgreSQL database, utilizing Docker volumes, ensuring data persistence.

Post Likes/Dislikes: Users can like or dislike posts made by other users, but not their own posts. Likes are stored in a Redis cache for faster access.


## Set up project

### Prerequisites
Before running the application, make sure you have the following dependencies installed on your system:

- Docker: [Install Docker](https://docs.docker.com/get-docker/)
- Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/)

### Installation

1. Clone the repository to your local machine and make it your current working directory:

```
git clone https://github.com/RogerRabbit32/Python_FastAPI---TestTask_SocialNetwork.git
cd SocialNetwork
```

2. Inside the directory, create a <b>'.env'</b> file (this particular name is referenced in the docker-compose environment variable), where you have to specify two variables, storing your API keys:<p><br><code>HUNTER_API_KEY= CLEARBIT_API_KEY=</code></p><br>These keys will grant the application access to hunter.io and clearbit.com services. Without them, user registration will not be available and the project will not work properly.<br>


4. Build the Docker image. Run the command:

```
docker-compose build
```

5. Start the containers. Run the command:

```
docker-compose up
```


If the installation is successful, your app should be available at [https://localhost:8000](https://localhost:8000)

## Usage

All project API routes are available for tryouts via Swagger documentation [https://localhost:8000/docs](https://localhost:8000/docs)


<b>Register user</b>

Create a new user in the database with the specified login and password.

Route: `POST /accounts/signup`

<i>NOTE! A valid email has to be provided at this stage, since all emails are verified through emailhunter.co If additional data is available on the user through clearbit.com email enrichment, the user's full name, if not provided by the user himself, will be automatically added to registration credentials.</i>


<b>Login user</b>

Create a new JWT access token for the user. (Authentication also available via form data in Swagger docs)

Route: `POST /accounts/login`


<b>Create Post</b>

Create a new post with the specified title and text.

Route: `POST /posts`


<b>Get All Posts</b>

Fetch all posts with optional pagination support (limit and offset).

Route: `GET /posts`


<b>Get User's Own Posts</b>

Fetch all posts created by the currently authenticated user.

Route: `GET /posts/user`


<b>Get Single Post</b>

Fetch a single post by its ID.

Route: `GET /posts/{post_id}`


<b>Update User's Own Post</b>

Update a post created by the currently authenticated user.

Route: `PUT /posts/{post_id}`


<b>Delete a Post</b>

Delete a post created by the currently authenticated user.

Route: `DELETE /posts/{post_id}`


<b>Like/Dislike a Post</b>

Like or dislike a post made by other users.

Route: `POST /posts/{post_id}/like`


<b>Unlike/Remove Like from a Post</b>

Remove a previously liked or disliked post.

Route: `DELETE /posts/{post_id}/like`


<b>Get Post Likes</b>

Fetch all likes (and dislikes) for a specific post.

Route: `GET /accounts/{post_id}/likes`

## Running tests

When the containers are up, you can run the tests for the application by typing the following command in a new terminal:

```
docker-compose exec app pytest
```

This will execute the pytest autotests suite, stored in <b>/tests</b> directory

## Technologies used
<ul>
<li>FastAPI: Python Web framework for building APIs</li>
<li>pytest: Python framework for tests management</li>
<li>PostgreSQL: Database management system for storing application data</li>
<li>Redis: In-memory data store for handling likes/dislikes functionality</li>
<li>Docker + Docker Compose: Containerization for easy deployment</li>
</ul>
