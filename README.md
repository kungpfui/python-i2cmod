# python-i2cmod
A Python library for some popular I2C connected sensor ICs.
Basically intended to use with Raspberry Pi and similar single
board computers.

Yet an other implementation for some I2C connected sensors you meight think.
Well, yes and no. As I started with some humidity and pressure sensors I was
scared to see some 20% working implementations which where obviously not really
working. The faulty measurement values has become obvious to me ... but it looked
like not for everyone. It's really hard to find proper implementations of
common I2C based sensors. So that was my starting point.


# Sensor Module Collection
### Humidity & Temperature
- [Sensirion SHT2X](<https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht2x-digital-i2c-accurate/>) (SHT20, SHT21, SHT25)
- [Sensirion SHT3X](<https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht3x-digital-i2c-accurate/>) (SHT30, SHT31, SHT35)

### Pressure & Temperature
- Bosch BMP280

### Pressure, Temperature & Humidity
- Bosch BME280

### Daylight Sensors
- Maxim Integrated MAX44009
- Vishay VEML6040

### UV Sensors
- Vishay VEML6075

### Monochrome OLED Displays
- SSD1306
