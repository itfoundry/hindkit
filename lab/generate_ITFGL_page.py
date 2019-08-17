import hindkit as kit

data = kit.constants.get_glyph_list("itfgl.txt", with_u_scalar=True)

with open("temp/itfgl.md", "w") as f:
    f.write("# ITF Glyph List\n\n")
    f.write("| | glyph name | scalar value and character name |\n")
    f.write("| :---: | :--- | :--- |\n")
    for glyph_name, (u_scalar, u_name) in list(data.items()):
        f.write(
            "| {} | `{}` | `U+{} {}` |\n"
            .format(chr(int(u_scalar, 16)), glyph_name, u_scalar, u_name)
            .encode("UTF-8")
        )
