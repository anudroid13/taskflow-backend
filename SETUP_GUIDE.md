# FastAPI Setup Guide

## Prerequisites
Before you begin, ensure you have the following installed on your system:
- **Python 3.7 or higher**: You can download it from [python.org](https://www.python.org/downloads/).
- **pip**: This is the package installer for Python, which usually comes pre-installed with Python.
- **Virtual Environment (optional)**: It's recommended to use a virtual environment to manage dependencies (you can use `venv` or `virtualenv`).

## Installation
1. **Clone the Repository**
   ```bash
   git clone https://github.com/anudroid13/taskflow-backend.git
   cd taskflow-backend
   ```  

2. **Set up a Virtual Environment (optional)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```  

3. **Install Required Packages**
   ```bash
   pip install -r requirements.txt
   ```  

## Environment Configuration
1. **Create a `.env` File**
   Copy the example environment file and edit it with your configuration:
   ```bash
   cp .env.example .env
   ```  
   Modify the `.env` file according to your setup.

2. **Setting Environment Variables**: Ensure you set all necessary environment variables in the `.env` file, including:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - Other relevant configurations based on your requirements.

## Running the Application
To run the FastAPI application, execute the following command:
```bash
uvicorn main:app --reload
```
- This will start the server at `http://127.0.0.1:8000`
- You can access the documentation by navigating to `http://127.0.0.1:8000/docs`

## Troubleshooting Steps
- **Error: Port already in use**: If you encounter a port conflict, you can change the port by modifying the command as follows:
  ```bash
  uvicorn main:app --reload --port 8001
  ```
- **Missing Dependencies**: If you get an import error, make sure you have installed all required packages listed in `requirements.txt`.
- **Database Connection Issues**: Verify your `DATABASE_URL` in the `.env` file is correct and that your database server is up and running.
- For any other issues, refer to the [FastAPI documentation](https://fastapi.tiangolo.com/) or check the repository's GitHub issues.

---
With the above setup, you should be able to run and develop your FastAPI application without any issues!