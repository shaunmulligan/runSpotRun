# copletely borrowed from here: https://gist.github.com/ppearson/52774
# NMEA to GPX converter
# Peter Pearson
# version 0.11

import csv
import sys
from time import strftime

class Converter:

    def __init__(self):
        self.name = "nmea-to-gpx-converter"

    def convert_dms_to_dec(self, value, dir):
        dPos = value.find(".")

        mPos = dPos - 2
        ePos = dPos

        main = float(value[:mPos])
        min1 = float(value[mPos:])

        newval = float(main) + float(min1)/float(60)

        if dir == "W":
            newval = -newval
        elif dir == "S":
            newval = -newval

        return newval

    def format_coord(self, value):
        return "%.9f" % float(round(value, 8))

    def format_time(self, value):
        pre = strftime("%Y-%m-%dT") #"2007-04-15T"
        hour = value[:2]
        minute = value[2:4]
        second = value[4:6]
        timeval = pre + hour + ":" + minute + ":" + second + "Z"
        return timeval

    def convert(self, inputfile, outputfile):
        reader = csv.reader(open(inputfile, "rb"))
        file = open(outputfile, 'w+')

        file.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<gpx version=\"1.0\" creator=\"nmea_conv\"\nxmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns=\"http://www.topografix.com/GPX/1/0\"\nxsi:schemaLocation=\"http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd\">\n")

        points = []
        count = 0
        minlat = 90
        maxlat = -90
        minlon = 180
        maxlon = -180

        for row in reader:
            type = row[0]

            validLoc = all(v is not '' for v in row[:13])
            if type == "$GPGGA" and validLoc:
                lat = self.convert_dms_to_dec(row[2], row[3])
                lon = self.convert_dms_to_dec(row[4], row[5])

                            # ignore dodgy values - safe to do, as it's unlikely I'm going to be in the South Atlantic anytime soon
                if lat == 0.0 and lon == 0.0:
                                continue

                points.append([])
                points[count].append(row[1])

                if lat < minlat:
                    minlat = lat
                if lat > maxlat:
                    maxlat = lat
                if lon < minlon:
                    minlon = lon
                if lon > maxlon:
                    maxlon = lon

                points[count].append(lat)
                points[count].append(lon)

                points[count].append(row[9])
                count += 1

        print "Points: '%i'" % (count)

        strbounds = "<bounds minlat=\"" + self.format_coord(minlat) + "\" minlon=\"" + self.format_coord(minlon) + "\" maxlat=\"" + self.format_coord(maxlat) + "\" maxlon=\"" + self.format_coord(maxlon) + "\"/>\n<trk>\n<trkseg>\n"
        file.write(strbounds)

        for point in range(count):
            time = points[point][0]
            lat_val = points[point][1]
            long_val = points[point][2]
            elev = points[point][3]

            strElev = "%.4f" % float(elev)

            strtrkpt = "<trkpt lat=\"" + self.format_coord(lat_val) + "\" lon=\"" + self.format_coord(long_val) + "\">\n  <ele>" + strElev + "</ele>\n<time>" + self.format_time(time) + "</time>\n</trkpt>\n"
            file.write(strtrkpt)

        file.write("</trkseg>\n</trk>\n</gpx>\n")
        file.close()

if __name__ == '__main__':
    inputfile, outputfile = sys.argv[1], sys.argv[2]
    test = Converter()
    test.convert(inputfile,outputfile)
    print "Done!"
