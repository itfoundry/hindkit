# HindKit

This package provides an API but it is _not_ maintained in a stable way for users outside ITF.

The `develop` branch is the most unstable, but the most up to date.

## Dependencies

- AFDKO (version 2.5 build 65781, April 3 2017) https://adobe.com/devnet/opentype/afdko.html
- vfb2ufo (if dealing with VFB files) https://blog.fontlab.com/font-utility/vfb2ufo/

## Install and use

Must be installed to AFDKO's Python:

`AFDKOPython setup.py install`

To build a project, execute the project's `build.py` with AFDKO's Python:

`AFDKOPython build.py`

## FYI

This package was originally developed and released as the build system for the Hind multiscript project:

- [Hind Vadodara](https://github.com/itfoundry/hind-vadodara) (Gujarati)
- [Hind Jalandhar](https://github.com/itfoundry/hind-jalandhar) (Gurmukhi)
- [Hind Siliguri](https://github.com/itfoundry/hind-siliguri) (Bangla)
- [Hind Guntur](https://github.com/itfoundry/hind-guntur) (Telugu)
- [Hind Mysuru](https://github.com/itfoundry/hind-mysuru) (Kannada)
- [Hind Kochi](https://github.com/itfoundry/hind-kochi) (Malayalam)
- [Hind Madurai](https://github.com/itfoundry/hind-madurai) (Tamil)
- [Hind Colombo](https://github.com/itfoundry/hind-colombo) (Sinhala)
