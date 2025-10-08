FROM python:3.11-slim

# Instala dependências do sistema necessárias para xhtml2pdf/reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    libxml2-dev \
    libxslt1-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia arquivos do projeto
COPY . /app

# Instala dependências Python
RUN pip install --no-cache-dir -U pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Expõe porta padrão do Fly
ENV PORT=8080

# Comando para rodar a aplicação com gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
