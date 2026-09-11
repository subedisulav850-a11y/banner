# Made with love by Sulav
# Free Fire Banner API - Sulav Info API Integration
# OB54 Prime Level System - Prime 0 to 8
#
# Prime 8:
#   - prime8.png       = Prime 8 badge
#   - prime8frame.png  = Full banner gold/yellow frame
#
# Required assets:
#   prime0.png
#   prime1.png
#   prime2.png
#   prime3.png
#   prime4.png
#   prime5.png
#   prime6.png
#   prime7.png
#   prime8.png
#   prime8frame.png
#   arial_unicode_bold.otf
#   NotoSansCherokee.ttf


import io
import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import httpx
from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont, ImageEnhance


# ============================================================
# ADJUSTMENT SETTINGS
# ============================================================

AVATAR_ZOOM = 1.26
AVATAR_SHIFT_X = 0
AVATAR_SHIFT_Y = 0

BANNER_START_X = 0.25
BANNER_START_Y = 0.29
BANNER_END_X = 0.81
BANNER_END_Y = 0.65

BANNER_COLOR_FACTOR = 1.6
BANNER_BRIGHTNESS_FACTOR = 0.65
BANNER_CONTRAST_FACTOR = 1.8
BANNER_SHARPNESS_FACTOR = 3.0
AVATAR_SHARPNESS_FACTOR = 2.5

STROKE_NAME = 3
STROKE_GUILD = 2
STROKE_LEVEL = 3

TARGET_HEIGHT = 400

# Prime badge size
PRIME_BADGE_SIZE = 120

# Pin size
PIN_SIZE = 120

# ============================================================
# CONFIGURATION
# ============================================================

SULAV_INFO_API = "https://info.sulavcodex.com/Sulav"

# Decoded CDN
CDN_URL = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG"

FONT_FILE = "arial_unicode_bold.otf"
FONT_CHEROKEE = "NotoSansCherokee.ttf"


# ============================================================
# PRIME ASSETS
# ============================================================

PRIME_FILES = {
    0: "prime0.png",
    1: "prime1.png",
    2: "prime2.png",
    3: "prime3.png",
    4: "prime4.png",
    5: "prime5.png",
    6: "prime6.png",
    7: "prime7.png",
    8: "prime8.png",
}


# ============================================================
# HTTP CLIENT
# ============================================================

sulav_client = httpx.AsyncClient(
    headers={
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        )
    },
    timeout=httpx.Timeout(
        15.0,
        connect=10.0
    ),
    follow_redirects=True,
)


# ============================================================
# IMAGE PROCESSING POOL
# ============================================================

sulav_process_pool = ThreadPoolExecutor(
    max_workers=4
)


# ============================================================
# APP LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    yield

    await sulav_client.aclose()
    sulav_process_pool.shutdown(
        wait=True
    )


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Sulav Free Fire Banner API",
    description=(
        "Professional Free Fire player "
        "banner generator with Prime 0-8 support."
    ),
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LOCAL PATH HELPER
# ============================================================

def get_base_dir() -> str:

    return os.path.dirname(
        os.path.abspath(__file__)
    )


# ============================================================
# LOAD LOCAL IMAGE
# ============================================================

def load_local_image(
    filename: str
) -> Optional[Image.Image]:

    base_dir = get_base_dir()

    search_paths = [
        os.path.join(
            base_dir,
            filename
        ),
        os.path.join(
            base_dir,
            "assets",
            filename
        ),
        os.path.join(
            os.getcwd(),
            filename
        ),
        os.path.join(
            os.getcwd(),
            "assets",
            filename
        ),
    ]

    for path in search_paths:

        if not os.path.isfile(path):
            continue

        try:

            with Image.open(path) as image:

                return image.convert(
                    "RGBA"
                )

        except Exception:
            continue

    return None


# ============================================================
# FONT LOADER
# ============================================================

def load_unicode_font(
    size: int,
    font_file: str = FONT_FILE
):

    base_dir = get_base_dir()

    search_paths = [
        os.path.join(
            base_dir,
            font_file
        ),
        os.path.join(
            base_dir,
            "assets",
            font_file
        ),
        os.path.join(
            os.getcwd(),
            font_file
        ),
        os.path.join(
            os.getcwd(),
            "assets",
            font_file
        ),
    ]

    for path in search_paths:

        if not os.path.isfile(path):
            continue

        try:

            return ImageFont.truetype(
                path,
                size
            )

        except Exception:
            continue

    return ImageFont.load_default()


