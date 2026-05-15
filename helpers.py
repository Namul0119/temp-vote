import random
import string
import qrcode
import base64

from io import BytesIO


def get_clothes_weight(clothes):

    if clothes == "thin":
        return 1.2

    elif clothes == "thick":
        return 0.8

    return 1.0


def get_activity_weight(activity):

    if activity == "move":
        return 1.2

    return 1.0


def get_position_weight(position):

    if position == "ac":
        return 1.3

    elif position == "window":
        return 1.1

    return 1.0


def make_room_code():

    return ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )


def generate_qr_code(url):

    qr = qrcode.make(url)

    buffer = BytesIO()

    qr.save(buffer, format="PNG")

    img_str = base64.b64encode(
        buffer.getvalue()
    ).decode()

    return img_str