import fitparse
import sys
import xml.etree.ElementTree as ET


if len(sys.argv) != 3:
    print("Usage: python3 magic_foodpod.py activity.fit route.tcx")
    sys.exit(1)


fitfile = fitparse.FitFile(
    sys.argv[1],
    data_processor=fitparse.StandardUnitsDataProcessor(),
)

ns = {
    'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
}
root = ET.parse(sys.argv[2]).getroot()
route = root.iterfind('./tcx:Courses/tcx:Course/tcx:Track/tcx:Trackpoint', ns)
behind = next(route)
ahead = next(route)


def interpolate_position(distance):
    global behind, ahead
    while float(ahead.find('tcx:DistanceMeters', ns).text) < distance:
        behind = ahead
        ahead = next(route)
    distance_behind = float(behind.find('tcx:DistanceMeters', ns).text)
    distance_ahead = float(ahead.find('tcx:DistanceMeters', ns).text)
    q = (distance - distance_behind) / (distance_ahead - distance_behind)
    lat_behind = float(
        behind.find('tcx:Position/tcx:LatitudeDegrees', ns).text
    )
    lat_ahead = float(
        ahead.find('tcx:Position/tcx:LatitudeDegrees', ns).text
    )
    latitude = lat_behind + q * (lat_ahead - lat_behind)
    long_behind = float(
        behind.find('tcx:Position/tcx:LongitudeDegrees', ns).text
    )
    long_ahead = float(
        ahead.find('tcx:Position/tcx:LongitudeDegrees', ns).text
    )
    # Worst GOS calculation EVER.
    longitude = long_behind + q * (long_ahead - long_behind)
    return {'position_lat': latitude, 'position_long': longitude}


