import io

from PIL import Image
from aiogram import Bot, Dispatcher, types

bot = Bot('token')
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("Hello! To convert an image into a sticker, send me one or more photos!")


@dp.message_handler(content_types=types.ContentType.PHOTO)
async def convert_photo_to_sticker(message: types.Message):
    photo_bytes_io = await bot.download_file_by_id(message.photo[-1].file_id)
    image = Image.open(photo_bytes_io)
    # Calculate the ratio for resizing while keeping the aspect ratio
    max_size = 512
    width, height = image.size
    if width > height:
        ratio = max_size / float(width)
        new_size = (max_size, int(height * ratio))
    else:
        ratio = max_size / float(height)
        new_size = (int(width * ratio), max_size)
    image = image.resize(new_size, Image.LANCZOS)
    # Convert image to WebP
    webp_image_io = io.BytesIO()
    image.save(webp_image_io, "WebP")
    webp_image_io.seek(0)
    await bot.send_sticker(chat_id=message.chat.id, sticker=webp_image_io)


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
