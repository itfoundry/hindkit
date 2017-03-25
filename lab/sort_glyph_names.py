#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

# DERIVABLES = {
#     'nonbreakingspace': 'space',
#     'CR': 'space',
#     'softhyphen': 'hyphen',
#     'macronmod': 'macron', #?
# }
#
# DEFAULTS = [
#     'NULL',
#     'zerowidthspace',
#     'zerowidthjoiner',
#     'zerowidthnonjoiner',
#     '.notdef',
#     'dottedcircle',
# ]

names = 'odK_KA odNG_KA odT_KA odL_KA odLL_KA odSS_KA odS_KA odNG_KHA odS_KHA odNG_GA odDD_GA odD_GA odL_GA odD_GHA odNG_GHA odB_GHA odC_CA odNY_CA odSH_CA odC_CHA odNY_CHA odSH_CHA odJ_JA odNY_JA odB_JA odJ_JHA odNY_JHA odJ_NYA odK_TTA odNN_TTA odTT_TTA odP_TTA odPH_TTA odSS_TTA odS_TTA odK_TTHA odNN_TTHA odSS_TTHA odDD_DDA odNN_DDA odL_DDA odNN_DDHA odNN_NNA odSS_NNA odH_NNA odK_SS_NNA odK_TA odT_TA odN_TA odP_TA odS_TA odT_THA odN_THA odS_THA odG_DA odD_DA odN_DA odB_DA odG_DHA odD_DHA odN_DHA odB_DHA odG_NA odGH_NA odT_NA odN_NA odP_NA odM_NA odSH_NA odS_NA odH_NA odT_S_NA odT_PA odP_PA odM_PA odLL_PA odL_PA odSS_PA odS_PA odM_PHA odLL_PHA odSS_PHA odS_PHA odK_BA odNN_BA odT_BA odD_BA odDH_BA odN_BA odB_BA odM_BA odSH_BA odS_BA odH_BA odJ_J_BA odT_T_BA odN_T_BA odN_D_BA odN_DH_BA odD_BHA odM_BHA odLL_BHA odT_MA odD_MA odN_MA odM_MA odL_MA odSS_MA odS_MA odH_MA odK_SS_MA odDH_YA odK_RA odT_RA odNG_K_T_RA odN_T_RA odS_T_RA odL_LA odH_LA odK_SHA odK_SSA odNG_K_SSA odK_SA odT_SA odN_SA odP_SA odS_SA odK_LLA odG_LLA odP_LLA odSH_LLA '.split()

rules = '''\
  sub mlKA mlVirama mlKA by mlK_KA;
  sub mlKA mlVirama mlTA by mlK_TA;
  sub mlGA mlVirama mlDA by mlG_DA;
  sub mlGA mlVirama mlNA by mlG_NA;
  sub mlGA mlVirama mlMA by mlG_MA;
  sub mlNGA mlVirama mlKA by mlNG_KA;
  sub mlNGA mlVirama mlNGA by mlNG_NGA;
  sub mlJA mlVirama mlJA by mlJ_JA;
  sub mlJA mlVirama mlNYA by mlJ_NYA;
  sub mlNYA mlVirama mlCA by mlNY_CA;
  sub mlNYA mlVirama mlJA by mlNY_JA;
  sub mlNYA mlVirama mlNYA by mlNY_NYA;
  sub mlTTA mlVirama mlTTA by mlTT_TTA;
  sub mlNNA mlVirama mlTTA by mlNN_TTA;
  sub mlNNA mlVirama mlDDA by mlNN_DDA;
  sub mlNNA mlVirama mlMA by mlNN_MA;
  sub mlTA mlVirama mlTA by mlT_TA;
  sub mlTA mlVirama mlTHA by mlT_THA;
  sub mlTA mlVirama mlNA by mlT_NA;
  sub mlTA mlVirama mlBHA by mlT_BHA;
  sub mlTA mlVirama mlMA by mlT_MA;
  sub mlTA mlVirama mlSA by mlT_SA;
  sub mlDA mlVirama mlDA by mlD_DA;
  sub mlDA mlVirama mlDHA by mlD_DHA;
  sub mlNA mlVirama mlTA by mlN_TA;
  sub mlNA mlVirama mlTHA by mlN_THA;
  sub mlNA mlVirama mlDA by mlN_DA;
  sub mlNA mlVirama mlDHA by mlN_DHA;
  sub mlNA mlVirama mlNA by mlN_NA;
  sub mlNA mlVirama mlMA by mlN_MA;
  sub mlMA mlVirama mlPA by mlM_PA;
  sub mlMA mlVirama mlMA by mlM_MA;
  sub mlSHA mlVirama mlCA by mlSH_CA;
  sub mlSA mlVirama mlTHA by mlS_THA;
  sub mlHA mlVirama mlNA by mlH_NA;
  sub mlHA mlVirama mlMA by mlH_MA;
  sub mlLLA mlVirama mlLLA by mlLL_LLA;
  sub mlGA uni200D mlVirama mlDA by mlG_DA;
  sub mlGA uni200D mlVirama mlNA by mlG_NA;
  sub mlGA uni200D mlVirama mlMA by mlG_MA;
  sub mlNYA uni200D mlVirama mlCHA by mlNY_CHA;
  sub mlNNA uni200D mlVirama mlDDHA by mlNN_DDHA;
  sub mlTA uni200D mlVirama mlBHA by mlT_BHA;
  sub mlNA uni200D mlVirama mlTHA by mlN_THA;
  sub mlSHA uni200D mlVirama mlCHA by mlSH_CHA;
  sub mlSA uni200D mlVirama mlTHA by mlS_THA;
  sub mlHA uni200D mlVirama mlNA by mlH_NA;
  sub mlHA uni200D mlVirama mlMA by mlH_MA;
'''.splitlines()

STEMS = 'K KH G GH NG C CH J JH NY TT TTH DD DDH NN T TH D DH N P PH B BH M Y R L V SH SS S H RR LL K_SS J_NY'.split()
# STEMS.remove('K_SS')
# STEMS.remove('J_NY')
PARTS = []
for stem in STEMS:
    for suffix in ['A', '', 'Ac2']:
        if (stem in ['K_SS', 'J_NY']) and ('x' in suffix):
            continue
        else:
            PARTS.append(stem + suffix)

def process_name(name, remove_nukta=False):
    main = name[2:]
    if remove_nukta:
        main = main.replace('x', '')
    main = main.replace('_', ' ')
    main = main.replace('K SS', 'K_SS')
    main = main.replace('J NY', 'J_NY')
    parts = main.split(' ')
    return parts

def get_key(rule):
    name = rule.split()[-1][:-1]
    return [PARTS.index(part) for part in process_name(name)]

def get_key_without_nukta(name):
    key = [PARTS.index(part) for part in process_name(name, remove_nukta=True)]
    print(key)
    key.reverse()
    print(key)
    return key

# rules_sorted = sorted(rules, key=get_key)
names_sorted = sorted(names, key=get_key_without_nukta)

with open('original.txt', 'w') as f:
    f.write('\n'.join(names))

with open('sorted.txt', 'w') as f:
    f.write('\n'.join(names_sorted))
