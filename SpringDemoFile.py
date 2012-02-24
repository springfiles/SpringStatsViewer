#!/usr/bin/python
#
# SpringDemoFile - Class library for parsing Spring Demo Files
#
# The module should be placed in a directory in your Python class path or in the 
# directory of any module that is using it.
#
# Tested on Python 2.7.2, Windows 7 on ZK Games only, YMMV on other platforms and other games based on Spring
#
# There are known issues with games that include bots and/or chickens (i.e. it doesnt work)
# 
# (C) 2011, Rene van 't Veen
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
'''Python script to collection statistics from one or more spring demo files'''

import struct
import re

__author__ = 'rene'
__version__ = '0.1.0'

class PlayerStatistics:
    '''
    Just a struct of player statistics
    '''
    def __init__(self):
        '''
        Initialize all member variables to zero
        
        Note that this will also be the value for any player that leaves the game before the game is over
        '''
        # total mouse movement during game
        self.mousePixels = 0
        # number of mouse clicks during game
        self.mouseClicks = 0
        # number of keypresses during game
        self.keyPresses = 0
        # number of commands given during game
        self.numCommands = 0
        # number of unit commands resulting from keypresses
        self.unitCommands = 0
    def __str__(self):
        '''
        Pretty printing the structure
        '''
        return ( 'KP: ' + str(self.keyPresses) + 
            ', MP: ' + str(self.mousePixels) + 
            ', MC: ' + str(self.mouseClicks) + 
            ', NC: ' + str(self.numCommands) + 
            ', UC: ' + str(self.unitCommands) )
            

class TeamStatistics:
    '''
    Just a struct of team statistics
    '''
    def __init__(self):
        '''
        Initialize all member variables to zero
        '''
        # the game frame ID (use as a measure of time)
        self.frame = 0
        # metal used (to build units or morph)
        self.metalUsed = 0.0
        # energy used (to build units, repair, resurrect, overdrive)
        self.energyUsed = 0.0
        # metal produced
        self.metalProduced = 0.0
        # energy produced
        self.energyProduced = 0.0
        # excess metal (that is, metal for which player has no storage)
        self.metalExcess = 0.0
        # excess energy (in zero-k this is almost always 0 as it is used to overdrive mexes)
        self.energyExcess = 0.0
        # metal received from sharing (either explicit or implicit through metal communism)
        self.metalReceived = 0.0
        # in zero-k energy received is most always zero unless someone sent you some E
        self.energyReceived = 0.0
        # metal sent by sharing (explicit and implicit)
        self.metalSent = 0.0
        # in zero-k energy sent is most always zero unless you explicitly sent some to a teammate
        self.energySent = 0.0
        # damage you dealt (in HP)
        self.damageDealt = 0.0
        # damage you received (in HP)
        self.damageReceived = 0.0
        # number of units produced
        self.unitsProduced = 0
        
        self.unitsDied = 0
        self.unitsReceived = 0
        self.unitsSent = 0
        self.unitsCaptured = 0
        self.unitsOutCaptured = 0
    def __str__(self):
        '''
        Pretty printing
        '''
        return ( str(self.frame) + ' M(Use: ' + str(self.metalUsed) + 
            ' Prod: ' + str(self.metalProduced) +
            ' Excess: ' + str(self.metalExcess) +
            ' Rcv: ' + str(self.metalReceived) + 
            ' Sent: ' + str(self.metalSent) +
            ') E(Use: ' + str(self.energyUsed) + 
            ' Prod: ' + str(self.energyProduced) +
            ' Excess: ' + str(self.energyExcess) +
            ' Rcv: ' + str(self.energyReceived) + 
            ' Sent: ' + str(self.energySent) +
            ') Damage(Done: ' + str(self.damageDealt) +
            ' Received: ' + str(self.damageReceived) + 
            ') Units(Prod: ' + str(self.unitsProduced) +
            ' Dead: ' + str(self.unitsDied) +
            ' Rcv: ' + str(self.unitsReceived) +
            ' Sent: ' + str(self.unitsSent) +
            ' Cap: ' + str(self.unitsCaptured) +
            ' Steal: ' + str(self.unitsOutCaptured) +
            ')' )
            
    

