import logging


# Custom colouring for log printing when running locally
class CustomFormatter(logging.Formatter):
    yellow = "\x1b[33;20m"
    green = "\033[92m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    style = "\n%(name)s | %(asctime)s | %(levelname)s: %(message)s"

    FORMATS = {
        logging.INFO: green + style + reset,
        logging.ERROR: red + style + reset,
        logging.WARNING: yellow + style + reset,
        logging.CRITICAL: bold_red + style + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class TotalLog:
    data = []

    @classmethod
    def add(cls, item):
        cls.data.append(item)
