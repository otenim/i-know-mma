FROM python:3.11.6 AS builder
RUN pip install Scrapy==2.11.0 click==8.1.7 scrapy-rotating-proxies==0.6.2

FROM python:3.11.6-slim
WORKDIR /scripts
COPY --from=builder /usr/local/bin/scrapy /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY scraper ./scraper
COPY scrapy.cfg .