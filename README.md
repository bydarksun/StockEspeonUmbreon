# Pokémon 30th Anniversary stock monitor (starter)

This starter monitor sends Telegram messages when it detects a stock status change.
It does NOT automatically discover every shop yet; add product-page URLs to `config.json`.
Website text detection can produce false positives/negatives and may not work on JavaScript-rendered or protected pages.

## Setup
1. Create a Telegram bot via `@BotFather` and copy its token privately.
2. Start a chat with your new bot and press Start.
3. Get your Telegram chat ID using a trusted method (for example, `getUpdates` after messaging your bot).
4. Copy `config.example.json` to `config.json` and add store/product URLs.
5. Install Python 3.10+ and dependencies:
   `pip install -r requirements.txt`
6. Set environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
7. Run:
   `python monitor.py`

Keep the bot token secret; never paste it into public repositories or chats.

## Target stores & bilingual product discovery

The initial target store list is Carrefour España, El Corte Inglés, ToyPlanet, Fnac España, Juguettos, and GAME España. `store_catalog.json` contains Spanish and English product search phrases. The monitor checks individual product-page URLs entered into `config.json`; it does not perform automated search/discovery yet.
