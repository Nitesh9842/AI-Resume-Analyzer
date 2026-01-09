
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BotConfig:
    """Configuration class for the trading bot."""
    
    # API Credentials - Set these via environment variables or directly
    api_key: str = ""
    api_secret: str = ""
    
    # Testnet Configuration
    testnet: bool = True
    testnet_base_url: str = "https://testnet.binancefuture.com"
    
    # Trading Parameters
    default_symbol: str = "BTCUSDT"
    default_quantity: float = 0.001
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "trading_bot.log"
    
    @classmethod
    def from_env(cls) -> "BotConfig":
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv("BINANCE_API_KEY", ""),
            api_secret=os.getenv("BINANCE_API_SECRET", ""),
            testnet=os.getenv("BINANCE_TESTNET", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    
    def validate(self) -> bool:
        """Validate that required configuration is set."""
        if not self.api_key or not self.api_secret:
            return False
        return True


# Default configuration instance
DEFAULT_CONFIG = BotConfig()
