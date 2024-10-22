FROM python:3.11-slim 
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1 
WORKDIR /root 
COPY . . 
RUN pip install --upgrade pip \ 
    && pip install selenium==4.5.0
CMD ["python", "insider.py"]
