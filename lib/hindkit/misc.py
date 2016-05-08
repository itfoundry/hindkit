def write_mI_matches_to_files(style, mI_table, long_base_names):

    # do_mark_positioning = style.family.project.options['position_marks_for_mI_variants']
    # directory = style.directory
    # script_prefix = style.family.script.abbreviation

    # if do_mark_positioning:

        # with open(directory + '/abvm.fea', 'r') as f:
        #     abvm_content = f.read()
        #
        # original_abvm_content = restore_abvm_content(abvm_content)

        # original_abvm_lookup = re.search(
        #     r'(?m)^lookup MARK_BASE_{0} \{{\n(.+\n)+^\}} MARK_BASE_{0};'.format(MATRA_I_ANCHOR_NAME),
        #     original_abvm_content
        # ).group()

        # modified_abvm_lookup = original_abvm_lookup.replace(
        #     'pos base {}{}'.format(script_prefix, MATRA_I_NAME_STEM),
        #     'pos base @MATRA_I_BASES_'
        # )

    # Reph_positioning_offset = mI_table[0].glyph.width

    # class_def_lines = []
    # class_def_lines.extend(
    #     kit.Feature.compose_glyph_class_def_lines('MATRA_I_BASES_TOO_LONG', long_base_names)
    # )

    # substitute_rule_lines = []
    # lookup_name = 'matra_i_matching'

    # substitute_rule_lines.append('lookup {} {{'.format(lookup_name))

    for mI in mI_table:

        # mI_number = mI.glyph.name[-2:]
        # to_comment_substitute_rule = False

        # if not mI.matches:
        #     print('\t       `%s` is not used.' % mI.glyph.name)
        #     to_comment_substitute_rule = True
        #
        #     if do_mark_positioning:
        #
        #         modified_abvm_lookup = modified_abvm_lookup.replace(
        #             '\tpos base @MATRA_I_BASES_' + mI_number,
        #             '#\tpos base @MATRA_I_BASES_' + mI_number
        #         )

        if do_mark_positioning:

            locator = '@MATRA_I_BASES_%s <anchor ' % mI_number

            search_result = re.search(
                locator + r'\-?\d+',
                modified_abvm_lookup
            )

            if search_result:
                x = search_result.group().split(' ')[-1]
                modified_x = str(int(x) - Reph_positioning_offset)
                modified_abvm_lookup = modified_abvm_lookup.replace(
                    locator + x,
                    locator + modified_x,
                )

            else:
                print("\t[!] `%s` doesn't have the anchor for Reph." % mI.glyph.name)

        class_def_lines.extend(
            kit.Feature.compose_glyph_class_def_lines(
                'MATRA_I_BASES_' + mI_number,
                mI.matches
            )
        )

        substitute_rule_lines.append(
            "{}sub {}mI' @MATRA_I_BASES_{} by {};".format(
                '# ' if to_comment_substitute_rule else '  ',
                script_prefix,
                mI_number,
                mI.glyph.name
            )
        )

    # substitute_rule_lines.append('}} {};'.format(lookup_name))

    # if do_mark_positioning:

        # commented_original_abvm_lookup = '# ' + original_abvm_lookup.replace('\n', '\n# ')

        # modified_abvm_content = original_abvm_content.replace(
        #     original_abvm_lookup,
        #     commented_original_abvm_lookup + '\n\n\n' + modified_abvm_lookup
        # )

        # with open(directory + '/abvm.fea', 'w') as f:
        #     f.write(modified_abvm_content)

    # with open(directory + '/matra_i_matching.fea', 'w') as f:
    #     result_lines = (
    #         ['# CLASSES', ''] + class_def_lines +
    #         ['# RULES', ''] + substitute_rule_lines
    #     )
    #     f.write('\n'.join(result_lines) + '\n')
