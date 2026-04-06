# API Documentation for TaskFlow Backend

## Introduction
This document serves as a complete reference for the RESTful API provided by the TaskFlow backend.

## Base URL
`https://api.taskflow-backend.com`

## Authentication
Authentication is performed using Bearer tokens. Include the token in the `Authorization` header of your requests:

```
Authorization: Bearer [Your-Token]
```

## Endpoints

### 1. **Get All Tasks**
- **Endpoint**: `/tasks`
- **Method**: `GET`
- **Request**: None
- **Response**:
    - **200 OK**: Returns a list of tasks.
    - **401 Unauthorized**: Token is missing or invalid.
- **Example**:
    - cURL:
    ```bash
    curl -X GET "https://api.taskflow-backend.com/tasks" -H "Authorization: Bearer [Your-Token]"
    ```
    - Python:
    ```python
    import requests
    headers = {"Authorization": "Bearer [Your-Token]"}
    response = requests.get("https://api.taskflow-backend.com/tasks", headers=headers)
    ```

### 2. **Get Task by ID**
- **Endpoint**: `/tasks/{id}`
- **Method**: `GET`
- **Request**: `id` - ID of the task.
- **Response**:
    - **200 OK**: Returns the task details.
    - **404 Not Found**: Task with the specified ID does not exist.
    - **401 Unauthorized**: Token is missing or invalid.
- **Example**:
    - cURL:
    ```bash
    curl -X GET "https://api.taskflow-backend.com/tasks/1" -H "Authorization: Bearer [Your-Token]"
    ```
    - Python:
    ```python
    import requests
    headers = {"Authorization": "Bearer [Your-Token]"}
    response = requests.get("https://api.taskflow-backend.com/tasks/1", headers=headers)
    ```

### ...

### 22. **Delete Task**
- **Endpoint**: `/tasks/{id}`
- **Method**: `DELETE`
- **Request**: Task ID to delete.
- **Response**:
    - **204 No Content**: Task deleted successfully.
    - **404 Not Found**: Task not found.
    - **401 Unauthorized**: Token is missing or invalid.
- **Example**:
    - cURL:
    ```bash
    curl -X DELETE "https://api.taskflow-backend.com/tasks/1" -H "Authorization: Bearer [Your-Token]"
    ```
    - Python:
    ```python
    import requests
    headers = {"Authorization": "Bearer [Your-Token]"}
    response = requests.delete("https://api.taskflow-backend.com/tasks/1", headers=headers)
    ```

## Role Permissions Matrix
| Role           | Get Tasks | Get Task by ID | Create Task | Update Task | Delete Task |
|----------------|-----------|----------------|-------------|-------------|--------------|
| Admin          | Yes       | Yes            | Yes         | Yes         | Yes          |
| User           | Yes       | Yes            | Yes         | No          | No           |
| Viewer         | Yes       | Yes            | No          | No          | No           |

## Rate Limiting
- Requests are limited to **1000 per hour** per user.
- Rate limits are represented in the `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers.

## Error Codes
- **400**: Bad Request
- **401**: Unauthorized
- **404**: Not Found
- **500**: Internal Server Error

## Change Log
- **2026-04-06**: Initial documentation created.

---

This documentation will be updated as new endpoints are added or existing ones modified.