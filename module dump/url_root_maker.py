# -*- coding: utf-8 -*-
"""
Created on Mon Jan 22 21:12:56 2024

@author: surma
"""

import pandas as pd
import numpy as np

info = pd.read_csv('../../data/imports/d3info.csv')
urls = info[info.columns.values[-1]]
info['url_root'] = urls.str.split('//').str[1].str.split('/').str[0].str.replace('www.','').fillna('')
info.to_csv('../../data/imports/d3info.csv')
