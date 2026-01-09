"""
Binance Futures Trading Bot - Main Bot Class
Supports Market, Limit, Stop-Limit, and OCO orders on Binance Futures Testnet (USDT-M).
"""

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from decimal import Decimal, ROUND_DOWN
import time

from config import BotConfig
from logger import BotLogger, get_logger


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    STOP_LIMIT = "STOP"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT"


class PositionSide(Enum):
    """Position side for hedge mode."""
    BOTH = "BOTH"
    LONG = "LONG"
    SHORT = "SHORT"


class BasicBot:
    """
    Basic Trading Bot for Binance Futures Testnet.
    
    Supports:
    - Market orders
    - Limit orders
    - Stop-Limit orders
    - Take-Profit orders
    - Position management
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True,
        config: Optional[BotConfig] = None,
        logger: Optional[BotLogger] = None
    ):
        """
        Initialize the trading bot.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet (default: True)
            config: Optional BotConfig instance
            logger: Optional BotLogger instance
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.config = config or BotConfig()
        self.logger = logger or get_logger()
        
        # Initialize Binance client
        self.client = self._initialize_client()
        
        # Cache for symbol info
        self._symbol_info_cache: Dict[str, Dict] = {}
        
        self.logger.info(f"Trading Bot initialized - Testnet: {testnet}")
    
    def _initialize_client(self) -> Client:
        """Initialize and configure the Binance client."""
        try:
            client = Client(self.api_key, self.api_secret)
            
            if self.testnet:
                # Set testnet URLs for futures
                client.FUTURES_URL = "https://testnet.binancefuture.com/fapi"
                self.logger.info("Connected to Binance Futures Testnet")
            
            self.logger.log_api_request("GET", "/fapi/v1/ping")
            client.futures_ping()
            self.logger.log_api_response("SUCCESS", {"status": "connected"})
            
            return client
            
        except Exception as e:
            self.logger.log_api_error("CONNECTION", str(e))
            raise ConnectionError(f"Failed to connect to Binance: {e}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get futures account information."""
        try:
            self.logger.log_api_request("GET", "/fapi/v2/account")
            account = self.client.futures_account()
            self.logger.log_api_response("SUCCESS", {"totalWalletBalance": account.get("totalWalletBalance")})
            return account
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def get_balance(self, asset: str = "USDT") -> Dict[str, Any]:
        """
        Get balance for a specific asset.
        
        Args:
            asset: Asset symbol (default: USDT)
            
        Returns:
            Dictionary with balance information
        """
        try:
            self.logger.log_api_request("GET", "/fapi/v2/balance")
            balances = self.client.futures_account_balance()
            
            for balance in balances:
                if balance["asset"] == asset:
                    result = {
                        "asset": asset,
                        "balance": float(balance["balance"]),
                        "available": float(balance["availableBalance"]),
                        "cross_wallet": float(balance.get("crossWalletBalance", 0))
                    }
                    self.logger.log_api_response("SUCCESS", result)
                    return result
            
            return {"asset": asset, "balance": 0.0, "available": 0.0, "cross_wallet": 0.0}
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get trading rules and filters for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            
        Returns:
            Symbol information dictionary
        """
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        
        try:
            self.logger.log_api_request("GET", "/fapi/v1/exchangeInfo")
            exchange_info = self.client.futures_exchange_info()
            
            for s in exchange_info["symbols"]:
                if s["symbol"] == symbol:
                    self._symbol_info_cache[symbol] = s
                    return s
            
            raise ValueError(f"Symbol {symbol} not found")
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Current price as float
        """
        try:
            self.logger.log_api_request("GET", f"/fapi/v1/ticker/price?symbol={symbol}")
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])
            self.logger.log_api_response("SUCCESS", {"symbol": symbol, "price": price})
            return price
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def _validate_quantity(self, symbol: str, quantity: float) -> Tuple[bool, str, float]:
        """
        Validate and adjust quantity based on symbol filters.
        
        Args:
            symbol: Trading pair symbol
            quantity: Desired quantity
            
        Returns:
            Tuple of (is_valid, message, adjusted_quantity)
        """
        try:
            symbol_info = self.get_symbol_info(symbol)
            
            for filter_item in symbol_info["filters"]:
                if filter_item["filterType"] == "LOT_SIZE":
                    min_qty = float(filter_item["minQty"])
                    max_qty = float(filter_item["maxQty"])
                    step_size = float(filter_item["stepSize"])
                    
                    if quantity < min_qty:
                        return False, f"Quantity {quantity} below minimum {min_qty}", quantity
                    
                    if quantity > max_qty:
                        return False, f"Quantity {quantity} above maximum {max_qty}", quantity
                    
                    # Adjust to step size
                    precision = len(str(step_size).rstrip('0').split('.')[-1]) if '.' in str(step_size) else 0
                    adjusted_qty = float(Decimal(str(quantity)).quantize(
                        Decimal(str(step_size)), rounding=ROUND_DOWN
                    ))
                    
                    return True, "Valid", adjusted_qty
            
            return True, "No LOT_SIZE filter found", quantity
            
        except Exception as e:
            self.logger.warning(f"Could not validate quantity: {e}")
            return True, "Validation skipped", quantity
    
    def _validate_price(self, symbol: str, price: float) -> Tuple[bool, str, float]:
        """
        Validate and adjust price based on symbol filters.
        
        Args:
            symbol: Trading pair symbol
            price: Desired price
            
        Returns:
            Tuple of (is_valid, message, adjusted_price)
        """
        try:
            symbol_info = self.get_symbol_info(symbol)
            
            for filter_item in symbol_info["filters"]:
                if filter_item["filterType"] == "PRICE_FILTER":
                    min_price = float(filter_item["minPrice"])
                    max_price = float(filter_item["maxPrice"])
                    tick_size = float(filter_item["tickSize"])
                    
                    if price < min_price:
                        return False, f"Price {price} below minimum {min_price}", price
                    
                    if max_price > 0 and price > max_price:
                        return False, f"Price {price} above maximum {max_price}", price
                    
                    # Adjust to tick size
                    precision = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0
                    adjusted_price = float(Decimal(str(price)).quantize(
                        Decimal(str(tick_size)), rounding=ROUND_DOWN
                    ))
                    
                    return True, "Valid", adjusted_price
            
            return True, "No PRICE_FILTER found", price
            
        except Exception as e:
            self.logger.warning(f"Could not validate price: {e}")
            return True, "Validation skipped", price
    
    def place_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            quantity: Order quantity
            reduce_only: Whether this is a reduce-only order
            
        Returns:
            Order result dictionary
        """
        # Validate quantity
        is_valid, msg, adjusted_qty = self._validate_quantity(symbol, quantity)
        if not is_valid:
            self.logger.error(f"Invalid quantity: {msg}")
            raise ValueError(msg)
        
        self.logger.log_order("MARKET", side.value, symbol, adjusted_qty)
        
        try:
            self.logger.log_api_request("POST", "/fapi/v1/order", {
                "symbol": symbol,
                "side": side.value,
                "type": "MARKET",
                "quantity": adjusted_qty,
                "reduceOnly": reduce_only
            })
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.value,
                type="MARKET",
                quantity=adjusted_qty,
                reduceOnly=reduce_only
            )
            
            self.logger.log_order_result(
                order_id=str(order["orderId"]),
                status=order["status"],
                filled_qty=float(order.get("executedQty", 0)),
                avg_price=float(order.get("avgPrice", 0))
            )
            
            return self._format_order_response(order)
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
        except BinanceOrderException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def place_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY or SELL)
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force (GTC, IOC, FOK)
            reduce_only: Whether this is a reduce-only order
            
        Returns:
            Order result dictionary
        """
        # Validate quantity and price
        is_valid, msg, adjusted_qty = self._validate_quantity(symbol, quantity)
        if not is_valid:
            self.logger.error(f"Invalid quantity: {msg}")
            raise ValueError(msg)
        
        is_valid, msg, adjusted_price = self._validate_price(symbol, price)
        if not is_valid:
            self.logger.error(f"Invalid price: {msg}")
            raise ValueError(msg)
        
        self.logger.log_order("LIMIT", side.value, symbol, adjusted_qty, adjusted_price)
        
        try:
            self.logger.log_api_request("POST", "/fapi/v1/order", {
                "symbol": symbol,
                "side": side.value,
                "type": "LIMIT",
                "quantity": adjusted_qty,
                "price": adjusted_price,
                "timeInForce": time_in_force,
                "reduceOnly": reduce_only
            })
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.value,
                type="LIMIT",
                quantity=adjusted_qty,
                price=adjusted_price,
                timeInForce=time_in_force,
                reduceOnly=reduce_only
            )
            
            self.logger.log_order_result(
                order_id=str(order["orderId"]),
                status=order["status"],
                filled_qty=float(order.get("executedQty", 0)),
                avg_price=float(order.get("avgPrice", 0))
            )
            
            return self._format_order_response(order)
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
        except BinanceOrderException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def place_stop_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        stop_price: float,
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        Place a stop-limit order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY or SELL)
            quantity: Order quantity
            price: Limit price (execution price after stop triggers)
            stop_price: Stop trigger price
            time_in_force: Time in force
            reduce_only: Whether this is a reduce-only order
            
        Returns:
            Order result dictionary
        """
        # Validate inputs
        is_valid, msg, adjusted_qty = self._validate_quantity(symbol, quantity)
        if not is_valid:
            raise ValueError(msg)
        
        is_valid, msg, adjusted_price = self._validate_price(symbol, price)
        if not is_valid:
            raise ValueError(msg)
        
        is_valid, msg, adjusted_stop = self._validate_price(symbol, stop_price)
        if not is_valid:
            raise ValueError(msg)
        
        self.logger.log_order("STOP_LIMIT", side.value, symbol, adjusted_qty, adjusted_price)
        self.logger.info(f"Stop Price: {adjusted_stop}")
        
        try:
            self.logger.log_api_request("POST", "/fapi/v1/order", {
                "symbol": symbol,
                "side": side.value,
                "type": "STOP",
                "quantity": adjusted_qty,
                "price": adjusted_price,
                "stopPrice": adjusted_stop,
                "timeInForce": time_in_force,
                "reduceOnly": reduce_only
            })
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.value,
                type="STOP",
                quantity=adjusted_qty,
                price=adjusted_price,
                stopPrice=adjusted_stop,
                timeInForce=time_in_force,
                reduceOnly=reduce_only
            )
            
            self.logger.log_order_result(
                order_id=str(order["orderId"]),
                status=order["status"],
                filled_qty=float(order.get("executedQty", 0)),
                avg_price=float(order.get("avgPrice", 0))
            )
            
            return self._format_order_response(order)
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def place_stop_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        stop_price: float,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        Place a stop-market order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side
            quantity: Order quantity
            stop_price: Stop trigger price
            reduce_only: Whether this is a reduce-only order
            
        Returns:
            Order result dictionary
        """
        is_valid, msg, adjusted_qty = self._validate_quantity(symbol, quantity)
        if not is_valid:
            raise ValueError(msg)
        
        is_valid, msg, adjusted_stop = self._validate_price(symbol, stop_price)
        if not is_valid:
            raise ValueError(msg)
        
        self.logger.log_order("STOP_MARKET", side.value, symbol, adjusted_qty)
        self.logger.info(f"Stop Price: {adjusted_stop}")
        
        try:
            self.logger.log_api_request("POST", "/fapi/v1/order", {
                "symbol": symbol,
                "side": side.value,
                "type": "STOP_MARKET",
                "quantity": adjusted_qty,
                "stopPrice": adjusted_stop,
                "reduceOnly": reduce_only
            })
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.value,
                type="STOP_MARKET",
                quantity=adjusted_qty,
                stopPrice=adjusted_stop,
                reduceOnly=reduce_only
            )
            
            self.logger.log_order_result(
                order_id=str(order["orderId"]),
                status=order["status"],
                filled_qty=float(order.get("executedQty", 0)),
                avg_price=float(order.get("avgPrice", 0))
            )
            
            return self._format_order_response(order)
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def place_take_profit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        stop_price: float,
        price: Optional[float] = None,
        reduce_only: bool = True
    ) -> Dict[str, Any]:
        """
        Place a take-profit order (market or limit).
        
        Args:
            symbol: Trading pair symbol
            side: Order side
            quantity: Order quantity
            stop_price: Take-profit trigger price
            price: Limit price (if None, uses market order)
            reduce_only: Whether this is a reduce-only order
            
        Returns:
            Order result dictionary
        """
        is_valid, msg, adjusted_qty = self._validate_quantity(symbol, quantity)
        if not is_valid:
            raise ValueError(msg)
        
        is_valid, msg, adjusted_stop = self._validate_price(symbol, stop_price)
        if not is_valid:
            raise ValueError(msg)
        
        order_type = "TAKE_PROFIT_MARKET"
        params = {
            "symbol": symbol,
            "side": side.value,
            "type": order_type,
            "quantity": adjusted_qty,
            "stopPrice": adjusted_stop,
            "reduceOnly": reduce_only
        }
        
        if price:
            order_type = "TAKE_PROFIT"
            is_valid, msg, adjusted_price = self._validate_price(symbol, price)
            if not is_valid:
                raise ValueError(msg)
            params["type"] = order_type
            params["price"] = adjusted_price
            params["timeInForce"] = "GTC"
        
        self.logger.log_order(order_type, side.value, symbol, adjusted_qty, price)
        self.logger.info(f"Take Profit Price: {adjusted_stop}")
        
        try:
            self.logger.log_api_request("POST", "/fapi/v1/order", params)
            
            order = self.client.futures_create_order(**params)
            
            self.logger.log_order_result(
                order_id=str(order["orderId"]),
                status=order["status"],
                filled_qty=float(order.get("executedQty", 0)),
                avg_price=float(order.get("avgPrice", 0))
            )
            
            return self._format_order_response(order)
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an open order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to cancel
            
        Returns:
            Cancellation result
        """
        try:
            self.logger.log_api_request("DELETE", f"/fapi/v1/order", {
                "symbol": symbol,
                "orderId": order_id
            })
            
            result = self.client.futures_cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            
            self.logger.info(f"Order {order_id} cancelled successfully")
            return result
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """
        Cancel all open orders for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Cancellation result
        """
        try:
            self.logger.log_api_request("DELETE", "/fapi/v1/allOpenOrders", {"symbol": symbol})
            
            result = self.client.futures_cancel_all_open_orders(symbol=symbol)
            
            self.logger.info(f"All orders for {symbol} cancelled")
            return result
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open orders
        """
        try:
            params = {"symbol": symbol} if symbol else {}
            self.logger.log_api_request("GET", "/fapi/v1/openOrders", params)
            
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol)
            else:
                orders = self.client.futures_get_open_orders()
            
            self.logger.info(f"Retrieved {len(orders)} open orders")
            return [self._format_order_response(o) for o in orders]
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Get status of a specific order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Order status dictionary
        """
        try:
            self.logger.log_api_request("GET", "/fapi/v1/order", {
                "symbol": symbol,
                "orderId": order_id
            })
            
            order = self.client.futures_get_order(symbol=symbol, orderId=order_id)
            
            return self._format_order_response(order)
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of positions
        """
        try:
            self.logger.log_api_request("GET", "/fapi/v2/positionRisk")
            
            positions = self.client.futures_position_information()
            
            if symbol:
                positions = [p for p in positions if p["symbol"] == symbol]
            
            # Filter to only positions with non-zero quantity
            active_positions = []
            for pos in positions:
                if float(pos["positionAmt"]) != 0:
                    active_positions.append({
                        "symbol": pos["symbol"],
                        "position_amount": float(pos["positionAmt"]),
                        "entry_price": float(pos["entryPrice"]),
                        "mark_price": float(pos["markPrice"]),
                        "unrealized_pnl": float(pos["unRealizedProfit"]),
                        "liquidation_price": float(pos["liquidationPrice"]),
                        "leverage": int(pos["leverage"]),
                        "margin_type": pos["marginType"],
                        "position_side": pos["positionSide"]
                    })
            
            self.logger.info(f"Retrieved {len(active_positions)} active positions")
            return active_positions
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Set leverage for a symbol.
        
        Args:
            symbol: Trading pair symbol
            leverage: Leverage value (1-125)
            
        Returns:
            Result dictionary
        """
        if leverage < 1 or leverage > 125:
            raise ValueError("Leverage must be between 1 and 125")
        
        try:
            self.logger.log_api_request("POST", "/fapi/v1/leverage", {
                "symbol": symbol,
                "leverage": leverage
            })
            
            result = self.client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            
            self.logger.info(f"Leverage for {symbol} set to {leverage}x")
            return result
            
        except BinanceAPIException as e:
            self.logger.log_api_error(str(e.code), e.message)
            raise
    
    def _format_order_response(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Format order response for consistent output."""
        return {
            "order_id": order.get("orderId"),
            "client_order_id": order.get("clientOrderId"),
            "symbol": order.get("symbol"),
            "side": order.get("side"),
            "type": order.get("type"),
            "status": order.get("status"),
            "price": float(order.get("price", 0)),
            "quantity": float(order.get("origQty", 0)),
            "executed_qty": float(order.get("executedQty", 0)),
            "avg_price": float(order.get("avgPrice", 0)),
            "stop_price": float(order.get("stopPrice", 0)) if order.get("stopPrice") else None,
            "time_in_force": order.get("timeInForce"),
            "reduce_only": order.get("reduceOnly", False),
            "close_position": order.get("closePosition", False),
            "working_type": order.get("workingType"),
            "update_time": order.get("updateTime")
        }
