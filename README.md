# Integration Blueprint

[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]

Helper integration to make one weight sensor be able to track several people's weight in separate sensors for each person.

**This integration will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show person's weight

## Installation
### Using HACS (Recommended)
1. Go to HACS > Integrations
1. In the top right corner click ⋮ > Custom repositories
1. Add this repository (https://github.com/maciejewiczow/ha-multiperson-weight-sensor) with category "Integration"
1. Click the new repository added
1. In the bottom right corner click "Download"
1. Restart Home Assistant after the download finishes
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Multi person weight sensor"

### Manual
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `integration_blueprint`.
1. Download _all_ the files from the `custom_components/multi_person_weight_sensor/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Multi person weight sensor"

## Configuration is done in the UI

Setup the integration using the provided configuration flow.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[license-shield]: https://img.shields.io/github/license/maciejewiczow/ha-multiperson-weight-sensor.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Maciej%20Adamus%20@maciejewiczow-blue.svg?style=for-the-badge
