"""
Logging configuration for Binance Futures Trading Bot.
Provides comprehensive logging for API requests, responses, and errors.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class BotLogger:
    """Custom logger for the trading bot with API request/response logging."""
    
    def __init__(
        self,
        name: str = "TradingBot",
        log_level: str = "INFO",
        log_file: Optional[str] = "trading_bot.log",
        console_output: bool = True
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.logger.handlers = []  # Clear existing handlers
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)
    
    def log_api_request(self, method: str, endpoint: str, params: Optional[dict] = None):
        """Log API request details."""
        params_str = str(params) if params else "None"
        self.info(f"API REQUEST  | {method} {endpoint} | Params: {params_str}")
    
    def log_api_response(self, status: str, response: dict):
        """Log API response details."""
        self.info(f"API RESPONSE | Status: {status} | Response: {response}")
    
    def log_api_error(self, error_code: str, error_message: str):
        """Log API error details."""
        self.error(f"API ERROR    | Code: {error_code} | Message: {error_message}")
    
    def log_order(self, order_type: str, side: str, symbol: str, quantity: float, price: Optional[float] = None):
        """Log order placement details."""
        price_str = f"@ {price}" if price else "@ MARKET"
        self.info(f"ORDER        | {order_type} {side} {quantity} {symbol} {price_str}")
    
    def log_order_result(self, order_id: str, status: str, filled_qty: float, avg_price: float):
        """Log order execution result."""
        self.info(f"ORDER RESULT | ID: {order_id} | Status: {status} | Filled: {filled_qty} @ {avg_price}")


# Create default logger instance
def get_logger(
    name: str = "TradingBot",
    log_level: str = "INFO",
    log_file: str = "trading_bot.log"
) -> BotLogger:
    """Get or create a logger instance."""
    return BotLogger(name=name, log_level=log_level, log_file=log_file)
