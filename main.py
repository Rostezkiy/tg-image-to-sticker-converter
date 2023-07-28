import io
import logging
import time
from PIL import Image, ImageFile
from aiogram import Bot, Dispatcher, types

bot = Bot('token')
dp = Dispatcher(bot)

# Enable parser to avoid potential exploits with malformed images
ImageFile.LOAD_TRUNCATED_IMAGES = True
# Maximum image size in pixels (width, height)
MAX_IMAGE_SIZE = (2048, 2048)
# Dictionary to store the number of requests each user has made in the current minute
request_counts = {}
# Maximum number of requests a user can make in a minute
RATE_LIMIT = 10


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("Hello! To convert an image into a sticker, send me one or more photos!")


@dp.message_handler(content_types=types.ContentType.PHOTO)
async def convert_photo_to_sticker(message: types.Message):
    # Check rate limit
    if rate_limiter(message.from_user.id):
        # Validate file id
        image = await validate_file_id(message.photo[-1].file_id)
        if image:
            try:
                image = Image.open(image)
                # Check size before processing
                if image.size < MAX_IMAGE_SIZE:
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
                    image.save(webp_image_io, 'webp')
                    # Check processed file
                    if validate_file(webp_image_io):
                        webp_image_io.seek(0)
                        await bot.send_sticker(chat_id=message.chat.id, sticker=webp_image_io)
            except Exception as e:
                logging.error("Error processing image: " + str(e))
                await bot.send_message(chat_id=message.chat.id,
                                       text='Error processing image. Try again or another file.')
        else:
            logging.error("Invalid file id")
            await bot.send_message(chat_id=message.chat.id, text='Invalid file id. Try again.')

    else:
        logging.error("Rate limit exceeded for user: " + str(message.from_user.id))
        await bot.send_message(chat_id=message.chat.id,
                               text='Rate limit exceeded. Try again later. \nLimit = 10 images per minute.')


async def validate_file_id(file_id):
    try:
        image = await bot.download_file_by_id(file_id)
        return image
    except Exception as e:
        logging.error("Invalid file id: " + str(e))
        return False


def validate_file(file):
    # Check if file is in the correct format (WebP)
    try:
        image = Image.open(file)
        if image.format == 'WEBP':
            return True
        else:
            return False
    except IOError:
        return False


def rate_limiter(user_id):
    global request_counts
    # Get the current minute
    current_minute = time.time() // 60
    # If the user has not made any requests in the current minute, allow the request
    if user_id not in request_counts or request_counts[user_id][0] != current_minute:
        request_counts[user_id] = [current_minute, 1]
        return True
    # If the user has made less than the maximum number of requests in the current minute, allow the request
    elif request_counts[user_id][1] < RATE_LIMIT:
        request_counts[user_id][1] += 1
        return True
    # If the user has made the maximum number of requests in the current minute, deny the request
    else:
        return False


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
