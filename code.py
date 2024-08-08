# Write your code here :-)
import time
import microcontroller
from board import NEOPIXEL
import displayio
import adafruit_display_text.label
from adafruit_datetime import datetime
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network

STOP_ID = "A48"
DATA_SOURCE = "https://api.wheresthefuckingtrain.com/by-id/%s" % (STOP_ID,)
DATA_LOCATION = ["data"]
UPDATE_DELAY = 15
SYNC_TIME_DELAY = 15
MINIMUM_MINUTES_DISPLAY = 1
BACKGROUND_IMAGE = "a-dashboard.bmp"
ERROR_RESET_THRESHOLD = 5


def get_arrival_in_minutes_from_now(now, date_str):
    train_date = datetime.fromisoformat(date_str).replace(
        tzinfo=None
    )  # Remove tzinfo to be able to diff dates
    return round((train_date - now).total_seconds() / 60.0)


def get_arrival_times():
    stop_trains = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
    stop_data = stop_trains[0]
    nortbound_trains = [x["time"] for x in stop_data["N"]]
    southbound_trains = [x["time"] for x in stop_data["S"]]

    now = datetime.now()
    print("Now: ", now)

    nortbound_arrivals = [
        get_arrival_in_minutes_from_now(now, x) for x in nortbound_trains
    ]
    southound_arrivals = [
        get_arrival_in_minutes_from_now(now, x) for x in southbound_trains
    ]

    n = [str(x) for x in nortbound_arrivals if x >= MINIMUM_MINUTES_DISPLAY]
    s = [str(x) for x in southound_arrivals if x >= MINIMUM_MINUTES_DISPLAY]

    n0 = n[0] if len(n) > 0 else "-"
    n1 = n[1] if len(n) > 1 else "-"
    s0 = s[0] if len(s) > 0 else "-"
    s1 = s[1] if len(s) > 1 else "-"

    return n0, n1, s0, s1



def update_text(n0, n1, s0, s1):
    top_static_line.text = "%s,%s m" % (n0, n1)
    bottom_static_line.text = "%s,%s m" % (s0, s1)
    display.show(group)


# --- Display setup ---
matrix = Matrix()
display = matrix.display
network = Network(status_neopixel=NEOPIXEL, debug=False)

# --- Drawing setup ---
group = displayio.Group()
bitmap = displayio.OnDiskBitmap(open(BACKGROUND_IMAGE, "rb"))
colors = [0x444444, 0xFC6900]  # [dim white, gold]

font = bitmap_font.load_font("fonts/6x10.bdf")

background = displayio.TileGrid(
    bitmap, pixel_shader=getattr(bitmap, "pixel_shader", displayio.ColorConverter())
)

top_dynamic_line = adafruit_display_text.label.Label(
    font, color=colors[0], x=16, y=3, text="NOSTRAND Av"
)
top_static_line = adafruit_display_text.label.Label(
    font, color=colors[1], x=20, y=11, text="- mins"
)

bottom_dynamic_line = adafruit_display_text.label.Label(
    font, color=colors[0], x=16, y=20, text="LEFFERTS Blvd"
)
bottom_static_line = adafruit_display_text.label.Label(
    font, color=colors[1], x=20, y=28, text="- mins"
)

group.append(background)
group.append(top_dynamic_line)
group.append(top_static_line)
group.append(bottom_dynamic_line)
group.append(bottom_static_line)
display.show(group)

error_counter = 0
last_time_sync = None
while True:
    try:
        if (
            last_time_sync is None
            or time.monotonic() > last_time_sync + SYNC_TIME_DELAY
        ):
            # Sync clock to minimize time drift
            network.get_local_time()
            last_time_sync = time.monotonic()
        arrivals = get_arrival_times()
        update_text(*arrivals)
    except (ValueError, RuntimeError) as e:
        print("Some error occured, retrying! -", e)
        error_counter = error_counter + 1
        if error_counter > ERROR_RESET_THRESHOLD:
            microcontroller.reset()

    time.sleep(UPDATE_DELAY)
