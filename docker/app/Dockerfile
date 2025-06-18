FROM python:3.11

ARG work_dir=/var/www
RUN mkdir ${work_dir}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONNUNBUFFERED 1

WORKDIR ${work_dir}

COPY ./. ${work_dir}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    default-libmysqlclient-dev \
    poppler-utils \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --upgrade pip &&\
    pip install debugpy &&\
    pip install -r requirements.txt &&\
    pip install --no-cache-dir google-adk

RUN groupadd -g 1000 www
RUN useradd -u 1000 -ms /bin/bash -g www www

# Create logs directory and set permissions
RUN mkdir -p ${work_dir}/logs && \
    chown -R www:www ${work_dir}/logs

# Copy existing application directory permissions
COPY --chown=www:www . ${work_dir}

# Ensure www user has access to python packages and set ADK config
ENV PATH="/usr/local/bin:$PATH"
ENV ADK_HOST="0.0.0.0"
ENV ADK_PORT="8002"

# Set up startup script
COPY docker/app/start.sh /start.sh
RUN chmod +x /start.sh && \
    chown www:www /start.sh

RUN echo 'export PATH="/usr/local/bin:$PATH"' >> /home/www/.bashrc && \
    echo 'export PATH="/usr/local/bin:$PATH"' >> /home/www/.profile && \
    echo 'export ADK_HOST="0.0.0.0"' >> /home/www/.bashrc && \
    echo 'export ADK_PORT="8002"' >> /home/www/.bashrc
# Switch to non-root user
USER www

# Use the startup script as the entrypoint
CMD ["/start.sh"]
