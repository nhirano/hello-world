import argparse
import filter_luminance_csv
import cie_xyz
import hologram
import lumens_luminance
import calc_fill_factor
import get_ui_in_fb_from_undistort
import csv
import pandas as pd
import numpy as np
from PIL import Image

COLORS = ['Red  ', 'Green', 'Blue ']
TOL = ['Min', 'Typ', 'Max']

def main():
    '''
    This script improves the accuracy form correlate_lm_nits by calculating the
    fill factor from the UI coordinates in frame buffer space instead of using
    the extents file.
    The intent of this script is to take in measured data for the hologram
    and projector to run through the hologram, lumens_luminance, and fill_factor
    models to calculate the expected luminance and u'v' color per ep.  
    The results then can be compared to the luminance and u'v' color measured
    directly at the Gamma Scientific station.  
    A command line input/output interface is implemented.  
    To be implemented: improve the interface which pulls in a list of Frames and
    the data associated with those frames from a csv and outputs a table of results.
    An even better implementation would be to grab all the needed data from
    Pyrope based on the Frames number only.
    '''

    parser = argparse.ArgumentParser("Calculate nits per ep")
    # parser.add_argument('-csv', '--csv_file', type=str, help="filename of the Luminance.csv from sheets", required=True)
    parser.add_argument('-f', '--frames', type=str, help="FF####", required=True)
    parser.add_argument('-u', '--undistort_image', type=str,
                        help="undistort_image.png. This is the output of undistort.exe from display tools, "
                        + "given a white220x220.png input and the specific frame undistortMap.bin file",
                        required=True)
    parser.add_argument('-p','--pixel_pulse_width', type=float,
                        help="pixel pulse width in ns.  Use 10ns for RTZ assumed elsewhere. "
                        + "Or use 5ns to include RTZ 50 percent duty factor in calculated fill factor values.",
                        required=False, default=10)
    parser.add_argument('-o', '--output_filename', type=str, help=".csv output file name", required=False,
                        default='Compare_GSI_Sim.csv')
    args = parser.parse_args()

    temperature = 28
    num_colors = 3
    num_eps = 4

    # dvt data file from Luminance tab in this Google Spreadsheet:
    # https://docs.google.com/spreadsheets/d/1IRBPWiw00xvhBf8A5g9ERYtBrXCw_AKGCv0U7nvLEtc/edit#gid=1323064588
    frames_data = filter_luminance_csv.filter_luminance(
        pd.read_csv('DVT Brightness and Colour - Luminance.csv', header=None),
        args.frames)

    wavelengths = [frames_data['WavelengthsR'], frames_data['WavelengthsG'], frames_data['WavelengthsB']]

    this_cie_xyz = cie_xyz.CIEXYZ(red=[wavelengths[0], 1.0],
        green=[wavelengths[1], 1.0],
        blue=[wavelengths[2], 1.0])

    this_lumens_luminance = lumens_luminance.LumensLuminance(
        conf_filename='lumens_luminance.conf')

    projector_rgb_powers = this_cie_xyz.get_RGB_powers([frames_data['Estimated Lumens'],
                                                        frames_data['Whitex'], frames_data['Whitey']])

    # calculate fill factors from the rgb undistort image
    fb_rgb = np.array(Image.open(args.undistort_image))

    fill_factors = calc_fill_factor.calculate_fill_factor(
        get_ui_in_fb_from_undistort.split_eps(get_ui_in_fb_from_undistort.split_colors(fb_rgb)),
        frames_data['Frame Rate'], args.pixel_pulse_width)

    holograms = np.empty(num_colors, dtype=object)

    holograms[0] = hologram.Hologram(conf_filename='red_hologram.conf', bin=3)#2)
    holograms[1] = hologram.Hologram(conf_filename='green_hologram.conf', bin=3)#2)
    holograms[2] = hologram.Hologram(conf_filename='blue_hologram.conf', bin=3)

    #update the hologram models based on peak DE inputs
    holograms[0].peak_de = [frames_data['RedDE'], frames_data['RedDE'], frames_data['RedDE'], frames_data['RedDE']]
    holograms[1].peak_de = [frames_data['GreenDE'], frames_data['GreenDE'], frames_data['GreenDE'], frames_data['GreenDE']]
    holograms[2].peak_de = [frames_data['BlueDE'], frames_data['BlueDE'], frames_data['BlueDE'], frames_data['BlueDE']]

    holograms[0].peak_de_angle = [frames_data['RedAngle'] - holograms[0].peak_de_design_angle,
                                  frames_data['RedAngle'] - holograms[0].peak_de_design_angle,
                                  frames_data['RedAngle'] - holograms[0].peak_de_design_angle,
                                  frames_data['RedAngle'] - holograms[0].peak_de_design_angle]
    holograms[1].peak_de_angle = [frames_data['GreenAngle'] - holograms[1].peak_de_design_angle,
                                  frames_data['GreenAngle'] - holograms[1].peak_de_design_angle,
                                  frames_data['GreenAngle'] - holograms[1].peak_de_design_angle,
                                  frames_data['GreenAngle'] - holograms[1].peak_de_design_angle]
    holograms[2].peak_de_angle = [frames_data['BlueAngle'] - holograms[2].peak_de_design_angle,
                                  frames_data['BlueAngle'] - holograms[2].peak_de_design_angle,
                                  frames_data['BlueAngle'] - holograms[2].peak_de_design_angle,
                                  frames_data['BlueAngle'] - holograms[2].peak_de_design_angle]

    holograms[0].wavelength = [frames_data['Redλ'], frames_data['Redλ'], frames_data['Redλ'], frames_data['Redλ']]
    holograms[1].wavelength = [frames_data['Greenλ'], frames_data['Greenλ'],frames_data['Greenλ'], frames_data['Greenλ']]
    holograms[2].wavelength = [frames_data['Blueλ'], frames_data['Blueλ'], frames_data['Blueλ'], frames_data['Blueλ']]

    # organize results for command line output
    for e in range(4):
        for t in range(4):
            holograms[0].fwhm[e, t] = frames_data['RedBW']
            holograms[1].fwhm[e, t] = frames_data['GreenBW']
            holograms[2].fwhm[e, t] = frames_data['BlueBW']

    eps_rgb_powers = np.empty((num_colors, num_eps, 3))
    eps_lumens_uv = np.empty((num_colors, num_eps, 3))
    eps_luminance = np.empty((num_eps, 3))

    des = np.empty((num_colors, num_eps, 3))

    for i in range(3):
        for e in range(num_eps):
            for c in range(num_colors):
                eps_rgb_powers[c, e, i] = holograms[c].simulate(
                    projector_rgb_powers[c] * fill_factors[e, c],
                    wavelengths[c], temperature, e, i)
                des[c, e, i] = holograms[c].get_de(wavelengths[c], temperature, e, i)
            eps_lumens_uv[:, e, i] = this_cie_xyz.get_lumens_uv(eps_rgb_powers[:, e, i])
            eps_luminance[e, i] = this_lumens_luminance.lm_to_nits(eps_lumens_uv[0, e, i])

    eps = ['EP0','EP1','EP2','EP3']
    colors=['Red','Green','Blue']
    sim_vs_gsi = {'indices':[], 'Sim_min': [], 'Sim_typ': [], 'Sim_max': [], 'GSI': []}
    for e in range(num_eps):
        for c in range(num_colors):
            ec = eps[e]+' '+colors[c]
            sim_vs_gsi['indices'] += (ec+' % Fill Factor', ec+' %DE', ec+' Power (mW)')
            sim_vs_gsi['GSI'] += (frames_data['Fill Factor-'+colors[c]+str(e)].values[0],
                                  frames_data[colors[c]+'DE'].values[0], '')
            sim_vs_gsi['Sim_min'] += ('', des[c, e, 0], eps_rgb_powers[c, e, 0])
            sim_vs_gsi['Sim_typ'] += (fill_factors[e, c], des[c, e, 1], eps_rgb_powers[c, e, 1])
            sim_vs_gsi['Sim_max'] += ('', des[c, e, 2], eps_rgb_powers[c, e, 2])
        ep = eps[e]
        sim_vs_gsi['indices'] += (ep+' lumens', ep+" u'", ep+" v'",ep+' luminance')
        sim_vs_gsi['GSI'] += ('',frames_data[eps[e]+"u'"].values[0], frames_data[eps[e]+"v'"].values[0],
                              frames_data[eps[e]+'Y'].values[0])
        sim_vs_gsi['Sim_min'] += (eps_lumens_uv[0, e, 0], eps_lumens_uv[1, e, 0], eps_lumens_uv[2, e, 0], eps_luminance[e, 0])
        sim_vs_gsi['Sim_typ'] += (eps_lumens_uv[0, e, 1], eps_lumens_uv[1, e, 1], eps_lumens_uv[2, e, 1], eps_luminance[e, 1])
        sim_vs_gsi['Sim_max'] += (eps_lumens_uv[0, e, 2], eps_lumens_uv[1, e, 2], eps_lumens_uv[2, e, 2], eps_luminance[e, 2])

    df = pd.DataFrame(data=sim_vs_gsi)
    df = df.set_index('indices')
    print(df)

    # save results in a csv
    df.to_csv(args.output_filename)


if __name__ == '__main__':
    main()
