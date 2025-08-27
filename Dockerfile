# Use Python 3.11 slim base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV ACCEPT_EULA=Y

# Set work directory
WORKDIR /app

# Install system dependencies including Microsoft ODBC drivers
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        wget \
        gnupg2 \
        apt-transport-https \
        ca-certificates \
        lsb-release \
        unixodbc-dev \
        g++ \
        build-essential \
        telnet \
        iputils-ping \
        dnsutils \
        net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 18 for SQL Server (fixed approach)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/repos/microsoft-debian-bullseye-prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 \
    && echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set ODBC environment variables
ENV ODBCINI=/etc/odbc.ini
ENV ODBCSYSINI=/etc
ENV PATH="$PATH:/opt/mssql-tools18/bin"

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Copy database utilities and scripts
COPY test_db_connection.py /app/
COPY db_utils.py /app/
COPY debug_connection.sh /app/
RUN chmod +x /app/debug_connection.sh

# Create directories for static files, media files, and logs
RUN mkdir -p /app/staticfiles /app/mediafiles /app/logs

# Create non-root user and set permissions
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app \
    && chmod +x /app/debug_connection.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check with database connectivity test
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD python /app/test_db_connection.py --health-check || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "familyhub_timesheet.wsgi:application"]