# ============================================================
# FETCH CDN IMAGE
# ============================================================

async def fetch_image_bytes(
    item_id: Optional[Any]
) -> Optional[bytes]:

    if item_id is None:
        return None

    item_id = str(item_id).strip()

    if item_id.lower() in (
        "",
        "0",
        "none",
        "null",
        "false",
    ):
        return None

    # Avoid accidental full URLs
    item_id = item_id.strip("/")

    try:

        response = await sulav_client.get(
            f"{CDN_URL}/{item_id}.png"
        )

        if response.status_code == 200:
            return response.content

    except (
        httpx.HTTPError,
        asyncio.TimeoutError,
    ):
        pass

    return None


# ============================================================
# BYTES -> IMAGE
# ============================================================

def bytes_to_image(
    img_bytes: Optional[bytes]
) -> Image.Image:

    if img_bytes:

        try:

            return Image.open(
                io.BytesIO(img_bytes)
            ).convert("RGBA")

        except Exception:
            pass

    return Image.new(
        "RGBA",
        (100, 100),
        (0, 0, 0, 0)
    )


# ============================================================
# PRIME LEVEL EXTRACTION
# ============================================================

def extract_prime_level(
    data: Dict[str, Any],
    query_prime: Optional[int] = None
) -> int:
    """
    Supports Prime Level 0 through 8.

    Query override:
        ?prime=0
        ?prime=1
        ...
        ?prime=8
    """

    # --------------------------------------------------------
    # Manual query override
    # --------------------------------------------------------

    if query_prime is not None:

        if 0 <= query_prime <= 8:
            return query_prime


    # --------------------------------------------------------
    # Find actual API data
    # --------------------------------------------------------

    if isinstance(
        data.get("data"),
        dict
    ):
        d = data["data"]

    else:
        d = data


    # --------------------------------------------------------
    # Basic info
    # --------------------------------------------------------

    basic_info = d.get(
        "basicInfo",
        {}
    )

    if not isinstance(
        basic_info,
        dict
    ):
        basic_info = {}


    # --------------------------------------------------------
    # Prime info
    # --------------------------------------------------------

    prime_info = (
        d.get("primeInfo")
        or basic_info.get("primeInfo")
        or {}
    )

    if not isinstance(
        prime_info,
        dict
    ):
        prime_info = {}


    # --------------------------------------------------------
    # Possible API fields
    # --------------------------------------------------------

    candidates = [

        prime_info.get(
            "primeLevel"
        ),

        prime_info.get(
            "level"
        ),

        prime_info.get(
            "prime_level"
        ),

        basic_info.get(
            "primeLevel"
        ),

        basic_info.get(
            "prime_level"
        ),

        d.get(
            "primeLevel"
        ),

        d.get(
            "prime_level"
        ),

        d.get(
            "prime"
        ),
    ]


    # --------------------------------------------------------
    # Convert to 0-8
    # --------------------------------------------------------

    for value in candidates:

        if value is None:
            continue

        try:

            level = int(value)

            if 0 <= level <= 8:
                return level

        except (
            ValueError,
            TypeError,
        ):
            continue


    # Default Prime 0
    return 0


# ============================================================
# LOAD PRIME BADGE
# ============================================================

def load_prime_badge(
    prime_level: int
) -> Optional[Image.Image]:

    if not 0 <= prime_level <= 8:
        prime_level = 0

    filename = PRIME_FILES.get(
        prime_level,
        "prime0.png"
    )

    return load_local_image(
        filename
    )


# ============================================================
# APPLY FULL PRIME 8 FRAME
# ============================================================

def apply_prime8_frame(
    final: Image.Image
) -> Image.Image:
    """
    Loads prime8frame.png and applies it as a
    transparent full-banner frame.

    This is the yellow/gold border style shown
    in the supplied reference.
    """

    frame_img = load_local_image(
        "prime8frame.png"
    )

    if frame_img is None:
        return final


    # Make frame same size as complete banner
    frame_img = frame_img.resize(
        final.size,
        Image.LANCZOS
    )


    # Ensure RGBA
    if frame_img.mode != "RGBA":
        frame_img = frame_img.convert(
            "RGBA"
        )


    # Overlay frame
    final.alpha_composite(
        frame_img,
        (0, 0)
    )

    return final


