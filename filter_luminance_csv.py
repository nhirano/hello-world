import csv
import pandas as pd
# import numpy as np

def filter_luminance(lumens_csv, frames):
    column_headers = []
    header1 = lumens_csv.iloc[0]
    header2 = lumens_csv.iloc[1]
    i=0
    while i < len(lumens_csv.columns):
        header_1 = str(header1[i])
        if ('EP' in header_1) or ('Wavelengths' in header_1):
            column_headers.append(header_1+str(header2[i]))
            column_headers.append(header_1+str(header2[i+1]))
            column_headers.append(header_1+str(header2[i+2]))
            i += 2
        elif ('Red' in header_1) or ('Green' in header_1) or ('Blue' in header_1):
            column_headers.append(header_1+str(header2[i]))
            column_headers.append(header_1+str(header2[i+1]))
            column_headers.append(header_1+str(header2[i+2]))
            column_headers.append(header_1+str(header2[i+3]))
            i += 3
        elif pd.isnull(header1[i]) or ('Lumens' in header_1):
            column_headers.append(str(header2[i]))
        else:
            print('Error in column headers')
        i += 1

    lumens_csv.columns = column_headers
    lumens_csv = lumens_csv.drop([0,1,2])
    for header in column_headers:
        if all(s not in header for s in ('date', 'Frames', 'HOE')):
            lumens_csv[header] = lumens_csv[header].astype(str).replace('%', '', regex=True)
            lumens_csv[header] = lumens_csv[header].astype(str).replace('nan', '', regex=True)
            lumens_csv[header] = pd.to_numeric(lumens_csv[header])
        if any(s in header for s in ('DE', 'Fill Factor')):
            lumens_csv.loc[:,header] *= 0.01
    '''
    column headers are now:
      ['date', 'Frames', 'nan',
      'EP0Y', "EP0u'", "EP0v'", 'EP1Y', "EP1u'", "EP1v'", 'EP2Y', "EP2u'", "EP2v'", 'EP3Y', "EP3u'", "EP3v'",
      '--get-calibration-output-lumens', 'Target Lumens', 'Estimated Lumens', 'Whitex', 'Whitey',
      'WavelengthsR', 'WavelengthsG', 'WavelengthsB', 'HOE',
      'RedDE', 'RedAngle', 'RedBW', 'Red wavelength',
      'GreenDE', 'GreenAngle', 'GreenBW', 'Green wavelength',
      'BlueDE', 'BlueAngle', 'BlueBW', 'Blue wavelength',
      'EPx(deg)', 'EPy(deg)', 'EPz(mm)', 'FoR', 'Frame Rate',
      'Fill Factor-Red0', 'Fill Factor-Red1', 'Fill Factor-Red2', 'Fill Factor-Red3',
      'Fill Factor-Green0', 'Fill Factor-Green1', 'Fill Factor-Green2', 'Fill Factor-Green3',
      'Fill Factor-Blue0', 'Fill Factor-Blue1', 'Fill Factor-Blue2', 'Fill Factor-Blue3']
    '''

    frames_data = lumens_csv[lumens_csv['Frames'] == frames]

    return frames_data

def main():
    parser = argparse.ArgumentParser("Filter DVT luminance data for frames of interest")
    parser.add_argument('-fr', '--frames', type=str, help="FF####", required=True)
    parser.add_argument('-csv', '--csv_file', type=str, help="filename of the Luminance.csv from sheets", required=True)
    args = parser.parse_args()

    frames_data = filter_luminance(pd.read_csv(args.csv_file, header=None), args.frames)
    print(frames_data)


if __name__ == '__main__':
	main()