import datetime
import hindkit as kit

class Client(object):

    def __init__(self, family, name):

        self.family = family
        self.name = name

        self.style_scheme = kit.constants.STYLES_ITF
        self.vertical_metrics_strategy = "ITF"

        current_year = datetime.date.today().year
        if self.family.initial_release_year:
            self.release_year_range = str(self.family.initial_release_year)
            if current_year > self.family.initial_release_year:
                self.release_year_range += "-{}".format(str(current_year))
        else:
            self.release_year_range = str(current_year)

        self.tables = {}
        self.tables["name"] = {
            0: kit.fallback(
                self.family.info.copyright,
                "Copyright {} Indian Type Foundry. All rights reserved.".format(self.release_year_range),
            ),
            7: "{} is a trademark of the Indian Type Foundry.".format(self.family.trademark),
            8: "Indian Type Foundry",
            9: self.family.info.openTypeNameDesigner,
            10: self.family.info.openTypeNameDescription,
            11: "https://indiantypefoundry.com",
            12: self.family.info.openTypeNameDesignerURL,
            13: "This Font Software is protected under domestic and international trademark and copyright law. You agree to identify the ITF fonts by name and credit the ITF's ownership of the trademarks and copyrights in any design or production credits.",
            14: "https://indiantypefoundry.com/licensing",
            19: self.family.script.sample_text,
        }
        self.tables["OS/2"] = {
            "fsType": kit.fallback(self.family.info.openTypeOS2Type, 0),
            "Panose": "0 0 0 0 0 0 0 0 0 0",
            "Vendor": "ITFO",
        }

        self.override()

    def override(self):
        if self.name == "Google Fonts":
            self.style_scheme = kit.constants.STYLES_ITF_CamelCase
            self.vertical_metrics_strategy = "Google Fonts"
            self.tables["name"].update({
                0: kit.fallback(
                    self.family.info.copyright,
                    "Copyright {} Indian Type Foundry (info@indiantypefoundry.com)".format(self.release_year_range),
                ),
                7: None,
                13: "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL",
                14: "http://scripts.sil.org/OFL",
            })
