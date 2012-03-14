#!/usr/bin/python
#
# ZkUnitNames - console application to give the names of the units
#
# Tested on Python 2.7.2, Windows 7 on ZK Games only, YMMV on other platforms and other games based on Spring
# 
# (C) 2012, Rene van 't Veen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# For a copy of the GNU General Public License see <http://www.gnu.org/licenses/>.
#
import sys
import os
import fnmatch
import re

__author__ = 'rene'
__version__ = '0.1.0'

class ZkUnitParserError(Exception):
    '''
    This modules own exception
    '''
    pass

class ZkUnitNamesParser:
    def run(self, dir):
        '''
        Parse all .lua files in the given directory and extract unitname (the abbreviation) and the
        name (the full display name)
        '''
        unitfilemark = re.compile(r'^unitDef\s*=\s*\{\s*$')
        unitname = re.compile(r'^\s*unitname\s*=\s*\[\[(.*)\]\]\s*,\s*$')
        fullname = re.compile(r'^\s*name\s*=\s*\[\[(.*)\]\]\s*,\s*$')
        braceopen = re.compile(r'{')
        braceclose = re.compile(r'}')
        names = dict()
        for filename in ( os.listdir(dir)):
            if fnmatch.fnmatch(filename,'*.lua'):
                try:
                    f = open(dir + '/' + filename)
                    try:
                        state = 0
                        depth = 0
                        munit = None
                        mfull = None
                        n = 0
                        for line in f:
                            n += 1
                            if state == 0 and depth == 0:
                                if unitfilemark.match(line):
                                    state = 1
                                    depth = 1
                                    continue
                            elif state == 1 and depth == 1:
                                m = unitname.match(line)
                                if m:
                                    if munit != None:
                                        raise ZkUnitParserError()
                                    munit = m.group(1)
                                    continue
                                else:
                                    m = fullname.match(line)
                                    if m:
                                        if mfull != None:
                                            raise ZkUnitParserError()
                                        mfull = m.group(1)
                                        continue
                            depth += line.count('{')
                            depth -= line.count('}')
                        if state == 0:
                            print >> sys.stderr, 'file ' + filename + ' does not contain a parseable unit definition'
                        else:
                            if munit == None:
                                print >> sys.stderr, 'file ' + filename + ' does not contain a unit name'
                            elif mfull == None:
                                print >> sys.stderr, 'file ' + filename + ' does not contain the full name of the unit'
                            elif munit in names:
                                print >> sys.stderr, 'file ' + filename + ' contains the name of unit already identified as ' + names[munit][1] + ' in ' + names[munit][2]
                            else:
                                names[munit] = (munit, mfull, filename)
                    except ZkUnitParserError as e:
                        print >> sys.stderr, 'parse error in ' + filename + ' at line ' + str(n)
                    except IOError:
                        print >> sys.stderr, 'IO error reading ' + filename + ' at line ' + str(n)
                    finally:
                        f.close()
                except: 
                    print >> sys.stderr, 'error opening ' + filename
        return names
    
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >> sys.stderr, 'Usage: ZkUnitNames <unit-directory>'
        sys.exit(1)
    elif sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print 'Usage: ZkUnitNames <unit-directory>'
        sys.exit(0)
        
    z = ZkUnitNamesParser()
    names = z.run(sys.argv[1])
    keys = names.keys()
    keys.sort()
    n = 1
    comma = ','
    for k in keys:
        if k == keys[len(keys) - 1]:
            comma = ''
        print '        \'' + names[k][0] + '\': \'' + names[k][1] + '\'' + comma + ' # ' + str(n) + ' ' + names[k][2]   
        n += 1