import logging
import os
from datetime import datetime
try:
    from language import get_translation
except ImportError:
    # If language module is not yet imported (circular import prevention)
    def get_translation(key, **kwargs):
        if key == "logger_initialized":
            return "Logger initialized, log directory: {dir}"
        return key

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)



logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log"),
            encoding="utf-8",
        ),
    ],
)

# Set custom formatter for file handlers
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.FileHandler):
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )


# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(message)s"))

# Add the console handler to the logger
logging.getLogger().addHandler(console_handler)

# Print log directory path
logging.info(get_translation("logger_initialized", dir=os.path.abspath(log_dir)))