tcx = ET.Element('TrainingCenterDatabase')
tcx.set(
    'xsi:schemaLocation',
    ' '.join([
        'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
        'http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd',
    ])
)
tcx.set('xmlns:ns5', 'http://www.garmin.com/xmlschemas/ActivityGoals/v1')
tcx.set('xmlns:ns3', 'http://www.garmin.com/xmlschemas/ActivityExtension/v2')
tcx.set('xmlns:ns2', 'http://www.garmin.com/xmlschemas/UserProfile/v2')
tcx.set('xmlns', 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2')
tcx.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
tcx.set('xmlns:ns4', 'http://www.garmin.com/xmlschemas/ProfileExtension/v1')

activities = ET.SubElement(tcx, 'Activities')
activity = ET.SubElement(activities, 'Activity')
activity_id = ET.SubElement(activity, 'Id')
lap = None
creator_info = {}


def create_lap():
    lap = ET.SubElement(activity, 'Lap')
    ET.SubElement(lap, 'TotalTimeSeconds')
    ET.SubElement(lap, 'DistanceMeters')
    ET.SubElement(lap, 'MaximumSpeed')
    ET.SubElement(lap, 'Calories')
    ET.SubElement(ET.SubElement(lap, 'AverageHeartRateBpm'), 'Value')
    ET.SubElement(ET.SubElement(lap, 'MaximumHeartRateBpm'), 'Value')
    ET.SubElement(lap, 'Intensity').text = 'Active'
    ET.SubElement(lap, 'TriggerMethod').text = 'Manual'
    ET.SubElement(lap, 'Track')
    extensions = ET.SubElement(ET.SubElement(lap, 'Extensions'), 'ns3:LX')
    ET.SubElement(extensions, 'ns3:AvgSpeed')
    ET.SubElement(extensions, 'ns3:AvgRunCadence')
    ET.SubElement(extensions, 'ns3:MaxRunCadence')
    return lap


def render_product_name(product_name):
    if product_name.startswith('fr'):
        return 'Forerunner {}'.format(product_name[2:])
    return product_name


def render_timestamp(dt):
    return '{}.000Z'.format(dt.isoformat())


for record in fitfile.get_messages():
    if record.type != 'data':
        continue

    if record.name == 'file_id':
        activity_id.text = render_timestamp(record.get_value('time_created'))
        creator_info['product_name'] = record.get_value('garmin_product')
        creator_info['serial_number'] = record.get_value('serial_number')
    elif record.name == 'file_creator':
        creator_info['software_version'] = record.get_value('software_version')
    elif record.name in [
        'device_info', 'device_settings', 'user_profile', 'zones_target',
        'developer_data_id', 'field_description', 'hrv', 'session', 'activity',
        'training_file',
    ]:
        pass
    elif record.name == 'event':
        event = record.get_values()
        if event['event_type'] == 'start':
            if lap is None:
                lap = create_lap()
            lap.set('StartTime', render_timestamp(event['timestamp']))
        elif event['event_type'] in ['stop', 'stop_all', 'marker']:
            pass
        else:
            raise RuntimeError(event)
    elif record.name == 'sport':
        activity.set('Sport', record.get_value('sport').capitalize())
    elif record.name.startswith('unknown_'):
        pass
    elif record.name == 'record':
        if lap is None:
            lap = create_lap()
        data = record.get_values()
        trackpoint = ET.SubElement(lap.find('Track'), 'Trackpoint')
        time = ET.SubElement(trackpoint, 'Time')
        time.text = render_timestamp(record.get_value('timestamp'))
        position = ET.SubElement(trackpoint, 'Position')
        position_lat = ET.SubElement(position, 'LatitudeDegrees')
        position_long = ET.SubElement(position, 'LongitudeDegrees')
        coords = interpolate_position(record.get_value('distance') * 1000)
        position_long.text = str(coords['position_long'])
        position_lat.text = str(coords['position_lat'])
        distance = ET.SubElement(trackpoint, 'DistanceMeters')
        distance.text = str(record.get_value('distance') * 1000)
        heart_rate = ET.SubElement(
            ET.SubElement(trackpoint, 'HeartRateBpm'),
            'Value'
        )
        heart_rate.text = str(record.get_value('heart_rate'))
        extensions = ET.SubElement(
            ET.SubElement(trackpoint, 'Extensions'),
            'ns3:TPX')
        speed = ET.SubElement(extensions, 'ns3:Speed')
        speed.text = str(record.get_value('speed') / 3.6)
        cadence = ET.SubElement(extensions, 'ns3:RunCadence')
        cadence.text = str(record.get_value('cadence'))
    elif record.name == 'lap':
        lap.set('StartTime', render_timestamp(record.get_value('start_time')))
        lap.find('TotalTimeSeconds').text = '{:0.1f}'.format(
            float((record.get_value('timestamp') - record.get_value('start_time')).seconds)
        )
        lap.find('DistanceMeters').text = str(record.get_value('total_distance'))
        lap.find('MaximumSpeed').text = str(record.get_value('enhanced_max_speed') / 3.6)
        lap.find('Calories').text = str(record.get_value('total_calories'))
        lap.find('AverageHeartRateBpm/Value').text = str(record.get_value('avg_heart_rate'))
        lap.find('MaximumHeartRateBpm/Value').text = str(record.get_value('max_heart_rate'))
        extensions = lap.find('Extensions').find('ns3:LX')
        extensions.find('ns3:AvgSpeed').text = str(record.get_value('avg_speed') / 3.6)
        extensions.find('ns3:AvgRunCadence').text = str(record.get_value('avg_running_cadence'))
        extensions.find('ns3:MaxRunCadence').text = str(record.get_value('max_running_cadence'))

        lap = None
    else:
        print(record.name)
        print(record.get_values())
        raise RuntimeError('Unknown record name')


creator = ET.SubElement(activity, 'Creator')
creator.set('xsi:type', 'Device_t')
name = ET.SubElement(creator, 'Name')
name.text = render_product_name(creator_info['product_name'])
unit_id = ET.SubElement(creator, 'UnitId')
unit_id.text = str(creator_info['serial_number'])
v = creator_info['software_version']
version = ET.SubElement(creator, 'Version')
ET.SubElement(version, 'VersionMajor').text = str(v // 100)
ET.SubElement(version, 'VersionMinor').text = str(v % 100)
ET.SubElement(version, 'BuildMajor').text = '0'
ET.SubElement(version, 'BuildMinor').text = '0'

ET.dump(tcx)
