BOT_NAME = "bot"
SPIDER_MODULES = ["scraper.tapology"]

CONCURRENT_REQUESTS = 1
# CONCURRENT_REQUESTS_PER_DOMAIN = 100
# AUTOTHROTTLE_ENABLED = True
# AUTOTHROTTLE_TARGET_CONCURRENCY = 50
DOWNLOAD_DELAY = 3
# ROTATING_PROXY_LIST = {
#     "rotating-residential.geonode.com:9000",
#     "rotating-residential.geonode.com:9001",
#     "rotating-residential.geonode.com:9002",
#     "rotating-residential.geonode.com:9003",
#     "rotating-residential.geonode.com:9004",
#     "rotating-residential.geonode.com:9005",
#     "rotating-residential.geonode.com:9006",
#     "rotating-residential.geonode.com:9007",
#     "rotating-residential.geonode.com:9008",
#     "rotating-residential.geonode.com:9009",
#     "rotating-residential.geonode.com:9010",
# }
# DOWNLOADER_MIDDLEWARES = {
#     "rotating_proxies.middlewares.RotatingProxyMiddleware": 610,
#     "rotating_proxies.middlewares.BanDetectionMiddleware": 620,
# }

DOWNLOAD_TIMEOUT = 300
COOKIES_ENABLED = False
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
    499,
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

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
