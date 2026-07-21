"""Constants for Thermal Vision integration."""

DOMAIN = "thermal_vision"

VERSION = "v3.1.8"
ISSUE_URL = "https://github.com/TheRealWaldo/thermal/issues"

CONF_WIDTH = "width"
CONF_HEIGHT = "height"
CONF_PRESERVE_ASPECT_RATIO = "preserve_aspect_ratio"
CONF_PIXEL_SENSOR = "pixel_sensor"
CONF_MIN_DIFFERANCE = "min_diff"
CONF_MIN_TEMPERATURE = "min_temp"
CONF_MAX_TEMPERATURE = "max_temp"
CONF_METHOD = "method"
CONF_AUTO_RANGE = "auto_range"
CONF_ROI = "roi"
CONF_TOP = "top"
CONF_LEFT = "left"
CONF_RIGHT = "right"
CONF_BOTTOM = "bottom"
CONF_STATE = "state"
CONF_SENSOR = "sensor"
CONF_ROWS = "rows"
CONF_COLS = "cols"
CONF_ROTATE = "rotate"
CONF_MIRROR = "mirror"
CONF_FORMAT = "format"
CONF_INTERPOLATE = "interpolate"
CONF_COLD_COLOR = "cold_color"
CONF_HOT_COLOR = "hot_color"
CONF_SESSION_TIMEOUT = "session_timeout"
CONF_OVERLAY = "overlay"

ATTR_MIN_INDEX = "min_index"
ATTR_MAX_INDEX = "max_index"
ATTR_MIN = "min"
ATTR_MAX = "max"
ATTR_AVG = "average"
ATTR_SENSOR_TEMP = "sensor_temp"
ATTR_PERSON_DETECTED = "person_detected"

DEFAULT_NAME = "Thermal Vision"
DEFAULT_VERIFY_SSL = False
DEFAULT_OVERLAY = False
DEFAULT_IMAGE_WIDTH = 640
DEFAULT_IMAGE_HEIGHT = 640
DEFAULT_PRESERVE_ASPECT_RATIO = True
DEFAULT_MIN_TEMPERATURE = 26.0
DEFAULT_MAX_TEMPERATURE = 32.0
DEFAULT_METHOD = "bicubic"
DEFAULT_STATE = ATTR_AVG
DEFAULT_ROWS = 8
DEFAULT_COLS = 8
DEFAULT_ROTATE = 0
DEFAULT_MIRROR = False
DEFAULT_COLD_COLOR = "indigo"
DEFAULT_HOT_COLOR = "red"
DEFAULT_FORMAT = "jpeg"
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_SESSION_TIMEOUT = 2

SERVICE_AUTO_SCALE = "auto_scale"
