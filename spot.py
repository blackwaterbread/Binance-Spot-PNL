# Configs
BINANCE_API_KEY = 'YOUR-API-KEY'
BINANCE_API_SECRET = 'YOUR-API-SECRET'
POSITION_SPOT = {
    # Examples
    'BTCUSDT': { # Trading Pair
        'amount': 1.0000, # Crypto Amount
        'avg_price': 10000.00 # Average Price
    },
    'ETHUSDT': { # Trading Pair
        'amount': 20.0000, # Crypto Amount
        'avg_price': 2400.00 # Average Price
    }
}

import asyncio
from binance import AsyncClient, BinanceSocketManager
from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

current = {}

def generate_table() -> Table:
    table = Table(
        header_style="bold cyan",
        show_edge=False,
        show_header=True,
        expand=False,
        row_styles=["none"],
        box=box.SIMPLE
    )

    table.add_column("Symbol", justify="left")
    table.add_column("Size", justify="center", min_width=14)
    table.add_column("Last Price", justify="center", min_width=14)
    table.add_column("Avg. Price", justify="center", min_width=14)
    table.add_column("PNL", justify="center", min_width=24)

    for key, value in current.items():
        sign = '+' if value['pnl'] > 0 else ''
        style_pnl = 'bold green' if sign == '+' else 'bold red'
        table.add_row(
            Text(f"{key}"),
            Text(f"{value['amount']} {value['pair0']}", justify='right'),
            Text(f"{value['last_price']} {value['pair1']}", justify='right'),
            Text(f"{value['avg_price']} {value['pair1']}", justify='right'),
            Text(f"{sign}{value['pnl']} {value['pair1']} ({sign}{value['pnl_percent']} %)", style=style_pnl, justify='right'),
        )

    return table

def parse_stream_response(stream):
    symbol = stream['data']['s']
    pair0 = symbol.replace('USDT', '').replace('BUSD', '')
    pair1 = symbol.replace(pair0, '')
    pos = POSITION_SPOT[symbol]
    amount = pos['amount']
    avg_price = pos['avg_price']
    last_price = float(stream['data']['c'])
    pnl = round((amount * last_price) - (amount * avg_price), 2)
    pnl_percent = round(pnl / (amount * avg_price) * 100, 2)
    return symbol, {
        'amount': amount,
        'last_price': last_price,
        'avg_price': avg_price,
        'pair0': pair0.upper(),
        'pair1': pair1.upper(),
        'pnl': pnl,
        'pnl_percent': pnl_percent,
    }

async def main():
    console = Console()
    client = await AsyncClient.create(BINANCE_API_KEY, BINANCE_API_SECRET)
    socket_manager = BinanceSocketManager(client)
    tickers = list(map(lambda x: f"{x.lower()}@ticker", POSITION_SPOT.keys()))
    stream = socket_manager.multiplex_socket(tickers)
    console.clear()

    async with stream as tscm:
        with Live(generate_table(), console=console, refresh_per_second=1) as live:
            while True:
                received = await tscm.recv()
                symbol, response = parse_stream_response(received)
                current[symbol] = response
                live.update(generate_table())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())