#!/usr/bin/env AFDKOPython
# encoding: UTF-8


import hindkit

U_SCALAR_TO_U_NAME = hindkit.constants.get_u_scalar_to_u_name()

for production_name, u_scalar in hindkit.constants.get_adobe_latin(4).items():
    # print(
    #     "{0} {0} uni{1} # {2}".format(production_name, u_scalar, U_SCALAR_TO_U_NAME[u_scalar])
    # )
    print(production_name)