# ============================================================
# TEXT HELPER
# ============================================================

def draw_unicode_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    position,
    normal_font,
    cherokee_font,
    fill="white",
    stroke_width=2,
    stroke_fill="black",
):

    x, y = position

    def is_cherokee(
        character: str
    ) -> bool:

        code = ord(character)

        return (
            0x13A0 <= code <= 0x13FF
            or
            0xAB70 <= code <= 0xABBF
        )

    for character in text:

        font = (
            cherokee_font
            if is_cherokee(character)
            else normal_font
        )

        draw.text(
            (x, y),
            character,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )

        x += draw.textlength(
            character,
            font=font
        )


# ============================================================
# PROCESS BANNER
# ============================================================

def process_banner_image(
    data: Dict[str, Any],
    avatar_bytes: Optional[bytes],
    banner_bytes: Optional[bytes],
    pin_bytes: Optional[bytes],
    prime_level: int = 0,
) -> io.BytesIO:

    # ========================================================
    # LOAD IMAGES
    # ========================================================

    avatar_img = bytes_to_image(
        avatar_bytes
    )

    banner_img = bytes_to_image(
        banner_bytes
    )

    pin_img = bytes_to_image(
        pin_bytes
    )


    # ========================================================
    # PLAYER DATA
    # ========================================================

    level = str(
        data.get("level")
        or "0"
    )

    name = str(
        data.get("name")
        or "Unknown"
    )

    guild = str(
        data.get("guild")
        or ""
    )


    # ========================================================
    # AVATAR
    # ========================================================

    zoom_size = max(
        TARGET_HEIGHT,
        int(
            TARGET_HEIGHT
            * AVATAR_ZOOM
        )
    )

    avatar_img = avatar_img.resize(
        (
            zoom_size,
            zoom_size
        ),
        Image.LANCZOS
    )

    center = zoom_size // 2
    half = TARGET_HEIGHT // 2

    left = (
        center
        - half
        - AVATAR_SHIFT_X
    )

    top = (
        center
        - half
        - AVATAR_SHIFT_Y
    )

    right = (
        center
        + half
        - AVATAR_SHIFT_X
    )

    bottom = (
        center
        + half
        - AVATAR_SHIFT_Y
    )

    avatar_img = avatar_img.crop(
        (
            left,
            top,
            right,
            bottom
        )
    )

    avatar_img = ImageEnhance.Sharpness(
        avatar_img
    ).enhance(
        AVATAR_SHARPNESS_FACTOR
    )


    # ========================================================
    # BANNER
    # ========================================================

    # If banner is unavailable, use a transparent fallback
    if banner_bytes is None:

        banner_img = Image.new(
            "RGBA",
            (
                TARGET_HEIGHT * 2,
                TARGET_HEIGHT
            ),
            (
                30,
                30,
                30,
                255
            )
        )


    banner_img = ImageEnhance.Color(
        banner_img
    ).enhance(
        BANNER_COLOR_FACTOR
    )

    banner_img = ImageEnhance.Contrast(
        banner_img
    ).enhance(
        BANNER_CONTRAST_FACTOR
    )

    banner_img = ImageEnhance.Brightness(
        banner_img
    ).enhance(
        BANNER_BRIGHTNESS_FACTOR
    )


    banner_img = banner_img.rotate(
        3,
        expand=True
    )


    bw, bh = banner_img.size

    if bw <= 0:
        bw = 1

    if bh <= 0:
        bh = 1


    crop_left = int(
        bw * BANNER_START_X
    )

    crop_top = int(
        bh * BANNER_START_Y
    )

    crop_right = int(
        bw * BANNER_END_X
    )

    crop_bottom = int(
        bh * BANNER_END_Y
    )


    # Prevent invalid crop
    crop_right = max(
        crop_left + 1,
        crop_right
    )

    crop_bottom = max(
        crop_top + 1,
        crop_bottom
    )


    banner_img = banner_img.crop(
        (
            crop_left,
            crop_top,
            crop_right,
            crop_bottom
        )
    )


    bw, bh = banner_img.size

    if bh <= 0:
        bh = 1


    banner_width = max(
        100,
        int(
            TARGET_HEIGHT
            * (bw / bh)
            * 2
        )
    )


    banner_img = banner_img.resize(
        (
            banner_width,
            TARGET_HEIGHT
        ),
        Image.LANCZOS
    )

    banner_img = ImageEnhance.Sharpness(
        banner_img
    ).enhance(
        BANNER_SHARPNESS_FACTOR
    )


    # ========================================================
    # BASE COMPOSITE
    # ========================================================

    final_width = (
        avatar_img.width
        + banner_img.width
    )

    final = Image.new(
        "RGBA",
        (
            final_width,
            TARGET_HEIGHT
        ),
        (
            0,
            0,
            0,
            255
        )
    )


    final.alpha_composite(
        avatar_img,
        (0, 0)
    )

    final.alpha_composite(
        banner_img,
        (
            avatar_img.width,
            0
        )
    )


    # ========================================================
    # PRIME 8 FULL FRAME
    # ========================================================
    #
    # IMPORTANT:
    # prime8frame.png is treated as a FULL BANNER FRAME.
    #
    # It is NOT used as the Prime badge.
    #
    # It should preferably be a transparent PNG with:
    # - gold/yellow border
    # - transparent center
    #
    # ========================================================

    if prime_level == 8:

        apply_prime8_frame(
            final
        )


    # ========================================================
    # PIN / BADGE
    # ========================================================

    if (
        pin_bytes
        and pin_img.size != (100, 100)
    ):

        pin_img = pin_img.resize(
            (
                PIN_SIZE,
                PIN_SIZE
            ),
            Image.LANCZOS
        )

        final.alpha_composite(
            pin_img,
            (
                10,
                TARGET_HEIGHT
                - PIN_SIZE
                - 10
            )
        )


    # ========================================================
    # PRIME BADGE 0–8
    # ========================================================

    if 0 <= prime_level <= 8:

        prime_img = load_prime_badge(
            prime_level
        )

        if prime_img:

            prime_img.thumbnail(
                (
                    PRIME_BADGE_SIZE,
                    PRIME_BADGE_SIZE
                ),
                Image.LANCZOS
            )

            badge_x = (
                avatar_img.width
                - prime_img.width
                - 6
            )

            badge_y = 6

            final.alpha_composite(
                prime_img,
                (
                    badge_x,
                    badge_y
                )
            )


    # ========================================================
    # TEXT LAYERS
    # ========================================================

    draw = ImageDraw.Draw(
        final
    )


    font_big = load_unicode_font(
        125,
        FONT_FILE
    )

    font_big_c = load_unicode_font(
        125,
        FONT_CHEROKEE
    )

    font_small = load_unicode_font(
        95,
        FONT_FILE
    )

    font_small_c = load_unicode_font(
        95,
        FONT_CHEROKEE
    )

    font_level = load_unicode_font(
        50,
        FONT_FILE
    )


    # ========================================================
    # PLAYER NAME
    # ========================================================

    draw_unicode_text(
        draw=draw,
        text=name,
        position=(
            avatar_img.width + 65,
            40
        ),
        normal_font=font_big,
        cherokee_font=font_big_c,
        fill="white",
        stroke_width=STROKE_NAME,
        stroke_fill="black",
    )


    # ========================================================
    # GUILD
    # ========================================================

    draw_unicode_text(
        draw=draw,
        text=guild,
        position=(
            avatar_img.width + 65,
            220
        ),
        normal_font=font_small,
        cherokee_font=font_small_c,
        fill="white",
        stroke_width=STROKE_GUILD,
        stroke_fill="black",
    )


    # ========================================================
    # LEVEL
    # ========================================================

    level_text = f"Lvl. {level}"

    bbox = draw.textbbox(
        (0, 0),
        level_text,
        font=font_level,
        stroke_width=STROKE_LEVEL,
    )

    text_width = (
        bbox[2] - bbox[0]
    )

    text_height = (
        bbox[3] - bbox[1]
    )

    level_x = (
        final.width
        - text_width
        - 30
    )

    level_y = (
        TARGET_HEIGHT
        - text_height
        - 40
    )


    draw.text(
        (
            level_x,
            level_y
        ),
        level_text,
        font=font_level,
        fill="white",
        stroke_width=STROKE_LEVEL,
        stroke_fill="black",
    )


    # ========================================================
    # OUTPUT PNG
    # ========================================================

    output = io.BytesIO()

    final.save(
        output,
        format="PNG",
        optimize=True
    )

    output.seek(0)

    return output


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "status": "online",
        "api": "Sulav Banner API",
        "version": "2.0.0",
        "prime_levels": "0-8",
        "frame": "Prime 8 full banner frame",
        "endpoint": "/sulav?uid={uid}",
        "example": "/sulav?uid=11111111",
        "prime_override": (
            "/sulav?uid=11111111&prime=8"
        ),
    }


