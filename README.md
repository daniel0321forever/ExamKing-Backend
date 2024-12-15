# Preparation
### Install Redis server (Ubuntu)
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server.service  # Enable Redis to start on boot
sudo systemctl start redis-server.service   # Start Redis immediately
```

# Gaming API Documentation

This document provides an overview of the API endpoints available in the Gaming application.

## API Endpoints

### 1. AuthGoogle API
- **Endpoint:** `/auth/`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "id_token": "string"
  }
  ```
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "access_token": "string",
      "id": "integer",
      "email": "string",
      "name": "string",
      "username": "string"
    }
    ```
  - **Failure (403 Forbidden):**
    ```json
    {
      "error": "Invalid Google token"
    }
    ```

### 2. TokenLogin API
- **Endpoint:** `/token_login/`
- **Method:** `POST`
- **Request Headers:** Authorization header with Bearer token.
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "id": "integer",
      "email": "string",
      "name": "string",
      "username": "string"
    }
    ```

### 3. UserSignUp API
- **Endpoint:** `/signup/`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "email": "string",
    "username": "string",
    "password": "string",
    "name": "string"
  }
  ```
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "access_token": "string",
      "id": "integer",
      "email": "string",
      "name": "string",
      "username": "string"
    }
    ```
  - **Failure (400 Bad Request):**
    ```json
    {
      "error": "The 'field' field is required."
    }
    ```
  - **Failure (409 Conflict):**
    ```json
    {
      "error": "A user with this email or username already exists."
    }
    ```

### 4. UserLogin API
- **Endpoint:** `/login/`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "access_token": "string",
      "id": "integer",
      "email": "string",
      "name": "string",
      "username": "string"
    }
    ```
  - **Failure (401 Unauthorized):**
    ```json
    {
      "error": "Invalid credentials."
    }
    ```

### 5. CheckUsername API
- **Endpoint:** `/check_username/`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "username": "string"
  }
  ```
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "message": "username is available"
    }
    ```
  - **Failure (409 Conflict):**
    ```json
    {
      "message": "username already taken"
    }
    ```

### 6. CheckEmail API
- **Endpoint:** `/check_email/`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "email": "string"
  }
  ```
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "message": "email is available"
    }
    ```
  - **Failure (400 Bad Request):**
    ```json
    {
      "message": "email is invalid"
    }
    ```
  - **Failure (409 Conflict):**
    ```json
    {
      "message": "email already taken"
    }
    ```

### 7. SignOut API
- **Endpoint:** `/signout/`
- **Method:** `POST`
- **Response:**
  - **Success (204 No Content):**
    ```json
    {
      "message": "deleted"
    }
    ```

### 8. UserAPI
- **Endpoint:** `/user/`
- **Method:** `PATCH`
- **Request Headers:** Authorization header with Bearer token.
- **Request Body:**
  ```json
  {
    "name": "string"
  }
  ```
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "message": "user updated"
    }
    ```
  - **Failure (400 Bad Request):**
    ```json
    {
      "error": "the field 'field_name' is not permitted"
    }
    ```

### 9. Record API
- **Endpoint:** `/record/`
- **Method:** `GET` and `POST`

**GET Request:**
- **Headers:** Authorization header with Bearer token.
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "field_name": {
        "field": "string",
        "totCorrect": "integer",
        "totWrong": "integer",
        "correctRate": "float"
      },
      ...
    }
    ```

**POST Request:**
- **Headers:** Authorization header with Bearer token.
- **Request Body:**
  ```json
  {
    "field": "string",
    "totCorrect": "integer",
    "totWrong": "integer",
    "opponent": "string",
    "victory": "boolean"
  }
  ```
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "message": "updated"
    }
    ```

### 10. InitializeProblem API
- **Endpoint:** `/initialize_problem/`
- **Method:** `POST`
- **Request Headers:** Authorization header with Bearer token.
- **Response:**
  - **Success (200 OK):**
    ```json
    {
      "message": "initialized"
    }
    ```
  - **Failure (403 Forbidden):**
    ```json
    {
      "error": "no permission"
    }
    ```