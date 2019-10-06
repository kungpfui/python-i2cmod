# python-i2cmod
A Python library for some popular I2C connected sensor ICs.
Basically intended to use with Raspberry Pi and similar single board computers.

![I2C Sensor Modules][sensor_modules.jpg]

Another implementation for I2C sensors, you might think.
Well, yes and no. When I started a small project with some
humidity and air pressure sensors, I was surprised that the
implementations found for the Raspberry Pi didn't seem to work
quite right. The readings were often faulty ... and nobody was bothered.
It's really hard to get a clean implementation of I2C-based sensors.
Very often these are 1:1 ports of the C code for microcontrollers with
all errors of the original and new ones related to the platform limitations.
That was my starting point to make it a little better. First of all you have
 to read and understand all the datasheets, which I did :-).

## Notice
The implementations do not support all possible operating modes of the
respective sensors. Very often only a specific configuration of the IC
can be used without adapting the library functions. However, it should
still be quite easy to implement your required operating mode with little
adaptation or expansion.

## Examples
Can you find in the _examples_ directory.

## Sensor Module Collection
### Humidity & Temperature
- [Sensirion SHT2X](<https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht2x-digital-i2c-accurate/>) (SHT20, SHT21, SHT25)
- [Sensirion SHT3X](<https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht3x-digital-i2c-accurate/>) (SHT30, SHT31, SHT35)

### Pressure & Temperature
- [Bosch Sensortec BMP280](https://www.bosch-sensortec.com/bst/products/all_products/bmp280)

### Pressure, Temperature & Humidity
- [Bosch Sensortec BME280](https://www.bosch-sensortec.com/bst/products/all_products/bme280)

### Daylight Sensors
- [Maxim Integrated MAX44009](https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX44009.html)
- [Vishay VEML6040](https://www.vishay.com/product?docid=84276)

### UV Sensors
- [Vishay VEML6075](http://www.vishay.com/docs/84304/veml6075.pdf) (EOL)

### Monochrome OLED Displays
- [Salomon Systech SSD1306](http://www.solomon-systech.com/en/product/display-ic/oled-driver-controller/ssd1306/)


[sensor_modules.jpg]: https://github.com/kungpfui/python-i2cmod/blob/master/docs/sensor_modules.jpg "I2C Sensor Modules"
