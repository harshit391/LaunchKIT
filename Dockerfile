FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN python3 --version

RUN python3 -m pip install --upgrade pip

RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r requirements.txt

COPY . .

ENTRYPOINT ["python", "launchkit/cli.py"]
