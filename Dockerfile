# Career Compiler: Complete Production Container
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system utilities and Poppler tools (pdftotext, pdffonts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic binary
RUN curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.tectonic-typesetting.net | sh \
    && mv tectonic /usr/local/bin/

# Copy project files
COPY pyproject.toml README.md ./
COPY careercompiler careercompiler
COPY templates templates
COPY frontend/dist frontend/dist

# Install Python dependencies and CLI
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["careercompiler", "serve", "--host", "0.0.0.0", "--port", "8000"]
