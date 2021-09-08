# Changelog

## [3.0.0](https://www.github.com/TheRealWaldo/thermal/compare/v2.6.0...v3.0.0) (2021-09-08)


### ⚠ BREAKING CHANGES

* Using `person_detected` as a state on a sensor is deprecated and will be removed in future versions.  Use the new Binary Sensor instead.

### Features

* add state_class to sensor ([8019b86](https://www.github.com/TheRealWaldo/thermal/commit/8019b869a7d7f03246e85cc0cf4cb2814fe0da61))
* introduce binary_sensor for occupancy ([f0ee349](https://www.github.com/TheRealWaldo/thermal/commit/f0ee349c4d0f92c42929d4589f9b0121ce02c097))
* use hass native unit of measurement ([247487d](https://www.github.com/TheRealWaldo/thermal/commit/247487d7a873130a5a659d343e4279d53d219c3b))

## [2.6.0](https://www.github.com/TheRealWaldo/thermal/compare/v2.5.0...v2.6.0) (2021-09-07)


### Features

* support scaling, preserve aspect ratio ([0d02ea0](https://www.github.com/TheRealWaldo/thermal/commit/0d02ea05dc0f46d8db0a488d703bf7776b843add))

## [2.5.0](https://www.github.com/TheRealWaldo/thermal/compare/v2.4.2...v2.5.0) (2021-09-07)


### Features

* allow for min_diff when auto_range enabled ([f2a2e3c](https://www.github.com/TheRealWaldo/thermal/commit/f2a2e3c07891eb5a708f15c8140310b7b560d2b5))


### Documentation

* update HACS install steps ([967791a](https://www.github.com/TheRealWaldo/thermal/commit/967791add722b99768d59e79626b91aa867c7a70))

### [2.4.2](https://www.github.com/TheRealWaldo/thermal/compare/v2.4.1...v2.4.2) (2021-08-26)


### Bug Fixes

* person_detected and sensor_temp state ([78b4984](https://www.github.com/TheRealWaldo/thermal/commit/78b498419da6559cca9bc4d7d21b54fe8034935d))

### [2.4.1](https://www.github.com/TheRealWaldo/thermal/compare/v2.4.0...v2.4.1) (2021-08-26)


### Bug Fixes

* sensor would not start ([3402fdc](https://www.github.com/TheRealWaldo/thermal/commit/3402fdcec5cb50d21a2f2dc514961492dcd18b22))

## [2.4.0](https://www.github.com/TheRealWaldo/thermal/compare/v2.3.0...v2.4.0) (2021-08-19)


### Features

* add rudimentary person_detected support ([1dfa585](https://www.github.com/TheRealWaldo/thermal/commit/1dfa585305c25125051b5d1444890aa9e7b01a0c))

## [2.3.0](https://www.github.com/TheRealWaldo/thermal/compare/v2.2.1...v2.3.0) (2021-08-18)


### Features

* add ability to leverage ESPHome based camera ([8b4a6d8](https://www.github.com/TheRealWaldo/thermal/commit/8b4a6d8ab6210784c3ca776f61e221dca09749b1))