class DemoFileReader:
    '''
    Class whose instance reads Spring demo files
    '''
    def __init__(self, fn, dirname='My Games/Spring/demos/'):
        '''
        Initializer for the class instance. Opens the file named fn (with dirname prepended to it)
        '''
        if dirname == None:
            self.filename = fn
        else:
            self.filename = dirname + fn
        # initialize some data members
        self.file = None
        # see .error(), this member gets set to the last error or warning message
        self._lasterror = None
        
        # major file format
        self.file_version = -1
        # minor file format or header size
        self.headersize = 0
        # engine version
        self.engine_version = None

        # stuff parsed from the demo file header
        self.gameid = None
        self.timestamp = None
        self.scriptsize = 0
        self.demostreamsize = 0
        self.totalgametime = 0
        self.elapsedrealtime = 0
        # the number of players, including spectators
        self.numplayers = 0
        self.playerstatchunksize = 0
        self.playerstatelemsize = 0
        # the number of teams, each spectator is his own team
        self.numteams = 0
        self.teamstatchunksize = 0
        self.teamstatelemsize = 0
        self.teamstatperiod = 0
        self.winningteam = -1
        
        # things we can infer from the header
        self.incomplete = True
        self.exited = False
        self.crashed = False
        
        # the raw startscript
        self.startscript = None
        # real player details inferred from the start script
        self.players = None
        # real team details inferred from the start script
        self.teams = None
        # Game type and map inferred from the start script
        self.gametype = None
        self.map = None
        # player statistics, call method playerstats()
        self.playerstatistics = None
        # team statistics, call method teamstats()
        self.teamstatistics = None
        
        # open the file, if it fails self.file will remain at None
        self.file = open(self.filename, 'rb')
    
    def header(self):
        '''
        Reads the file header and stuffs whatever it read into data members. Do this only once.
        
        Returns False if the header was not parsed successfully, True if it did
        '''
        if self.file == None:
            self._lasterror = 'File ' + self.filename + ' not open.'
            return False
        self.file.seek(0, 0)
        # read the 'fixed' header first
        size = struct.calcsize('=16s2i')
        buffer = self.file.read(size)
        if len(buffer) != size:
            self._lasterror = 'Unable to read fixed header from ' + self.filename
            return False
        values = struct.unpack('=16s2i', buffer)
        # check magic
        self.headervalues = values
        if values[0] != 'spring demofile\0':
            self._lasterror = 'File ' + self.filename + ' is probably not a spring demofile'
            return False
        self.version = values[1]
        # size of the header or minor file version
        self.headersize = values[2]
        if self.version < 5:
            buffer = self.file.read(struct.calcsize('<16s'))
            values = struct.unpack('<16s', buffer)
        else:
            buffer = self.file.read(struct.calcsize('<256s'))
            values = struct.unpack('<256s', buffer)
        # store the engine version in self.engine_version
        position = values[0].find('\0')
        if position == -1:
            self.engine_version = values[0]
        elif position == 0:
            self.engine_version = '' 
        else:
            self.engine_version = values[0][0:position]
        # the next part concerns game ID and various chunk sizes
        size = struct.calcsize('=16sQ12i')
        #if size + len(buffer) != self.headersize:
            #self._lasterror = 'File ' + self.filename + ' has header length ' + str(self.headersize) + ', expected ' + str(size + len(buffer))
            #return False
        buffer = self.file.read(size)
        if len(buffer) != size:
            self._lasterror = 'Unable to read variable header from ' + self.filename
            return False
        values = struct.unpack('=16sQ12i', buffer)
        self.gameid = values[0]
        self.timestamp = values[1]
        self.scriptsize = values[2]
        self.demostreamsize = values[3]
        self.totalgametime = values[4]
        self.elapsedrealtime = values[5]
        self.numplayers = values[6]
        self.playerstatchunksize = values[7]
        self.playerstatelemsize = values[8]
        self.numteams = values[9]
        self.teamstatchunksize = values[10]
        self.teamstatelemsize = values[11]
        self.teamstatperiod = values[12]
        self.winningteam = values[13]
        if self.demostreamsize == 0:
            self._lasterror = 'Spring crashed, recording incomplete'
            self.crashed = True
        else:
            if self.playerstatchunksize == 0 and self.teamstatchunksize == 0:
                # demo recording was stopped before the game ended; player quit spring before the game ended
                self.incomplete = True
                self._lasterror = self.filename + ' is not a complete demo'
            elif self.winningteam == -1:
                # self.filename + ': ' + str(self.numplayers) + ' players in ' + str(self.numteams) + ' teams, nobody won, the game was exited before it could end.'
                self.exited = True
                self.incomplete = False
            else:
                self.incomplete = False
                # print self.filename + ': ' + str(self.numplayers) + ' players in ' + str(self.numteams) + ' teams, team #' + str(self.winningteam) + ' won.'
        return True
    
    def script(self):
        '''
        Read the startscript and parse it.
        
        On success, the raw startscript is returned, on failure None is returned
        '''
        self.startscript = None
        if self.file == None:
            self._lasterror = 'File ' + self.filename + ' not open.'
            return None
        if self.headersize == 0:
            self._lasterror = 'Cannot read start script, read the header first'
            return None
        if self.scriptsize == 0:
            self._lasterror = 'Cannot read start script, none is recorded'
            return None
        self.file.seek(self.headersize, 0)
        buffer = self.file.read(self.scriptsize)
        if len(buffer) != self.scriptsize:
            self._lasterror = 'File ' + self.filename + ' contains an incomplete (broken) start script'
            return None
        self.startscript = buffer
        # now parse the start script, begin by initializing a root dictionary
        self.settings = dict()
        level = 0
        dictstack = list()
        currentdict = self.settings
        dictstack.append(currentdict)
        # precompile some regular expressions
        hash = re.compile(r'^\s*\[\s*(\w+)\s*\]\s*$')
        opening = re.compile(r'^\s*\{\s*$')
        closing = re.compile(r'^\s*\}\s*$')
        simple = re.compile(r'^\s*(\w+)\s*=(.*?);\s*$')
        empty = re.compile(r'^\s*$')
        position = 0
        expectedopen = False
        errors = 0
        currentline = 0
        self._lasterror = ''
        while position < len(self.startscript):
            nextposition = self.startscript.find('\n',position)
            if nextposition == -1:
                position = len(self.startscript)
                continue
            line = self.startscript[position:nextposition]
            position = nextposition + 1
            currentline = currentline + 1
            test = hash.match(line)
            if test != None:
                name = test.group(1)
                if name in currentdict:
                    self._lasterror += 'Duplicate dictionary entry ' + name + ' in start script at line ' + str(currentline) + '\n'
                    errors = errors + 1
                else:
                    newdict = dict()
                    currentdict[name] = newdict
                expectedopen = True
                lastdict = name
                continue
            test = opening.match(line)
            if test != None:
                if not expectedopen:
                    self._lasterror += 'No { expected in start script at line ' + str(currentline) + '\n'
                    errors = errors + 1
                    continue
                expectedopen = False
                level = level + 1
                dictstack.append(currentdict[lastdict])
                currentdict = currentdict[lastdict]
                # print 'Pushed ' + lastdict + ' at level ' + str(level) + '[' + str(len(dictstack)) + ']'
                continue
            test = empty.match(line)
            if test != None:
                continue
            test = closing.match(line)
            if test != None:
                if expectedopen:
                    self._lasterror += 'Expected opening { in start script at line ' + str(currentline) + '\n'
                    errors = errors + 1
                    continue
                level = level - 1
                if level < 0:
                    self._lasterror += 'Unmatched } in start script at line ' + str(currentline) + '\n'
                    errors = errors + 1
                    continue
                dictstack.pop()
                currentdict = dictstack[-1]
                # print 'Popped to level ' + str(level) + '[' + str(len(dictstack)) + ']'
                continue
            test = simple.match(line)
            if test != None:
                if expectedopen:
                    self._lasterror += 'Expected opening { in start script at line ' + str(currentline) + '\n'
                    errors = errors + 1
                    continue
                name = test.group(1)
                if name in currentdict:
                    self._lasterror += 'Duplicate dictionary entry ' + name + ' in start script at line ' + str(currentline) + '\n'
                    errors = errors + 1
                currentdict[name] = test.group(2).strip()
                continue
            if len(line) < 70:
                self._lasterror += 'No match: '+ line + '\n'
            else:
                self._lasterror += 'No match: ' + line[0:60] + ' ... ' + '\n'
            errors = errors + 1

        if level != 0: 
            self._lasterror = 'Unmatched { at EOF in start script' + '\n'
            errors = errors + 1

        if errors != 0:
            self._lasterror += str(errors) + ' error(s) while parsing start script in file ' + self.filename
            return None
        self._lasterror = None
        
        if 'game' not in self.settings or type(self.settings['game']) != type(dict()):
            self._lasterror = 'Game settings not present or not a dictionary'
            return None
        
        if 'gametype' in self.settings['game'] and type(self.settings['game']['gametype']) == type(''):
            self.gametype = self.settings['game']['gametype']
        else:
            self.gametype = 'Unknown'
        
        if 'mapname' in self.settings['game'] and type(self.settings['game']['mapname']) == type(''):
            self.map = self.settings['game']['mapname']
        else:
            self.map = 'Unknown map'
        
        # find out who the players are
        playerseq = 0
        self.players = list()
        while 'player' + str(playerseq) in self.settings['game']:
            dictname = 'player' + str(playerseq)
            playerdict = self.settings['game'][dictname]
            if type(playerdict) != type(dict()):
                self._lasterror = 'Entry for ' + dictname + ' is not a dictionary'
                return None
            if 'name' not in playerdict or 'spectator' not in playerdict:
                self._lasterror = 'Game settings incomplete for ' + dictname
                return None
            playername = playerdict['name']
            spectator = playerdict['spectator']
            if spectator == '0':
                # this person is playing
                if 'team' not in playerdict:
                    self._lasterror = 'Game settings incomplete for ' + dictname + ', active player ' + playername
                    return None
                team = int(playerdict['team'])
                if 'team' + str(team) not in self.settings['game']:
                    self._lasterror = 'Unable to find team for ' + dictname + ', active player ' + playername
                    return None
                teamdict = self.settings['game']['team' + str(team)]
                if type(teamdict) != type(dict()):
                    self._lasterror = 'Team entry for active player ' + dictname + ' is not a dictionary'
                    return None
                if 'allyteam' not in teamdict:
                    self._lasterror = 'Unable to find the real team for ' + dictname + ', active player ' + playername
                    return None
                realteam = int(teamdict['allyteam'])
                # note that the value of the teamleader entry in the teamdict should be the same as the player sequence number
                self.players.append((playername, realteam, team, dictname))
            else:
                self.players.append(None)
                
            playerseq = playerseq + 1
            
        # find out who the teams are
        teamseq = 0
        self.teams = list()
        while 'team' + str(teamseq) in self.settings['game']:
            dictname = 'team' + str(teamseq)
            teamdict = self.settings['game'][dictname]
            if type(teamdict) != type(dict()):
                self._lasterror = 'Entry for ' + dictname + ' is not a dictionary'
                return None
            if 'teamleader' not in teamdict or 'allyteam' not in teamdict:
                self._lasterror = 'Game settings incomplete for ' + dictname
                return None
            teamleader = int(teamdict['teamleader'])
            realteam = int(teamdict['allyteam'])
            if teamleader < 0 or teamleader >= len(self.players):
                self._lasterror = 'Invalid teamleader for team ' + dictname
                return None
            if self.players[teamleader] == None:
                self._lasterror = 'Teamleader of team ' + dictname + ' is spectating?'
                return None
            self.teams.append((self.players[teamleader][0], realteam, dictname))
                
            teamseq = teamseq + 1
        if not self.incomplete:
            if len(self.teams) != self.numteams:
                self._lasterror = 'Number of teams in header does not correspond with number of teams in start script'
                return None
                
        return self.startscript
        
    def playerstats(self):
        '''
        Attempts to retrieve the player statistics from the file.
        
        Returns None on failure, a dictionary keyed to real player name otherwise. The value of this dictionary is a tuple of the player stat entries
        '''
        if self.file == None:
            self._lasterror = 'File ' + self.filename + ' not open.'
            return None
        if self.headersize == 0:
            self._lasterror = 'Cannot read player stats, read the header first'
            return None
        if self.players == None:
            self._lasterror = 'Cannot comprehend player stats, read the start script first'
            return None
        if self.incomplete:
            self._lasterror = 'File ' + self.filename + ' is an incomplete demo, cannot read player statistics'
            return None
        if self.numplayers == 0 or self.playerstatchunksize == 0:
            self._lasterror = 'File ' + self.filename + ' does not contain player statistics'
            return None
        size = struct.calcsize('=5i')
        if size != self.playerstatelemsize:
            self._lasterror = 'File ' + self.filename + ' contains player statistics in an unknown format'
            return None
        where = self.headersize + self.scriptsize + self.demostreamsize
        self.file.seek(where,0)
        buffer = self.file.read(self.playerstatchunksize)
        if len(buffer) != self.playerstatchunksize:
            self._lasterror = 'File ' + self.filename + ', player statistics truncated'
            return None
        offset = 0
        self.playerstatistics = dict()
        for x in self.players:
            if x != None:
                # if a player quits (or is kicked) before the end of the game then the values are recorded as 0, 0, 0, 0, 0
                values = struct.unpack('=5i', buffer[offset:offset + self.playerstatelemsize])
                p = PlayerStatistics()
                p.mousePixels = values[0]
                p.mouseClicks = values[1]
                p.keyPresses = values[2]
                p.numCommands = values[3]
                p.unitCommands = values[4]
                self.playerstatistics[x[0]] = p
            offset = offset + self.playerstatelemsize
        return self.playerstatistics
        
    def teamstats(self):
        '''
        Attempts to retrieve the team statistics from the file.
        
        Returns None on failure, a dictionary keyed to real player name otherwise. The value of this dictionary is a list of the
        '''
        if self.file == None:
            self._lasterror = 'File ' + self.filename + ' not open.'
            return None
        if self.headersize == 0:
            self._lasterror = 'Cannot read teams stats, read the header first'
            return None
        if self.players == None:
            self._lasterror = 'Cannot comprehend teams stats, read the start script first'
            return None
        if self.incomplete:
            self._lasterror = 'File ' + self.filename + ' is an incomplete demo, cannot team player statistics'
            return None
        if self.numteams == 0 or self.teamstatchunksize == 0:
            self._lasterror = 'File ' + self.filename + ' does not contain team statistics'
            return None
        size = struct.calcsize('=i12f7i')
        if size != self.teamstatelemsize:
            self._lasterror = 'File ' + self.filename + ' contains team statistics in an unknown format'
            return None
        where = self.headersize + self.scriptsize + self.demostreamsize + self.playerstatchunksize
        self.file.seek(where,0)
        buffer = self.file.read(self.teamstatchunksize)
        if len(buffer) != self.teamstatchunksize:
            self._lasterror = 'File ' + self.filename + ', team statistics truncated'
            return None
        offset = 0
        # first there is an array of self.numteams long of integers, giving the number of statistics for each team
        xsize = 0
        sizes = list()
        for x in self.teams:
            size = struct.calcsize('=i')
            values = struct.unpack('=i', buffer[offset:offset + size])
            sizes.append(values[0])
            # print x[0] + ' has ' + str(values[0]) + ' statistic records'
            offset = offset + size
            xsize = xsize + size + values[0] * self.teamstatelemsize
        # check for consistency
        if xsize != self.teamstatchunksize:
            self._lasterror = 'Calculated (' + str(xsize) + ') and real (' + str(self.teamchunksize) + ') team statistic chunk size differ'
            return None
        self.teamstatistics = dict()
        team = 0
        for x in self.teams:
            teamstat = list()
            for n in xrange(0,sizes[team]):
                values = struct.unpack('=i12f7i' , buffer[offset:offset + self.teamstatelemsize])
                t = TeamStatistics()
                t.frame = values[0]
                t.metalUsed = values[1]
                t.energyUsed = values[2]
                t.metalProduced = values[3]
                t.energyProduced = values[4]
                t.metalExcess = values[5]
                t.energyExcess = values[6]
                t.metalReceived = values[7]
                t.energyReceived = values[8]
                t.metalSent = values[9]
                t.energySent = values[10]
                t.damageDealt = values[11]
                t.damageReceived = values[12]
                t.unitsProduced = values[13]
                t.unitsDied = values[14]
                t.unitsReceived = values[15]
                t.unitsSent = values[16]
                t.unitsCaptured = values[17]
                t.unitsOutCaptured = values[18]
                t.unitsDied = values[19]
                teamstat.append(t)
                offset = offset + self.teamstatelemsize
            self.teamstatistics[x[0]] = teamstat
        return self.teamstatistics
    def errormessage(self):
        '''
        Simple accessor to get as the last error message, returns None if there was no error
        '''
        return self._lasterror
        
    def close(self):
        '''
        Closes the input file, most other operation will now fail silently
        '''
        self.file.close()
        self.file = None
        
if __name__ == '__main__':
    print 'This is the Spring Demo File class library, it should not be executed directly.'
    print 'Although it might have included a self-test here'

        
        
