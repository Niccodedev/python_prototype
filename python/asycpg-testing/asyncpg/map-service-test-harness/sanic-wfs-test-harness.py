# *********************************************************************************************************************
# PURPOSE: Uses multiprocessing to make concurrent WMS requests in separate processes for load testing a WMS service.
#          Supports the use of WMS as a tile map service (such as GeoWebCache services)
#
# USAGE: Edit the parameters before main() to set:
#     1. The proxy server (if required)
#     2. The number of requests and concurrent processes to run
#     3. The WMS service parameters
#     4. The min/max map width and bounding box(es). These limit the randomised map extents to the area(s) of interest
#
# TO DO:
#     1. Add support for WMTS services
#     2. Improve logging to record request failures (failures currently printed to screen only)
#
# NOTE: The log file will only be output after all test cases have been run, this is to avoid writing to a shared
#       log file from multiple processes (possible in Python, but complicated...)
#
# LICENSE: Creative Commons Attribution 4.0 (CC BY 4.0)
# *********************************************************************************************************************

import csv
import math
import os
import random
import datetime
import time
import urllib.request
import traceback
import multiprocessing

# WMS or WFS?
request_type = "WFS"

# # Set proxy for web requests (if required)
# proxy = urllib.request.ProxyHandler({'http': ''})
# opener = urllib.request.build_opener(proxy)
# urllib.request.install_opener(opener)

# Total number of requests
requests = 1000

# Number of concurrent processes to run
processes = 100

# Max pause between requests (in whole milliseconds)
max_pause = 2000

# WMS Map tiles? (i.e. 256 x 256 pixel images in a Google/Bing Maps grid?)
map_tiles = True

# Min/max zoom levels (only required if map_tiles = True)
min_tile_level = 10
max_tile_level = 15

# Map width limits in wms_srid units - allows random zoom scales to be tested
# (required if map_tiles = False or request_type = "WFS")
min_map_width = 3000.0
max_map_width = 30000.0

# Map image width and height in pixels (required if map_tiles = False or request_type = "WFS")
map_image_width = 1024
map_image_height = 768

# Sanic WFS parameters
base_url = "http://127.0.0.1:8000/get-data"

# Dictionary of max and min coordinates in web mercator (metres). Used to randomly set map extents
max_bounding_boxes = {1: [16796997.0, -4020748.0, 16835959.0, -3995282.0],  # Sydney
                      2: [16124628.0, -4559667.0, 16163590.0, -4534318.0],  # Melbourne
                      3: [17021863.0, -3192356.0, 17048580.0, -3174789.0],  # Brisbane
                      4: [15417749.0, -4162522.0, 15447805.0, -4143515.0],  # Adelaide
                      5: [12884117.0, -3773816.0, 12921966.0, -3748880.0],  # Perth
                      6: [16391795.0, -5296763.0, 16410719.0, -5284614.0],  # Hobart
                      7: [16587717.0, -4225203.0, 16609981.0, -4187007.0]}  # Canberra


def main():

    # get list of map request urls
    request_list = create_requests()

    # Create pool of processes to get map images/tiles
    pool = multiprocessing.Pool(processes)

    start_time = datetime.datetime.now()
    print("\nStart {1} Stress Test : {0}\n".format(start_time, request_type))

    # Fire off requests
    results = pool.imap_unordered(get_url, request_list)
    results_list = list(results)

    pool.close()
    pool.join()

    elapsed_time = datetime.datetime.now() - start_time

    # Finish by logging parameters used and the results
    log_results(results_list, elapsed_time)

    print("Finished: elapsed time = ", str(elapsed_time))


def create_requests():
    request_list = list()

    # get list of random map extents
    bounds_list = create_random_bounds_list()

    for bounds in bounds_list:
        # get random zoom level
        zoom_level = str(random.randint(min_tile_level, max_tile_level))

        # Construct URL
        bounds_str = "/".join(bounds)

        url = "/".join([base_url, bounds_str, zoom_level]) + "/"
        # print(url)

        request_list.append(url)

    return request_list


def create_random_bounds_list():
    # Set default map tile set parameters
    if map_tiles and request_type == "WMS":
        global map_image_width
        global map_image_height
        map_image_width = 256
        map_image_height = 256
        map_ratio = 1.0
    else:
        map_ratio = float(map_image_height) / float(map_image_width)

    # Count of bounding boxes to map within
    max_bounding_box_count = len(max_bounding_boxes)

    bounds_list = list()

    # Set random map extents and fire off WMS requests in separate processes
    for i in range(0, requests):
        # Get random max/min bounding box
        max_bbox_num = random.randint(1, max_bounding_box_count)
        max_bbox = max_bounding_boxes.get(max_bbox_num)

        # Get random map width and height in wms_srid units
        if map_tiles and request_type == "WMS":
            tile_level = random.randint(min_tile_level, max_tile_level)
            map_width = 256.0 * tile_pixel_sizes[tile_level]
            map_height = map_width
        else:
            map_width = random.uniform(float(min_map_width), float(max_map_width))
            map_height = map_width * map_ratio

        # Calculate random bottom/left map coordinates
        left = random.uniform(float(max_bbox[0]), float(max_bbox[2]) - map_width)
        bottom = random.uniform(float(max_bbox[1]), float(max_bbox[3]) - map_height)

        # Adjust bottom/left map coordinates to the Google/Bing Maps tile grid if creating map tiles
        if map_tiles and request_type == "WMS":
            left = math.floor(left / map_width) * map_width
            bottom = math.floor(bottom / map_height) * map_height

        # Get top/right map coordinates
        right = left + map_width
        top = bottom + map_height

        # convert to lat/long if WFS
        if request_type == "WFS":
            bottom, left = web_mercator_to_wgs84(bottom, left)
            top, right = web_mercator_to_wgs84(top, right)

        bounds_list.append([str(left), str(bottom), str(right), str(top)])

    return bounds_list


