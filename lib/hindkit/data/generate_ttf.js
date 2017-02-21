#!/usr/bin/env osascript -l JavaScript

function run(ufo_paths) {

  for (let ufo_path of ufo_paths) {

    app = Application("Glyphs");
    doc = app.open(ufo_path);
    font = doc.font;
    ttf_path = ufo_path.replace(".ufo", ".ttf");

    console.log("[OPENED IN GLYPHS]", ufo_path);

    for (let gid in font.glyphs) {
      console.log(gid);
      glyph = font.glyphs(gid);
      glyph.production = glyph.name;
    }

    console.log("[EXPORTING TO TTF]", ttf_path);

    font.instances[0].generate({
      to: ttf_path,
      as: "TTF",
      withProperties: {
        autohint: false,
        removeoverlap: true,
        usesubroutines: false,
        useproductionnames: false,
      },
    });

    doc.save();
    doc.close();

  }
}