# ============================================================
# MAIN BANNER ENDPOINT
# ============================================================

@app.get("/sulav")
async def get_sulav_banner(
    uid: str = Query(
        ...,
        min_length=1,
        description="Free Fire Player UID"
    ),

    prime: Optional[int] = Query(
        None,
        ge=0,
        le=8,
        description="Prime Level override 0-8"
    ),
) -> Response:

    uid = uid.strip()

    if not uid:

        raise HTTPException(
            status_code=400,
            detail="UID parameter is required"
        )


    # ========================================================
    # FETCH SULAV PLAYER INFO
    # ========================================================

    try:

        response = await sulav_client.get(
            SULAV_INFO_API,
            params={
                "uid": uid
            }
        )

    except (
        httpx.HTTPError,
        asyncio.TimeoutError,
    ) as error:

        raise HTTPException(
            status_code=502,
            detail=(
                "Sulav API connection error: "
                f"{str(error)}"
            )
        )


    if response.status_code != 200:

        raise HTTPException(
            status_code=502,
            detail=(
                "Sulav API returned HTTP "
                f"{response.status_code}"
            )
        )


    # ========================================================
    # PARSE JSON
    # ========================================================

    try:

        data = response.json()

    except Exception:

        raise HTTPException(
            status_code=502,
            detail="Sulav API returned invalid JSON"
        )


    if not isinstance(
        data,
        dict
    ):

        raise HTTPException(
            status_code=502,
            detail="Invalid Sulav API response"
        )


    # ========================================================
    # DATA OBJECT
    # ========================================================

    if isinstance(
        data.get("data"),
        dict
    ):

        d = data["data"]

    else:

        d = data


    # ========================================================
    # BASIC INFO
    # ========================================================

    basic_info = d.get(
        "basicInfo",
        {}
    )

    if not isinstance(
        basic_info,
        dict
    ):

        basic_info = {}


    clan_info = d.get(
        "clanBasicInfo",
        {}
    )

    if not isinstance(
        clan_info,
        dict
    ):

        clan_info = {}


    # ========================================================
    # PLAYER DETAILS
    # ========================================================

    name = basic_info.get(
        "nickname",
        "Unknown"
    )

    level = basic_info.get(
        "level",
        0
    )

    guild = clan_info.get(
        "clanName",
        ""
    )


    # ========================================================
    # IMAGE IDs
    # ========================================================

    avatar_id = (
        basic_info.get(
            "headPic"
        )
    )

    banner_id = (
        basic_info.get(
            "bannerId"
        )
    )


    pin_id = (
        basic_info.get("badgeId")
        or
        basic_info.get("title")
        or
        basic_info.get("pin")
        or
        basic_info.get("pinId")
    )


    # ========================================================
    # PRIME LEVEL
    # ========================================================

    prime_level = extract_prime_level(
        d,
        query_prime=prime
    )


    # ========================================================
    # FETCH ALL PLAYER IMAGES
    # ========================================================

    (
        avatar_bytes,
        banner_bytes,
        pin_bytes,
    ) = await asyncio.gather(

        fetch_image_bytes(
            avatar_id
        ),

        fetch_image_bytes(
            banner_id
        ),

        fetch_image_bytes(
            pin_id
        ),
    )


    # ========================================================
    # GENERATE IMAGE IN THREAD
    # ========================================================

    loop = asyncio.get_running_loop()

    try:

        image_buffer = await loop.run_in_executor(

            sulav_process_pool,

            process_banner_image,

            {
                "level": level,
                "name": name,
                "guild": guild,
            },

            avatar_bytes,
            banner_bytes,
            pin_bytes,
            prime_level,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Banner generation failed: "
                f"{str(error)}"
            )
        )


    # ========================================================
    # RETURN PNG
    # ========================================================

    return Response(
        content=image_buffer.getvalue(),
        media_type="image/png",
        headers={
            "Cache-Control": (
                "public, max-age=60"
            ),
            "X-Prime-Level": str(
                prime_level
            ),
        },
    )


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000
    )