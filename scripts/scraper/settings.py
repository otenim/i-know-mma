# Scrapy settings for scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
BOT_NAME = "scraper"
SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2.5

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 60 * 60 * 24 * 365
HTTPCACHE_IGNORE_HTTP_CODES = [
    400,  # Bad Request
    401,  # Unauthorized
    402,  # Payment Required
    403,  # Forbidden
    404,  # Not Found
    405,  # Method Not Allowed
    406,  # Not Acceptable
    407,  # Proxy Authentication Required
    408,  # Request Timeout
    409,  # Conflict
    410,  # Gone
    411,  # Length Required
    412,  # Precondition Failed
    413,  # Payload Too Large
    414,  # URI Too Long
    415,  # Unsupported Media Type
    416,  # Range Not Satisfiable
    417,  # Expectation Failed
    418,  # I’m a teapo
    421,  # Misdirected Request
    425,  # Too Early
    426,  # Upgrade Required
    428,  # Precondition Required
    429,  # Too Many Requests
    431,  # Request Header Fields Too Large
    451,  # Unavailable For Legal Reasons
    500,  # Internal Server Error
    501,  # Not Implemented
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
    505,  # Version Not Supported
    506,  # Variant Also Negotiates
    507,  # Insufficient Storage (WebDAV)
    508,  # Loop Detected (WebDAV)
    510,  # Not Extended
    511,  # Network Authentication Required
]

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
