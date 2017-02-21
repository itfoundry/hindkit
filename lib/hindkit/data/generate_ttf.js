function run(ufo_paths) {
  for (let ufo_path of ufo_paths) {
    console.log("[OPEN IN GLYPHS]", ufo_path);
    ttf_path = ufo_path.replace(".ufo", ".ttf");
    app = Application("Glyphs");
    doc = app.open(ufo_path);
    font = doc.font;
    // for (let glyph of font.glyphs) {
    //   glyph.production = glyph.name;
    // }
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
    doc.close({saving: "yes"});
  }
}
