FROM --platform=linux/arm64 amazonlinux:2
RUN amazon-linux-extras enable python3.8 && \
    yum clean metadata && \
    yum -y update && \
    yum -y install \
    python38 \
    python38-pip \
    python38-devel \
    postgresql-devel \
    gcc \
    glibc-devel \
    make \
    tar \
    which \
    && yum clean all
RUN echo "System details:" && \
    /usr/bin/uname -a && \
    cat /etc/system-release && \
    echo "Python details:" && \
    /usr/bin/python3.8 --version && \
    /usr/bin/which python3.8
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:$PATH"
COPY requirements.txt .
RUN python3.8 -m pip install --upgrade pip && \
    python3.8 -m pip install --no-cache-dir -r requirements.txt
COPY . .
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'set -ex' >> /start.sh && \
    echo 'echo "Current ENV: $ENV"' >> /start.sh && \
    echo 'echo "Python location: $(/usr/bin/which python3.8)"' >> /start.sh && \
    echo 'echo "App directory contents:"' >> /start.sh && \
    echo 'ls -la /app' >> /start.sh && \
    echo 'exec /usr/bin/python3.8 -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug' >> /start.sh && \
    chmod +x /start.sh
EXPOSE 8000
ENTRYPOINT ["/start.sh"]