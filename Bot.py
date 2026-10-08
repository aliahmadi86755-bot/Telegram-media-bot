import asyncio
import os
import random

from telegram import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Update,
)
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = os.environ["BOT_TOKEN"]
DELAY = 3

EMOJIS = [
    "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎",
    "💋", "😘",
    "☘️", "🍀", "🌸", "🌼", "🌻", "🌜", "🌛", "🌖", "🔥", "✨", "💦",
]

MEDIA_TYPES = {
    "visual": {"photo": InputMediaPhoto, "video": InputMediaVideo},
    "document": {"document": InputMediaDocument},
    "audio": {"audio": InputMediaAudio},
}

buffers: dict[int, list] = {}


def extract(msg):
    if msg.animation:
        return None
    if msg.photo:
        return "visual", "photo", msg.photo[-1].file_id
    if msg.video:
        return "visual", "video", msg.video.file_id
    if msg.audio:
        return "audio", "audio", msg.audio.file_id
    if msg.document:
        return "document", "document", msg.document.file_id
    return None


async def flush(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(DELAY)
    items = buffers.pop(chat_id, [])
    if not items:
        return

    caption = random.choice(EMOJIS)

    first_group = True
    for group, types in MEDIA_TYPES.items():
        part = [i for i in items if i["group"] == group]
        for start in range(0, len(part), 10):
            chunk = part[start:start + 10]
            cap = caption if first_group else None
            first_group = False
            if len(chunk) == 1:
                await context.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=chat_id,
                    message_id=chunk[0]["message_id"],
                    caption=cap,
                    parse_mode="HTML",
                )
                continue
            media = []
            for n, i in enumerate(chunk):
                media.append(
                    types[i["type"]](
                        i["file_id"],
                        caption=cap if n == 0 else None,
                        parse_mode="HTML",
                    )
                )
            await context.bot.send_media_group(chat_id=chat_id, media=media)


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat_id = msg.chat_id
    if msg.text:
        return

    info = extract(msg)
    if info is None:
        await context.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=chat_id,
            message_id=msg.message_id,
            caption=random.choice(EMOJIS),
        )
        return

    group, mtype, file_id = info
    new_batch = chat_id not in buffers
    buffers.setdefault(chat_id, []).append(
        {
            "group": group,
            "type": mtype,
            "file_id": file_id,
            "caption": msg.caption_html or "",
            "message_id": msg.message_id,
        }
    )
    if new_batch:
        asyncio.create_task(flush(chat_id, context))


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.ALL & ~filters.COMMAND, on_message
        )
    )
    app.run_polling()


if __name__ == "__main__":
    main()
