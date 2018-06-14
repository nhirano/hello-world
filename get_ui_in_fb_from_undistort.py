import numpy
import argparse
import cv2
import numpy as np
from PIL import Image

num_eps = 4
num_colors = 3

def split_colors(fb_rgb):
    red_img_array = np.zeros((len(fb_rgb), len(fb_rgb[0])), dtype=np.uint8)  # empty black and white image array
    green_img_array = np.zeros((len(fb_rgb), len(fb_rgb[0])), dtype=np.uint8)
    blue_img_array = np.zeros((len(fb_rgb), len(fb_rgb[0])), dtype=np.uint8)

    for i in range(0, len(fb_rgb)):  # 720
        for j in range(0, len(fb_rgb[0])):  # 1280
            # create separate RGB images
            if fb_rgb[i][j][0] > 1:
                red_img_array[i][j] = 100
            if fb_rgb[i][j][1] > 1:
                green_img_array[i][j] = 100
            if fb_rgb[i][j][2] > 1:
                blue_img_array[i][j] = 100
    red_ui_in_fb = corners(red_img_array)
    green_ui_in_fb = corners(green_img_array)
    blue_ui_in_fb = corners(blue_img_array)

    # img_array = [red_img_array, green_img_array, blue_img_array]

    return [red_ui_in_fb, green_ui_in_fb, blue_ui_in_fb] # return img_array for debug


def corners(img_array):
    img_array = cv2.dilate(img_array, None)
    img_array = cv2.GaussianBlur(img_array, (7, 7), 0)
    coords = cv2.goodFeaturesToTrack(img_array, num_eps*4, 0.01, 10)
    coords = np.int0(coords)
    return coords


def split_eps(all_ui_in_fb):
    y_array = np.empty([num_colors, num_eps*4])  # [all y coordinates for all eps][color]
    my_extents = np.zeros([4, 3, 4, 2])

    for c in range(0, num_colors):
        ui_in_fb = all_ui_in_fb[c]
        # this_img_array = img_array[c] # view image for debug (need img_array to be function input)
        for i in range(0, num_eps*4):
            y_array[c, i] = ui_in_fb[i][0][1]
            # this_img_array[y_array[c,i]-2:y_array[c,i]+2, x_array[c,i]-2:x_array[c,i]+2] = 255
        x_sorted = np.zeros([4,2])
        idx = 0
        for j in y_array[c].argsort()[12:16]: # 4 max y coordinates
            x_sorted[idx] = [ui_in_fb[j][0][0], ui_in_fb[j][0][1]]
            idx+=1
        x_sorted = x_sorted[x_sorted[:,0].argsort()]
        my_extents[2, c, 0, :] = x_sorted[0]
        my_extents[2, c, 1, :] = x_sorted[1]
        my_extents[1, c, 0, :] = x_sorted[2]
        my_extents[1, c, 1, :] = x_sorted[3]

        x_sorted = np.zeros([4,2])
        idx = 0
        for j in y_array[c].argsort()[8:12]: # 4 upper mid y coordinates
            x_sorted[idx] = [ui_in_fb[j][0][0], ui_in_fb[j][0][1]]
            idx+=1
        x_sorted = x_sorted[x_sorted[:,0].argsort()]
        my_extents[2, c, 3, :] = x_sorted[0]
        my_extents[2, c, 2, :] = x_sorted[1]
        my_extents[1, c, 3, :] = x_sorted[2]
        my_extents[1, c, 2, :] = x_sorted[3]

        x_sorted = np.zeros([4,2])
        idx = 0
        for j in y_array[c].argsort()[4:8]: # 4 lower mid y coordinates
            x_sorted[idx] = [ui_in_fb[j][0][0], ui_in_fb[j][0][1]]
            idx+=1
        x_sorted = x_sorted[x_sorted[:,0].argsort()]
        my_extents[0, c, 0, :] = x_sorted[0]
        my_extents[0, c, 1, :] = x_sorted[1]
        my_extents[3, c, 0, :] = x_sorted[2]
        my_extents[3, c, 1, :] = x_sorted[3]

        x_sorted = np.zeros([4,2])
        idx = 0
        for j in y_array[c].argsort()[0:4]: # 4 min coordinates
            x_sorted[idx] = [ui_in_fb[j][0][0], ui_in_fb[j][0][1]]
            idx+=1
        x_sorted = x_sorted[x_sorted[:,0].argsort()]
        my_extents[0, c, 3, :] = x_sorted[0]
        my_extents[0, c, 2, :] = x_sorted[1]
        my_extents[3, c, 3, :] = x_sorted[2]
        my_extents[3, c, 2, :] = x_sorted[3]

    return my_extents


def main():
    parser = argparse.ArgumentParser("Calculate ui coordinates in frame buffer space from the undistort image")
    parser.add_argument('-i', '--image', type=str, help="filename of the undistort_image.png", required=True)

    args = parser.parse_args()
    fb_rgb = np.array(Image.open(args.image))  # all colors and all EPs in one frame buffer image
    all_ui_in_fb = split_colors(fb_rgb)
    my_extents = split_eps(all_ui_in_fb)

    print(my_extents)

    # red = Image.fromarray(red_image)
    # green = Image.fromarray(green_image)
    # blue = Image.fromarray(blue_image)
    # red.show()
    # green.show()
    # blue.show()

if __name__ == '__main__':
	main()
