# Binance Futures Trading Bot - Testnet

A simplified trading bot for Binance Futures Testnet (USDT-M) with support for multiple order types and a command-line interface.

## Features

- ✅ **Market Orders** - Buy/Sell at current market price
- ✅ **Limit Orders** - Buy/Sell at a specific price
- ✅ **Stop-Limit Orders** - Conditional orders with stop trigger and limit price
- ✅ **Stop-Market Orders** - Conditional orders with stop trigger at market price
- ✅ **Take-Profit Orders** - Exit positions at target price
- ✅ **Position Management** - View and manage open positions
- ✅ **Leverage Control** - Set leverage per trading pair
- ✅ **Order Management** - View, cancel individual or all orders
- ✅ **Comprehensive Logging** - All API requests/responses logged to file
- ✅ **Input Validation** - Quantity and price validation based on exchange rules
- ✅ **Interactive CLI** - User-friendly command-line interface

## Prerequisites

- Python 3.8 or higher
- Binance Futures Testnet account

## Getting Testnet Credentials

1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com)
2. Log in with your GitHub account (or register)
3. Navigate to **API Management** in your account settings
4. Generate a new API key pair
5. Save both the **API Key** and **Secret Key**

> ⚠️ **Important**: These are testnet credentials. Never use mainnet credentials with testnet URLs!

## Installation

1. **Clone or download the project**

2. **Create a virtual environment** (recommended):
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Set up credentials** (choose one method):

   **Option A**: Environment variables
   ```powershell
   $env:BINANCE_API_KEY = "your_api_key_here"
   $env:BINANCE_API_SECRET = "your_api_secret_here"
   ```

   **Option B**: Command-line arguments (shown below)

   **Option C**: Enter when prompted (interactive mode)

## Usage

### Interactive Mode (Recommended)

```powershell
python cli.py
```

You'll be prompted to enter credentials if not set via environment variables.

### With Command-Line Arguments

```powershell
python cli.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET
```

### Programmatic Usage

```python
from bot import BasicBot, OrderSide

# Initialize the bot
bot = BasicBot(
    api_key="your_api_key",
    api_secret="your_api_secret",
    testnet=True  # Always use testnet for testing!
)

# Check balance
balance = bot.get_balance("USDT")
print(f"Available: {balance['available']} USDT")

# Get current price
price = bot.get_current_price("BTCUSDT")
print(f"BTC Price: {price}")

# Place a market order
order = bot.place_market_order(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    quantity=0.001
)
print(f"Order ID: {order['order_id']}, Status: {order['status']}")

# Place a limit order
order = bot.place_limit_order(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    quantity=0.001,
    price=40000.0
)

# Place a stop-limit order
order = bot.place_stop_limit_order(
    symbol="BTCUSDT",
    side=OrderSide.SELL,
    quantity=0.001,
    stop_price=38000.0,  # Trigger price
    price=37900.0        # Limit price
)

# View positions
positions = bot.get_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['position_amount']} @ {pos['entry_price']}")

# Cancel an order
bot.cancel_order("BTCUSDT", order_id=12345)
```

## CLI Menu Options

| Option | Action |
|--------|--------|
| 1 | View account balance for any asset |
| 2 | Get current market price for a symbol |
| 3 | Place a market order |
| 4 | Place a limit order |
| 5 | Place a stop-limit order |
| 6 | Place a stop-market order |
| 7 | Place a take-profit order |
| 8 | View all open orders |
| 9 | Cancel a specific order |
| 10 | Cancel all orders for a symbol |
| 11 | View current positions |
| 12 | Set leverage for a symbol |
| 13 | Get status of a specific order |
| 0 | Exit |

## Project Structure

```
cripto app/
├── bot.py           # Main trading bot class
├── cli.py           # Command-line interface
├── config.py        # Configuration management
├── logger.py        # Logging utilities
├── requirements.txt # Python dependencies
├── README.md        # This file
└── trading_bot.log  # Log file (created at runtime)
```

## Order Types Explained

### Market Order
Executes immediately at the best available price.
```python
bot.place_market_order("BTCUSDT", OrderSide.BUY, 0.001)
```

### Limit Order
Only executes at the specified price or better.
```python
bot.place_limit_order("BTCUSDT", OrderSide.BUY, 0.001, price=40000.0)
```

### Stop-Limit Order
Becomes a limit order when stop price is reached.
```python
bot.place_stop_limit_order(
    "BTCUSDT", OrderSide.SELL, 0.001,
    stop_price=38000.0,  # When BTC drops to 38000
    price=37900.0        # Sell limit at 37900
)
```

### Stop-Market Order
Becomes a market order when stop price is reached.
```python
bot.place_stop_market_order(
    "BTCUSDT", OrderSide.SELL, 0.001,
    stop_price=38000.0
)
```

### Take-Profit Order
Used to close positions at a profit target.
```python
bot.place_take_profit_order(
    "BTCUSDT", OrderSide.SELL, 0.001,
    stop_price=50000.0,  # TP trigger
    price=49900.0        # Optional limit price
)
```

## Logging

All API interactions are logged to `trading_bot.log`:
- API requests with parameters
- API responses
- Order placements and results
- Errors and warnings

Example log output:
```
2026-01-09 10:30:15 | INFO     | TradingBot | API REQUEST  | POST /fapi/v1/order | Params: {'symbol': 'BTCUSDT', ...}
2026-01-09 10:30:16 | INFO     | TradingBot | ORDER RESULT | ID: 123456 | Status: NEW | Filled: 0.0 @ 0.0
```

## Error Handling

The bot handles common errors:
- Invalid API credentials
- Network connectivity issues
- Invalid order parameters (quantity/price filters)
- Insufficient balance
- Order rejection by exchange

All errors are logged and displayed to the user with descriptive messages.

## Safety Notes

⚠️ **This bot is configured for TESTNET only!**

- The bot uses testnet URL: `https://testnet.binancefuture.com`
- Testnet funds are not real - safe for testing
- Always verify you're using testnet credentials
- Never expose your API secrets in code

## Extending the Bot

The `BasicBot` class can be extended for automated trading:

```python
from bot import BasicBot, OrderSide

class MyStrategy(BasicBot):
    def run_strategy(self, symbol: str):
        # Your trading logic here
        price = self.get_current_price(symbol)
        
        # Example: Buy if price drops 5% from some reference
        if price < self.reference_price * 0.95:
            self.place_market_order(symbol, OrderSide.BUY, 0.001)
```

## License

MIT License - Use at your own risk.

## Disclaimer

This software is for educational purposes only. Trading cryptocurrencies carries significant risk. Always test thoroughly on testnet before considering any real trading. The authors are not responsible for any financial losses.
