# Thermal Vision

[![hacs][hacsbadge]][hacs]
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

The Thermal Vision integration allows for the use of Thermal Imaging sensors in [Home Assistant](https://www.home-assistant.io/).

These can be used to detect humans much more reliably than motion sensors as do not require the subject to be moving. They also produce a pretty thermal camera image!

![Me, waving](docs/waving.png)

This is a rework of [eyalcha/thermal](https://github.com/eyalcha/thermal) that corrects a number of issues, makes it compatible with HA 2016.6 forward, and adds new functionality.

## Differences

This is may not be a complete list:

- The platform/domain name is `thermal_vision` instead of `thermal`
- More resilient connections
- Fixes issues:
  - https://github.com/eyalcha/thermal/issues/1
  - https://github.com/eyalcha/thermal/issues/2
  - https://github.com/eyalcha/thermal/issues/5
  - https://github.com/eyalcha/thermal/issues/6
- Works with HA 2016.6 and up
- Allows for both imperial and metric measurements
- Optional auto-ranging capabilities
- Optional in-camera overlay of metrics

## Installation

There is three options to install this integration; HACS is the easiest.

## INSTALLATION VIA HACS

Just go into the HACS Integrations section, search for the "Thermal Vision" repository, then click Install!

### MANUAL INSTALLATION VIA HACS

Follow the instructions at https://hacs.xyz/docs/faq/custom_repositories/ using the URL https://github.com/TheRealWaldo/thermal

### MANUAL INSTALLATION

1. Download the zip file from
   [latest release](https://github.com/TheRealWaldo/thermal/releases/latest).
2. Unpack the release and copy the `custom_components/thermal_vision` directory
   into the `custom_components` directory of your Home Assistant
   installation.
3. Configure the `thermal_vision` sensor and/or camera.
4. Restart Home Assistant.

## Configuration

### Camera

```yaml
# Example configuration.yaml entry

camera:
  - platform: thermal_vision
    host: http://192.168.0.10
```

#### Main Options

|Parameter |Required|Description
|:---|---|---
| `platform` | Yes | Platform name `thermal_vision`
| `name` | No | Friendly name **Default**: `Thermal Vision`
| `host` | Yes | IP address or hostname of your Thermal sensor server
| `pixel_sensor` | Required if `host` is not set; sensor containing the base64 encoded pixels
| `verify_ssl` | No | Verify SSL or not **Default**: `false`
| `width` | No | Image width in pixels **Default**: `640`
| `height` | No | Image height in pixels **Default**: `640`
| `preserve_aspect_ratio` | No | Preserve aspect ratio (ignores height) **Default**: `true`
| `rotate` | No | Rotate image **Default**: `0`
| `mirror` | No | Mirror image true / false **Default**: `false`
| `format` | No | Camera image format (`jpeg`, `png`) **Default**: `jpeg`
| `min_temp` | No | Min temperature **Default**: `26`
| `max_temp` | No | Max temperature **Default**: `32`
| `auto_range` | No | Rather than use a static minimum and maximum temperature, auto adjust based on the content ***Default***: `false`
| `min_diff` | No | Minimum difference when auto-ranging.  Favors cold.  ***Default***: `4`
| `sensor` | No | Sensor related configurations (see below)
| `interpolate` | No | Interpolation related configurations (see below)
| `cold_color` | No | Cold color **Default**: `indigo`
| `hot_color` | No | Hot color **Default**: `red`
| `session_timeout` | No | Timeout in seconds for polling Thermal sensor server **Default**: `2`
| `overlay` | No | Add an overlay to the image to visualize min/max temperature **Default**: `false`

Interpolate

|Parameter |Required|Description
|:---|---|---
| `method` | No | Interpolation method (`bicubic`, `linear`, `disabled`) **Default**: `bicubic`
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
  - platform: thermal_vision
    host: http://192.168.0.10
```

#### Main Options

|Parameter |Required|Description
|:---|---|---
| `platform` | Yes | Platform name `thermal_vision`
| `name` | No | Friendly name **Default**: `Thermal Vision`
| `host` | Yes | IP address of your Thermal sensor server
| `verify_ssl` | No | Verify SSL or not **Default**: `false`
| `scan_interval` | No | Get raw data interval in seconds **Default**: `60`
| `sensor` | No | Sensor related configurations (see below)
| `roi` | No | Sensor region of interest (see below)
| `state` | No | Sensor state type (`average`, `max`, `min`, `sensor_temp`, `person_detected` (*deprecated, use `binary_sensor`*)) **Default**: `average`

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

The sensor state can be either `average`, `max`, `min`, or `person_detected` based on `state` in the configuration.  It defaults to `average`.

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
| `person_detected` | A boolean representing whether the sensor detected a person or not.  Must use latest firmware! (*deprecated, use `binary_sensor`*)

### Binary Sensor

```yaml
# Example configuration.yaml entry

binary_sensor:
  - platform: thermal_vision
    host: http://192.168.0.10
```

#### Main Options

|Parameter |Required|Description
|:---|---|---
| `platform` | Yes | Platform name `thermal_vision`
| `name` | No | Friendly name **Default**: `Thermal Vision`
| `host` | Yes | IP address of your Thermal sensor server
| `verify_ssl` | No | Verify SSL or not **Default**: `false`
| `scan_interval` | No | Get raw data interval in seconds **Default**: `60`

#### State and Attributes

##### State

Returns `on` when the sensor claims to detect a person, `off` when it does not.  Device class is `occupancy`.

## Sensor Hardware and Firmware

Sensors are based on a simple JSON interface.

|Sensor|Firmware
|:---|---
[AMG8833](https://eu.industrial.panasonic.com/products/sensors-optical-devices/sensors-automotive-and-industrial-applications/infrared-array/series/grid-eye-high-performance-type-amg8833/ADI8005/model/AMG8833)|Firmware for a simple sensor using an ESP8266 (I'm using a D1 Mini) can built using [TheRealWaldo/esp8266-amg8833](https://github.com/TheRealWaldo/esp8266-amg8833).  This firmware is still under development!<br><br>Also, there's an experimental implementation using [ESPHome](https://esphome.io/) at [TheRealWaldo/AMG8833-ESPHOME](https://github.com/TheRealWaldo/AMG8833-ESPHOME).  You can leverage this by setting `pixel_sensor` to the sensor created by ESPHome and not using `host`.  Note: this only works with the camera at this time.
[MLX90640](https://www.melexis.com/en/product/MLX90640/Far-Infrared-Thermal-Sensor-Array)|Another [PlatformIO](https://platformio.org/) project using an ESP32 and the MLX90640 cab be found at [pixelsquared/thermal_vision-ESP32-MLX90640](https://github.com/pixelsquared/thermal_vision-ESP32-MLX90640).


## Known Issues

Interpolation only works with sensors that have even dimensions (i.e. 8x8, 64x64, etc.).  A work-around is to disable interpolation:

```yaml
camera:
  - platform: thermal_vision
    host: http://192.168.0.10
    sensor:
      rows: 24
      cols: 32
    interpolate:
      method: disabled
```

[commits]: https://github.com/TheRealWaldo/thermal/commits/main
[commits-shield]: https://img.shields.io/github/commit-activity/m/therealwaldo/thermal?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/therealwaldo/thermal.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/v/release/therealwaldo/thermal?include_prereleases&style=for-the-badge
[releases]: https://github.com/TheRealWaldo/thermal/releases