# Gets a map image and returns the time taken (seconds), image size (bytes) and the URL for logging
def get_url(url):

    # wait for a random time to simulate real-world use
    random_pause = float(random.randint(0, max_pause)) / 1000.0
    time.sleep(random_pause)  # in seconds

    file_size = 0
    start_time = datetime.datetime.now()

    try:
        # Request map image and get its size as evidence of success or failure for logging
        request = urllib.request.Request(url)
        result = urllib.request.urlopen(request).read()
        file_size = len(result)
    except urllib.request.URLError:
        # Print failures to screen (these aren't logged)
        print(''.join(["MAP REQUEST FAILED : ", url,  '\n', traceback.format_exc()]))

    elapsed_time = datetime.datetime.now() - start_time
    elapsed_seconds = float(elapsed_time.microseconds) / 1000000.0

    return [elapsed_seconds, file_size, url]


# Default Google/Bing map tile scales per level (metres per pixel)
tile_pixel_sizes = [156543.033906250000000000,
                    78271.516953125000000000,
                    39135.758476562500000000,
                    19567.879238281200000000,
                    9783.939619140620000000,
                    4891.969809570310000000,
                    2445.984904785160000000,
                    1222.992452392580000000,
                    611.496226196289000000,
                    305.748113098145000000,
                    152.874056549072000000,
                    76.437028274536100000,
                    38.218514137268100000,
                    19.109257068634000000,
                    9.554628534317020000,
                    4.777314267158510000,
                    2.388657133579250000,
                    1.194328566789630000,
                    0.597164283394814000,
                    0.298582141697407000,
                    0.149291070848703000,
                    0.074645535424351700,
                    0.037322767712175800,
                    0.018661383856087900,
                    0.009330691928043960,
                    0.004665345964021980,
                    0.002332672982010990,
                    0.001166336491005500,
                    0.000583168245502748,
                    0.000291584122751374,
                    0.000145792061375687]


def web_mercator_to_wgs84(mercator_y, mercator_x):

    if abs(mercator_x) < 180 and abs(mercator_y) < 90:
        return
    if abs(mercator_x) > 20037508.3427892 or abs(mercator_y) > 20037508.3427892:
        return

    x = mercator_x
    y = mercator_y
    num3 = x / 6378137.0
    num4 = num3 * 57.295779513082323
    num5 = math.floor((num4 + 180.0) / 360.0)
    num6 = num4 - (num5 * 360.0)
    num7 = 1.5707963267948966 - (2.0 * math.atan(math.exp((-1.0 * y) / 6378137.0)))
    longitude = num6
    latitude = num7 * 57.295779513082323

    return [latitude, longitude]


def log_results(results_list, elapsed_time):
    log_entries = list()

    # Title, parameters used and results summary
    log_entries.append(["{0} Stress Test Results".format(request_type,)])
    log_entries.append([])
    # log_entries.append(["Elapsed time", "'" + str(elapsed_time)]) # not a relevant measure as processes pause randomly
    # log_entries.append([])
    log_entries.append(["Concurrent processes", str(processes)])
    if request_type == "WMS":
        log_entries.append(["Map image size", str(map_image_width) + " x " + str(map_image_height), "pixels"])
    log_entries.append([])
    log_entries.append(["Max random delay (ms)", max_pause])
    log_entries.append([])
    log_entries.append(["Requests", requests])
    log_entries.append([])

    success_count = 0
    total_seconds = 0.0
    total_size = 0

    # Calculate some stats
    for item in results_list:
        seconds = item[0]
        file_size = item[1]

        if file_size > 0:
            success_count += 1
            total_seconds += seconds
            total_size += file_size

    if success_count > 0:
        avg_seconds = total_seconds / float(success_count)
        avg_size = (float(total_size) / float(success_count)) / 1024.0
    else:
        avg_seconds = 0
        avg_size = 0

    log_entries.append(["Successful requests", success_count])
    log_entries.append(["Average time", avg_seconds, "seconds"])
    log_entries.append(["Average size", avg_size, "Kb"])
    log_entries.append(["Failed requests", requests - success_count])
    log_entries.append([])
    log_entries.append(["Time_seconds", "Image_bytes", "URL"])

    # Output results to log file
    log_file = open(time_stamped_file_name(os.path.abspath(__file__).replace(".py", "")) + ".csv", 'w')
    log_writer = csv.writer(log_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    log_writer.writerows(log_entries)
    log_writer.writerows(results_list)
    log_file.close()


# Adds a time stamp to a file name
def time_stamped_file_name(file_name, fmt='{file_name}_%Y_%m_%d_%H_%M_%S'):
    return datetime.datetime.now().strftime(fmt).format(file_name=file_name)


if __name__ == '__main__':
    main()
