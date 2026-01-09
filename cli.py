"""
Command-Line Interface for Binance Futures Trading Bot.
Provides interactive menu-driven interface for trading operations.
"""

import argparse
import sys
import os
from typing import Optional
from getpass import getpass

from bot import BasicBot, OrderSide, OrderType
from config import BotConfig
from logger import get_logger


class TradingCLI:
    """Command-line interface for the trading bot."""
    
    def __init__(self):
        self.bot: Optional[BasicBot] = None
        self.logger = get_logger(name="CLI", log_level="INFO")
        self.running = True
    
    def print_header(self):
        """Print application header."""
        print("\n" + "=" * 60)
        print("   BINANCE FUTURES TRADING BOT - TESTNET")
        print("=" * 60)
        print("   ⚠️  TESTNET MODE - No real funds at risk")
        print("=" * 60 + "\n")
    
    def print_menu(self):
        """Print main menu options."""
        print("\n" + "-" * 40)
        print("MAIN MENU")
        print("-" * 40)
        print("1.  View Account Balance")
        print("2.  View Current Price")
        print("3.  Place Market Order")
        print("4.  Place Limit Order")
        print("5.  Place Stop-Limit Order")
        print("6.  Place Stop-Market Order")
        print("7.  Place Take-Profit Order")
        print("8.  View Open Orders")
        print("9.  Cancel Order")
        print("10. Cancel All Orders")
        print("11. View Positions")
        print("12. Set Leverage")
        print("13. Get Order Status")
        print("0.  Exit")
        print("-" * 40)
    
    def get_input(self, prompt: str, required: bool = True, default: Optional[str] = None) -> str:
        """Get user input with optional default value."""
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        
        while True:
            value = input(prompt).strip()
            
            if not value and default:
                return default
            
            if not value and required:
                print("❌ This field is required. Please enter a value.")
                continue
            
            return value
    
    def get_float_input(self, prompt: str, default: Optional[float] = None) -> float:
        """Get float input from user."""
        while True:
            try:
                if default is not None:
                    value = self.get_input(prompt, default=str(default))
                else:
                    value = self.get_input(prompt)
                return float(value)
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def get_int_input(self, prompt: str, default: Optional[int] = None) -> int:
        """Get integer input from user."""
        while True:
            try:
                if default is not None:
                    value = self.get_input(prompt, default=str(default))
                else:
                    value = self.get_input(prompt)
                return int(value)
            except ValueError:
                print("❌ Please enter a valid integer.")
    
    def get_side_input(self) -> OrderSide:
        """Get order side from user."""
        while True:
            side = self.get_input("Order Side (BUY/SELL)").upper()
            if side == "BUY":
                return OrderSide.BUY
            elif side == "SELL":
                return OrderSide.SELL
            else:
                print("❌ Please enter BUY or SELL.")
    
    def get_yes_no_input(self, prompt: str, default: bool = False) -> bool:
        """Get yes/no input from user."""
        default_str = "Y/n" if default else "y/N"
        while True:
            value = self.get_input(f"{prompt} ({default_str})", required=False)
            if not value:
                return default
            if value.lower() in ["y", "yes"]:
                return True
            if value.lower() in ["n", "no"]:
                return False
            print("❌ Please enter Y or N.")
    
    def display_order_result(self, order: dict):
        """Display order result in formatted way."""
        print("\n" + "=" * 50)
        print("ORDER EXECUTED")
        print("=" * 50)
        print(f"  Order ID:      {order['order_id']}")
        print(f"  Symbol:        {order['symbol']}")
        print(f"  Side:          {order['side']}")
        print(f"  Type:          {order['type']}")
        print(f"  Status:        {order['status']}")
        print(f"  Quantity:      {order['quantity']}")
        print(f"  Executed Qty:  {order['executed_qty']}")
        if order['price']:
            print(f"  Price:         {order['price']}")
        if order['avg_price']:
            print(f"  Avg Price:     {order['avg_price']}")
        if order['stop_price']:
            print(f"  Stop Price:    {order['stop_price']}")
        print("=" * 50)
    
    def display_balance(self, balance: dict):
        """Display balance information."""
        print("\n" + "=" * 40)
        print("ACCOUNT BALANCE")
        print("=" * 40)
        print(f"  Asset:          {balance['asset']}")
        print(f"  Total Balance:  {balance['balance']:.4f}")
        print(f"  Available:      {balance['available']:.4f}")
        print(f"  Cross Wallet:   {balance['cross_wallet']:.4f}")
        print("=" * 40)
    
    def display_positions(self, positions: list):
        """Display positions information."""
        print("\n" + "=" * 60)
        print("CURRENT POSITIONS")
        print("=" * 60)
        
        if not positions:
            print("  No active positions.")
        else:
            for pos in positions:
                print(f"\n  Symbol:          {pos['symbol']}")
                print(f"  Position:        {pos['position_amount']}")
                print(f"  Entry Price:     {pos['entry_price']:.2f}")
                print(f"  Mark Price:      {pos['mark_price']:.2f}")
                print(f"  Unrealized PnL:  {pos['unrealized_pnl']:.4f}")
                print(f"  Liquidation:     {pos['liquidation_price']:.2f}")
                print(f"  Leverage:        {pos['leverage']}x")
                print("-" * 40)
        
        print("=" * 60)
    
    def display_orders(self, orders: list):
        """Display open orders."""
        print("\n" + "=" * 60)
        print("OPEN ORDERS")
        print("=" * 60)
        
        if not orders:
            print("  No open orders.")
        else:
            for order in orders:
                print(f"\n  Order ID:    {order['order_id']}")
                print(f"  Symbol:      {order['symbol']}")
                print(f"  Side:        {order['side']}")
                print(f"  Type:        {order['type']}")
                print(f"  Status:      {order['status']}")
                print(f"  Quantity:    {order['quantity']}")
                print(f"  Price:       {order['price']}")
                if order['stop_price']:
                    print(f"  Stop Price:  {order['stop_price']}")
                print("-" * 40)
        
        print("=" * 60)
    
    def initialize_bot(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize the trading bot with API credentials."""
        # Try to get credentials from arguments, environment, or user input
        if not api_key:
            api_key = os.getenv("BINANCE_API_KEY")
        if not api_secret:
            api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not api_key:
            print("\nPlease enter your Binance Testnet API credentials:")
            print("(Get them from: https://testnet.binancefuture.com)")
            api_key = self.get_input("API Key")
        
        if not api_secret:
            api_secret = getpass("API Secret: ")
        
        try:
            print("\n⏳ Connecting to Binance Futures Testnet...")
            self.bot = BasicBot(
                api_key=api_key,
                api_secret=api_secret,
                testnet=True
            )
            print("✅ Connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def handle_view_balance(self):
        """Handle view balance action."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        asset = self.get_input("Asset", default="USDT")
        try:
            balance = self.bot.get_balance(asset)
            self.display_balance(balance)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def handle_view_price(self):
        """Handle view price action."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        symbol = self.get_input("Symbol", default="BTCUSDT").upper()
        try:
            price = self.bot.get_current_price(symbol)
            print(f"\n💰 Current {symbol} Price: {price}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def handle_market_order(self):
        """Handle market order placement."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        print("\n--- MARKET ORDER ---")
        symbol = self.get_input("Symbol", default="BTCUSDT").upper()
        side = self.get_side_input()
        quantity = self.get_float_input("Quantity")
        reduce_only = self.get_yes_no_input("Reduce Only?", default=False)
        
        # Confirm order
        print(f"\n📋 Order Summary: {side.value} {quantity} {symbol} @ MARKET")
        if not self.get_yes_no_input("Confirm order?"):
            print("❌ Order cancelled.")
            return
        
        try:
            order = self.bot.place_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                reduce_only=reduce_only
            )
            self.display_order_result(order)
        except Exception as e:
            print(f"❌ Order failed: {e}")
    
    def handle_limit_order(self):
        """Handle limit order placement."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        print("\n--- LIMIT ORDER ---")
        symbol = self.get_input("Symbol", default="BTCUSDT").upper()
        
        # Show current price for reference
        try:
            current_price = self.bot.get_current_price(symbol)
            print(f"📊 Current {symbol} price: {current_price}")
        except:
            pass
        
        side = self.get_side_input()
        quantity = self.get_float_input("Quantity")
        price = self.get_float_input("Limit Price")
        tif = self.get_input("Time in Force (GTC/IOC/FOK)", default="GTC").upper()
        reduce_only = self.get_yes_no_input("Reduce Only?", default=False)
        
        # Confirm order
        print(f"\n📋 Order Summary: {side.value} {quantity} {symbol} @ {price}")
        if not self.get_yes_no_input("Confirm order?"):
            print("❌ Order cancelled.")
            return
        
        try:
            order = self.bot.place_limit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                time_in_force=tif,
                reduce_only=reduce_only
            )
            self.display_order_result(order)
        except Exception as e:
            print(f"❌ Order failed: {e}")
    
    def handle_stop_limit_order(self):
        """Handle stop-limit order placement."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        print("\n--- STOP-LIMIT ORDER ---")
        symbol = self.get_input("Symbol", default="BTCUSDT").upper()
        
        try:
            current_price = self.bot.get_current_price(symbol)
            print(f"📊 Current {symbol} price: {current_price}")
        except:
            pass
        
        side = self.get_side_input()
        quantity = self.get_float_input("Quantity")
        stop_price = self.get_float_input("Stop Price (trigger)")
        price = self.get_float_input("Limit Price (execution)")
        reduce_only = self.get_yes_no_input("Reduce Only?", default=False)
        
        print(f"\n📋 Order Summary: {side.value} {quantity} {symbol}")
        print(f"    Stop @ {stop_price} → Limit @ {price}")
        if not self.get_yes_no_input("Confirm order?"):
            print("❌ Order cancelled.")
            return
        
        try:
            order = self.bot.place_stop_limit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                reduce_only=reduce_only
            )
            self.display_order_result(order)
        except Exception as e:
            print(f"❌ Order failed: {e}")
    
    def handle_stop_market_order(self):
        """Handle stop-market order placement."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        print("\n--- STOP-MARKET ORDER ---")
        symbol = self.get_input("Symbol", default="BTCUSDT").upper()
        
        try:
            current_price = self.bot.get_current_price(symbol)
            print(f"📊 Current {symbol} price: {current_price}")
        except:
            pass
        
        side = self.get_side_input()
        quantity = self.get_float_input("Quantity")
        stop_price = self.get_float_input("Stop Price (trigger)")
        reduce_only = self.get_yes_no_input("Reduce Only?", default=False)
        
        print(f"\n📋 Order Summary: {side.value} {quantity} {symbol}")
        print(f"    Stop @ {stop_price} → MARKET")
        if not self.get_yes_no_input("Confirm order?"):
            print("❌ Order cancelled.")
            return
        
        try:
            order = self.bot.place_stop_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                stop_price=stop_price,
                reduce_only=reduce_only
            )
            self.display_order_result(order)
        except Exception as e:
            print(f"❌ Order failed: {e}")
    
    def handle_take_profit_order(self):
        """Handle take-profit order placement."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        print("\n--- TAKE-PROFIT ORDER ---")
        symbol = self.get_input("Symbol", default="BTCUSDT").upper()
        
        try:
            current_price = self.bot.get_current_price(symbol)
            print(f"📊 Current {symbol} price: {current_price}")
        except:
            pass
        
        side = self.get_side_input()
        quantity = self.get_float_input("Quantity")
        stop_price = self.get_float_input("Take Profit Price (trigger)")
        
        use_limit = self.get_yes_no_input("Use limit price?", default=False)
        price = None
        if use_limit:
            price = self.get_float_input("Limit Price (execution)")
        
        print(f"\n📋 Order Summary: {side.value} {quantity} {symbol}")
        print(f"    TP @ {stop_price}" + (f" → Limit @ {price}" if price else " → MARKET"))
        if not self.get_yes_no_input("Confirm order?"):
            print("❌ Order cancelled.")
            return
        
        try:
            order = self.bot.place_take_profit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                stop_price=stop_price,
                price=price
            )
            self.display_order_result(order)
        except Exception as e:
            print(f"❌ Order failed: {e}")
    
    def handle_view_orders(self):
        """Handle view open orders action."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        symbol = self.get_input("Symbol (leave empty for all)", required=False)
        symbol = symbol.upper() if symbol else None
        
        try:
            orders = self.bot.get_open_orders(symbol)
            self.display_orders(orders)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def handle_cancel_order(self):
        """Handle cancel order action."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        symbol = self.get_input("Symbol").upper()
        order_id = self.get_int_input("Order ID")
        
        if not self.get_yes_no_input(f"Cancel order {order_id}?"):
            print("❌ Cancellation aborted.")
            return
        
        try:
            self.bot.cancel_order(symbol, order_id)
            print(f"✅ Order {order_id} cancelled successfully.")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def handle_cancel_all_orders(self):
        """Handle cancel all orders action."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        symbol = self.get_input("Symbol").upper()
        
        if not self.get_yes_no_input(f"Cancel ALL orders for {symbol}?"):
            print("❌ Cancellation aborted.")
            return
        
        try:
            self.bot.cancel_all_orders(symbol)
            print(f"✅ All orders for {symbol} cancelled.")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def handle_view_positions(self):
        """Handle view positions action."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        symbol = self.get_input("Symbol (leave empty for all)", required=False)
        symbol = symbol.upper() if symbol else None
        
        try:
            positions = self.bot.get_positions(symbol)
            self.display_positions(positions)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def handle_set_leverage(self):
        """Handle set leverage action."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        symbol = self.get_input("Symbol", default="BTCUSDT").upper()
        leverage = self.get_int_input("Leverage (1-125)", default=10)
        
        try:
            result = self.bot.set_leverage(symbol, leverage)
            print(f"✅ Leverage for {symbol} set to {leverage}x")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def handle_get_order_status(self):
        """Handle get order status action."""
        if self.bot is None:
            print("❌ Bot not initialized.")
            return
        symbol = self.get_input("Symbol").upper()
        order_id = self.get_int_input("Order ID")
        
        try:
            order = self.bot.get_order_status(symbol, order_id)
            self.display_order_result(order)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def run(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Run the CLI main loop."""
        self.print_header()
        
        if not self.initialize_bot(api_key, api_secret):
            print("\n⚠️  Failed to initialize bot. Exiting...")
            sys.exit(1)
        
        while self.running:
            try:
                self.print_menu()
                choice = self.get_input("Select option", default="0")
                
                if choice == "0":
                    print("\n👋 Goodbye!")
                    self.running = False
                elif choice == "1":
                    self.handle_view_balance()
                elif choice == "2":
                    self.handle_view_price()
                elif choice == "3":
                    self.handle_market_order()
                elif choice == "4":
                    self.handle_limit_order()
                elif choice == "5":
                    self.handle_stop_limit_order()
                elif choice == "6":
                    self.handle_stop_market_order()
                elif choice == "7":
                    self.handle_take_profit_order()
                elif choice == "8":
                    self.handle_view_orders()
                elif choice == "9":
                    self.handle_cancel_order()
                elif choice == "10":
                    self.handle_cancel_all_orders()
                elif choice == "11":
                    self.handle_view_positions()
                elif choice == "12":
                    self.handle_set_leverage()
                elif choice == "13":
                    self.handle_get_order_status()
                else:
                    print("❌ Invalid option. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                self.running = False
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                self.logger.error(f"Unexpected error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Binance Futures Trading Bot - Testnet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py                           # Interactive mode
  python cli.py --api-key KEY --api-secret SECRET
  
Environment Variables:
  BINANCE_API_KEY      Your Binance Testnet API key
  BINANCE_API_SECRET   Your Binance Testnet API secret

Get testnet credentials at: https://testnet.binancefuture.com
        """
    )
    
    parser.add_argument(
        "--api-key",
        help="Binance API key (or set BINANCE_API_KEY env var)"
    )
    parser.add_argument(
        "--api-secret",
        help="Binance API secret (or set BINANCE_API_SECRET env var)"
    )
    
    args = parser.parse_args()
    
    cli = TradingCLI()
    cli.run(api_key=args.api_key, api_secret=args.api_secret)


if __name__ == "__main__":
    main()
