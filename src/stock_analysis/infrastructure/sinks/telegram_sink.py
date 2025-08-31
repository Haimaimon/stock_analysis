from ...domain.entities import Signal
from ...domain.ports import AlertSink
from telegram import Bot

class TelegramSink(AlertSink):
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(self.token)

    async def emit(self, signal: Signal) -> None:
        text = (
            f"🔔 {signal.ticker}\n"
            f"{signal.ts:%Y-%m-%d %H:%M:%S %Z}\n"
            f"{signal.reason}"
        )
        # ⬇️ המתודה היא async ולכן חייבים await
        await self.bot.send_message(chat_id=self.chat_id, text=text)
