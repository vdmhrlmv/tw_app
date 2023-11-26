FROM python:3.10

WORKDIR /usr/src/pad

RUN pip install --upgrade pip

COPY requirements_prod.txt .

RUN pip install -r requirements_prod.txt

COPY . .

# RUN chmod a+x docker/*.sh
