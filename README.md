# Thermal

[![hacs][hacsbadge]][hacs]
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

This is a rework of [eyalcha/thermal](https://github.com/eyalcha/thermal) that corrects a number of issues, makes it compatible with HA 2016.6 forward, and adds new functionality.

## Installation

### INSTALLATION VIA HACS

Follow the instructions at https://hacs.xyz/docs/faq/custom_repositories/ using the URL https://github.com/TheRealWaldo/thermal

### MANUAL INSTALLATION

1. Download the zip file from
   [latest release](https://github.com/TheRealWaldo/thermal/releases/latest).
2. Unpack the release and copy the `custom_components/thermal` directory
   into the `custom_components` directory of your Home Assistant
   installation.
3. Configure the `thermal` sensor and/or camera.
4. Restart Home Assistant.

## Configuration

### Camera

```yaml
# Example configuration.yaml entry

camera:
  - platform: thermal
    host: http://192.168.0.10
```

#### Main Options

|Parameter |Required|Description
|:---|---|---
| `platform` | Yes | Platform name
| `name` | No | Friendly name **Default**: `Thermal`
| `host` | Yes | IP address or hostname of your Thermal sensor server
| `verify_ssl` | No | Verify SSL or not **Default**: `false`
| `width` | No | Image width in pixels **Default**: `640`
| `height` | No | Image height in pixels **Default**: `640`
| `rotate` | No | Rotate image **Default**: `0`
| `mirror` | No | Mirror image true / false **Default**: `false`
| `format` | No | Camera image format (`jpeg`, `png`) **Default**: `jpeg`
| `min_temp` | No | Min temperature **Default**: `26`
| `max_temp` | No | Max temperature **Default**: `32`
| `auto_range` | No | Rather than use a static minimum and maximum temperature, auto adjust based on the content ***Default***: `false`
| `sensor` | No | Sensor related configurations (see below)
| `interpolate` | No | Interpolation related configurations (see below)
| `cold_color` | No | Cold color **Default**: `indigo`
| `hot_color` | No | Hot color **Default**: `red`
| `session_timeout` | No | Timeout in seconds for polling Thermal sensor server **Default**: `2`
| `overlay` | No | Add an overlay to the image to visualize min/max temperature **Default**: `false`

Interpolate

|Parameter |Required|Description
|:---|---|---
| `method` | No | Interpolation method (`bicubic`, `linear`) **Default**: `bicubic`
| `rows` | No | Number of rows in interpolated data **Default**: `32`
| `cols` | No | Number of columns of interpolated data **Default**: `32`

Sensor

|Parameter |Required|Description
|:---|---|---
| `rows` | No | Number of rows in sensor data **Default**: `8`
| `cols` | No | Number of columns in sensor data **Default**: `8`

#### State and Attributes

##### Attributes

|Attribute |Description
|:---|---
| `fps` | Approximate frames per second based on response time of sensor
| `min` | Minimum value represented by the `cold_color` in the image
| `max` | Maximum value represented by the `hot_color` in the image

### Sensor

```yaml
# Example configuration.yaml entry

sensor:
  - platform: thermal
    host: http://192.168.0.10
```

#### Main Options

|Parameter |Required|Description
|:---|---|---
| `platform` | Yes | Platform name
| `name` | No | Friendly name **Default**: `Thermal`
| `host` | Yes | IP address of your Thermal sensor server
| `verify_ssl` | No | Verify SSL or not **Default**: `false`
| `scan_interval` | No | Get raw data interval in seconds **Default**: `60`
| `sensor` | No | Sensor related configurations (see below)
| `roi` | No | Sensor region of interest (see below)
| `state` | No | Sensor state type (`average`, `max`, `min`) **Default**: `average`

Sensor

|Parameter |Required|Description
|:---|---|---
| `rows` | No | Number of rows in sensor data **Default**: `8`
| `cols` | No | Number of columns in sensor data **Default**: `8`

ROI

|Parameter |Required|Description
|:---|---|---
| `left` | No | Left pixel index [0:cols-1] **Default**: `0`
| `top` | No | Top pixel index [0:rows-1] **Default**: `0`
| `right` | No | Right pixel index [0:cols-1] **Default**: `7`
| `bottom` | No | Bottom pixel index [0:rows-1] **Default**: `7`

#### State and Attributes

##### State

The sensor state can be either `average`, `max`, or `min` based on `state` in the configuration.  It defaults to `average`.

##### Attributes

All values are affected by the ROI configuration.

|Attribute |Description
|:---|---
| `average` | Average temperature of all pixels in current capture
| `max` | Maximum temperature of all pixels in current capture
| `min` | Min temperature of all pixels in current capture
| `min_index` | The index where the min temperature was detected (1 Dimensional)
| `max_index` | The index where the max temperature was detected (1 Dimensional)
| `sensor_temp` | The temperature of the sensor itself (if the sensor provides it)

[commits]: https://github.com/TheRealWaldo/thermal/commits/main
[commits-shield]: https://img.shields.io/github/commit-activity/m/therealwaldo/thermal?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/therealwaldo/thermal.svg?style=for-the-badge
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/v/release/therealwaldo/thermal?include_prereleases&style=for-the-badge
[releases]: https://github.com/TheRealWaldo/thermal/releases