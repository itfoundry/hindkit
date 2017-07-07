#!/usr/bin/env osascript -l JavaScript

function run(ufo_paths) {

  for (let ufo_path of ufo_paths) {

    app = Application("Glyphs");
    doc = app.open(ufo_path);
    font = doc.font;
    ttf_path = ufo_path.replace(".ufo", ".ttf");

    console.log("[OPENED IN GLYPHS]", ufo_path);

    font.instances[0].generate({
      to: ttf_path,
      as: "TTF",
      withProperties: {
        autohint: false,
        removeoverlap: true,
        usesubroutines: true,
        useproductionnames: false,
      },
    });

    doc.save();
    doc.close();

    console.log("[EXPORTED TO TTF]", ttf_path);

  }
}
