FROM python:3.12-slim

# Непривилегированный пользователь
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin ctfuser

WORKDIR /app

# Зависимости фиксируем по версии
RUN pip install --no-cache-dir flask==3.0.3

# Код сразу с нужным владельцем
COPY --chown=ctfuser:ctfuser app.py /app/app.py

# Понижаем привилегии
USER ctfuser

EXPOSE 5000
CMD ["python", "app.py"]
