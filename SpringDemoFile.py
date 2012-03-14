#!/usr/bin/python
#
# SpringDemoFile - Class library for parsing Spring Demo Files
#
# The module should be placed in a directory in your Python class path or in the 
# directory of any module that is using it.
#
# Tested on Python 2.7.2, Windows 7 on ZK Games only, YMMV on other platforms and other games based on Spring
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
'''Python script to collect statistics from one or more spring demo files'''

import struct
import re

__author__ = 'rene'
__version__ = '0.2.1'

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
        # number of unit commands resulting from key presses and/or mouse clicks
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
        self.unitsKilled = 0
    def __str__(self):
        '''
        Pretty printing
        '''
        s = ( str(self.frame) + ' M(Use: ' + str(self.metalUsed) + 
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
            ' Steal: ' + str(self.unitsOutCaptured) )
        if hasattr(self,'unitsKilled'):
            s += ' Killed:' + str(self.unitsKilled)
        s += ')'
        return s
            
class DemoRecord:
    '''
    Class that represents a single record in the demo stream
    '''
    # record type, this is data[0] (see BaseNetProtocol.h)
    KEYFRAME = 1
    NEWFRAME = 2
    QUIT = 3
    STARTPLAYING = 4
    SETPLAYERNUM = 5
    PLAYERNAME = 6
    CHAT = 7
    RANDSEED = 8
    GAMEID = 9
    PATH_CHECKSUM = 10
    COMMAND = 11
    SELECT = 12
    PAUSE = 13
    AICOMMAND = 14
    AICOMMANDS = 15
    AISHARE = 16
    USER_SPEED = 19
    INTERNAL_SPEED = 20
    CPU_USAGE = 21
    DIRECT_CONTROL = 22
    DC_UPDATE = 23
    SHARE = 26
    SETSHARE = 27
    SENDPLAYERSTAT = 28
    PLAYERSTAT = 29
    GAMEOVER = 30
    MAPDRAW = 31
    SYNCRESPONSE = 33
    SYSTEMMSG = 35
    STARTPOS = 36
    PLAYERINFO = 38
    PLAYERLEFT = 39
    LUAMSG = 50
    TEAM = 51
    GAMEDATA = 52
    ALLIANCE = 53
    CCOMMAND = 54
    CUSTOM_DATA = 55
    TEAMSTAT = 60
    ATTEMPT_CONNECT = 65
    AI_CREATED = 70
    AI_STATE_CHANGED = 71
    REQUEST_TEAMSTAT = 72
    CREATE_NEWPLAYER = 75
    # Forged records have negative numbers
    # ZK SPRINGIE records are really chat messages
    ZK_DAMAGE = -1
    ZK_UNIT = -2
    ZK_AWARD = -3
    # for ZK springie records we dont know about
    ZK_OTHER = -4
    
    # Chat destinations (from ChatMessage.h)
    CHAT_ALLIES = 252
    CHAT_SPECTATORS = 253
    CHAT_EVERYONE = 254
    # not defined in ChatMessage.h but present in demo files
    CHAT_HOST = 255
    
    # helper constants
    __SPRINGIE = 4 + len('SPRINGIE:')
    __MODSTATSDMG = __SPRINGIE + len('stats,dmg,')
    __MODSTATSUNIT = __SPRINGIE + len('stats,unit,')
    __AWARD = __SPRINGIE + len('award,')
    
    def __init__(self):
        '''
        Constructor, initializes all members to default values
        '''
        self.gametime = 0.0
        self.data = bytearray()
    def type(self):
        '''
        Returns the type of record or None if the DemoRecord is not mapped to data
        '''
        if len(self.data) > 0:
            v = ord(self.data[0])
            if v == self.CHAT:
                if ord(self.data[3]) == self.CHAT_HOST:
                    if self.data[4:self.__SPRINGIE] == 'SPRINGIE:':
                        if self.data[self.__SPRINGIE:self.__MODSTATSDMG] == 'stats,dmg,':
                            return self.ZK_DAMAGE
                        elif self.data[self.__SPRINGIE:self.__MODSTATSUNIT] == 'stats,unit,':
                            return self.ZK_UNIT
                        elif self.data[self.__SPRINGIE:self.__AWARD] == 'award,':
                            return self.ZK_AWARD
                        else:
                            # examples include teams and plist
                            return self.ZK_OTHER
            return v
        return None
    def player(self):
        '''
        Returns the initiating player number for messages that have an initiating player or None for those messages that do not
        have it, or if the record cannot be parsed
        '''
        t = self.type()
        if t == None:
            return None
        elif t == self.SETPLAYERNUM:
            return ord(self.data[1])
        elif t == self.PLAYERNAME:
            return ord(self.data[2])
        elif t == self.CHAT or t == self.ZK_DAMAGE or t == self.ZK_UNIT or t == self.ZK_AWARD or t == self.ZK_OTHER:
            return ord(self.data[2])
        elif t == self.PATH_CHECKSUM:
            return ord(self.data[1])
        elif t == self.COMMAND:
            return ord(self.data[2])
        elif t == self.SELECT:
            return ord(self.data[2])
        elif t == self.PAUSE:
            return ord(self.data[1])
        elif t == self.AICOMMAND:
            return ord(self.data[2])
        elif t == self.AICOMMANDS:
            return ord(self.data[2])
        elif t == self.AISHARE:
            return ord(self.data[2])
        elif t == self.USER_SPEED:
            return ord(self.data[1])
        elif t == self.DIRECT_CONTROL:
            return ord(self.data[1])
        elif t == self.DC_UPDATE:
            return ord(self.data[1])
        elif t == self.SHARE:
            return ord(self.data[1])
        elif t == self.SETSHARE:
            return ord(self.data[1])
        elif t == self.PLAYERSTAT:
            return ord(self.data[1])
        elif t == self.MAPDRAW:
            return ord(self.data[2])
        elif t == self.SYNCRESPONSE:
            return ord(self.data[1])
        elif t == self.SYSTEMMSG:
            # appears meaningless, it is always 0
            return ord(self.data[2])
        elif t == self.STARTPOS:
            return ord(self.data[1])
        elif t == self.PLAYERINFO:
            return ord(self.data[1])
        elif t == self.PLAYERLEFT:
            return ord(self.data[1])
        elif t == self.LUAMSG:
            return ord(self.data[3])
        elif t == self.TEAM:
            return ord(self.data[1])
        elif t == self.ALLIANCE:
            return ord(self.data[1])
        elif t == self.CUSTOM_DATA:
            return ord(self.data[1])
        elif t == self.AI_CREATED:
            return ord(self.data[2])
        elif t == self.AI_STATE_CHANGED:
            return ord(self.data[1])
        elif t == self.CREATE_NEWPLAYER:
            # appears meaningless, it is always 0, the player number is assigned by SETPLAYERNUM
            return ord(self.data[2])
        elif t == self.SETSHARE:
            return ord(self.data[1])
        else:
            return None
        
    def destination(self):
        '''
        Returns the destination player number for messages that have an destination player or None for those messages that do not
        have it, or if the record cannot be parsed
        '''
        t = self.type()
        if t == None:
            return None
        elif t == self.CHAT:
            return ord(self.data[3])
        else:
            return None
        
    def text(self):
        '''
        Returns the text of messages that have text or None if the message has no text
        '''
        t = self.type()
        if t == None:
            return None
        elif t == self.QUIT:
            # apparently there is a 0 byte in front of the label
            s = self.data[3:]
        elif t == self.PLAYERNAME:
            s = self.data[3:]
        elif t == self.CHAT:
            s = self.data[4:]
        elif t == self.MAPDRAW and len(self.data) > 9 and ord(self.data[3]) == 0:
            # apparently there is a 0 byte in front of the label
            s = self.data[9:]
        elif t == self.SYSTEMMSG:
            # apparently, there is a 255 byte in front of the label
            s = self.data[4:]
        elif t == self.AI_CREATED:
            # untested
            s = self.data[8:]
        elif t == self.CREATE_NEWPLAYER:
            s = self.data[6:]
        elif t == self.ZK_DAMAGE:
            s = self.data[self.__MODSTATSDMG:]
        elif t == self.ZK_UNIT:
            s = self.data[self.__MODSTATSUNIT:]
        elif t == self.ZK_AWARD:
            s = self.data[self.__AWARD:]
        elif t == self.ZK_OTHER:
            s = self.data[self.__SPRINGIE:]
        else:
            return None
        # get rid of any terminating null characters
        while len(s) > 1 and s[-1] == '\0':
            s = s[0:-1]
        if s == '\0':
            s = None
        return s
    
    def spectator(self):
        '''
        Returns the value of the spectator field in the createnewplayer record only or None.
        '''
        t = self.type()
        if t == None:
            return None
        elif t == self.CREATE_NEWPLAYER:
            return ord(self.data[3])
        else:
            return None
        
    def reason(self):
        '''
        Returns the value of the reason or type field in the PAUSED and PLAYERLEFT record only or None.
        '''
        t = self.type()
        if t == None:
            return None
        elif t == self.PAUSE:
            return ord(self.data[2])
        elif t == self.PLAYERLEFT:
            return ord(self.data[2])
        else:
            return None
        
    def team(self):
        '''
        Returns the value of the team field in the records that have such a field or None.
        '''
        t = self.type()
        if t == None:
            return None
        elif t == self.CREATE_NEWPLAYER:
            return ord(self.data[4])
        else:
            return None
        
    def __str__(self):
        '''
        Pretty printing
        '''
        v = divmod(self.gametime, 60.0)
        w = divmod(v[0], 60.0)
        if w[0] == 0.0:
            s = '%.0fm%04.1fs' % ( w[1], v[1] )
        else:
            s = '%.0fh%02.0fm%04.1fs' % ( w[0], w[1], v[1] )
        s += ':' + repr(bytearray(self.data))
        return s
    
class DemoFileReader:
    '''
    Class whose instance reads Spring demo files
    '''
    zkunitnames = {
        'amgeo': 'Moho Geothermal Powerplant', # 1 amgeo.lua
        'amphaa': 'Angler', # 2 amphaa.lua
        'amphassault': 'Grizzly', # 3 amphassault.lua
        'amphcon': 'Clam', # 4 amphcon.lua
        'amphfloater': 'Buoy', # 5 amphfloater.lua
        'amphraider': 'Grebe', # 6 amphraider.lua
        'amphraider2': 'Archer', # 7 amphraider2.lua
        'amphraider3': 'Duck', # 8 amphraider3.lua
        'amphriot': 'Scallop', # 9 amphriot.lua
        'amphtele': 'Djinn', # 10 amphtele.lua
        'arm_spider': 'Weaver', # 11 arm_spider.lua
        'arm_venom': 'Venom', # 12 arm_venom.lua
        'armaak': 'Archangel', # 13 armaak.lua
        'armamd': 'Protector', # 14 armamd.lua
        'armanni': 'Annihilator', # 15 armanni.lua
        'armarad': 'Advanced Radar Tower', # 16 armarad.lua
        'armartic': 'Faraday', # 17 armartic.lua
        'armasp': 'Air Repair/Rearm Pad', # 18 armasp.lua
        'armbanth': 'Bantha', # 19 armbanth.lua
        'armbrawl': 'Brawler', # 20 armbrawl.lua
        'armbrtha': 'Big Bertha', # 21 armbrtha.lua
        'armca': 'Crane', # 22 armca.lua
        'armcarry': 'Reef', # 23 armcarry.lua
        'armcir': 'Chainsaw', # 24 armcir.lua
        'armcom1': 'Strike Commander', # 25 armcom1.lua
        'armcomdgun': 'Ultimatum', # 26 armcomdgun.lua
        'armcrabe': 'Crabe', # 27 armcrabe.lua
        'armcsa': 'Athena', # 28 armcsa.lua
        'armcybr': 'Licho', # 29 armcybr.lua
        'armdeva': 'Stardust', # 30 armdeva.lua
        'armestor': 'Energy Transmission Pylon', # 31 armestor.lua
        'armflea': 'Flea', # 32 armflea.lua
        'armfus': 'Fusion Reactor', # 33 armfus.lua
        'armham': 'Hammer', # 34 armham.lua
        'armjamt': 'Sneaky Pete', # 35 armjamt.lua
        'armjeth': 'Jethro', # 36 armjeth.lua
        'armkam': 'Banshee', # 37 armkam.lua
        'armmanni': 'Penetrator', # 38 armmanni.lua
        'armmerl': 'Merl', # 39 armmerl.lua
        'armmstor': 'Storage', # 40 armmstor.lua
        'armnanotc': 'Caretaker', # 41 armnanotc.lua
        'armorco': 'Detriment', # 42 armorco.lua
        'armpb': 'Gauss', # 43 armpb.lua
        'armpt': 'Skeeter', # 44 armpt.lua
        'armpw': 'Glaive', # 45 armpw.lua
        'armraven': 'Catapult', # 46 armraven.lua
        'armraz': 'Razorback', # 47 armraz.lua
        'armrectr': 'Rector', # 48 armrectr.lua
        'armrock': 'Rocko', # 49 armrock.lua
        'armroy': 'Crusader', # 50 armroy.lua
        'armsnipe': 'Sharpshooter', # 51 armsnipe.lua
        'armsolar': 'Solar Collector', # 52 armsolar.lua
        'armsonar': 'Sonar Station', # 53 armsonar.lua
        'armsptk': 'Recluse', # 54 armsptk.lua
        'armspy': 'Infiltrator', # 55 armspy.lua
        'armstiletto_laser': 'Stiletto', # 56 armstiletto_laser.lua
        'armtboat': 'Surfboard', # 57 armtboat.lua
        'armtick': 'Tick', # 58 armtick.lua
        'armwar': 'Warrior', # 59 armwar.lua
        'armwin': 'Wind/Tidal Generator', # 60 armwin.lua
        'armzeus': 'Zeus', # 61 armzeus.lua
        'assaultcruiser': 'Vanquisher', # 62 assaultcruiser.lua
        'asteroid': 'Asteroid', # 63 asteroid.lua
        'attackdrone': 'Firefly', # 64 attackdrone.lua
        'blackdawn': 'Black Dawn', # 65 blackdawn.lua
        'bladew': 'Gnat', # 66 bladew.lua
        'blastwing': 'Blastwing', # 67 blastwing.lua
        'cafus': 'Singularity Reactor', # 68 cafus.lua
        'capturecar': 'Dominatrix', # 69 capturecar.lua
        'carrydrone': 'Gull', # 70 carrydrone.lua
        'chicken': 'Chicken', # 71 chicken.lua
        'chicken_blimpy': 'Blimpy', # 72 chicken_blimpy.lua
        'chicken_digger': 'Digger', # 73 chicken_digger.lua
        'chicken_digger_b': 'Digger (burrowed)', # 74 chicken_digger_b.lua
        'chicken_dodo': 'Dodo', # 75 chicken_dodo.lua
        'chicken_dragon': 'White Dragon', # 76 chicken_dragon.lua
        'chicken_drone': 'Drone', # 77 chicken_drone.lua
        'chicken_drone_starter': 'Drone', # 78 chicken_drone_starter.lua
        'chicken_leaper': 'Leaper', # 79 chicken_leaper.lua
        'chicken_listener': 'Listener', # 80 chicken_listener.lua
        'chicken_listener_b': 'Listener (burrowed)', # 81 chicken_listener_b.lua
        'chicken_pigeon': 'Pigeon', # 82 chicken_pigeon.lua
        'chicken_roc': 'Roc', # 83 chicken_roc.lua
        'chicken_shield': 'Toad', # 84 chicken_shield.lua
        'chicken_spidermonkey': 'Spidermonkey', # 85 chicken_spidermonkey.lua
        'chicken_sporeshooter': 'Sporeshooter', # 86 chicken_sporeshooter.lua
        'chicken_tiamat': 'Tiamat', # 87 chicken_tiamat.lua
        'chickena': 'Cockatrice', # 88 chickena.lua
        'chickenblobber': 'Blobber', # 89 chickenblobber.lua
        'chickenbroodqueen': 'Chicken Brood Queen', # 90 chickenbroodqueen.lua
        'chickenc': 'Basilisk', # 91 chickenc.lua
        'chickend': 'Chicken Tube', # 92 chickend.lua
        'chickenf': 'Talon', # 93 chickenf.lua
        'chickenflyerqueen': 'Chicken Flyer Queen', # 94 chickenflyerqueen.lua
        'chickenlandqueen': 'Chicken Queen', # 95 chickenlandqueen.lua
        'chickenq': 'Chicken Queen', # 96 chickenq.lua
        'chickenr': 'Lobber', # 97 chickenr.lua
        'chickens': 'Spiker', # 98 chickens.lua
        'chickenspire': 'Chicken Spire', # 99 chickenspire.lua
        'chickenwurm': 'Wurm', # 100 chickenwurm.lua
        'commrecon1': 'Recon Commander', # 101 commrecon1.lua
        'commsupport1': 'Support Commander', # 102 commsupport1.lua
        'coracv': 'Welder', # 103 coracv.lua
        'corak': 'Bandit', # 104 corak.lua
        'corape': 'Rapier', # 105 corape.lua
        'corarch': 'Shredder', # 106 corarch.lua
        'corawac': 'Vulture', # 107 corawac.lua
        'corbats': 'Warlord', # 108 corbats.lua
        'corbhmth': 'Behemoth', # 109 corbhmth.lua
        'corbtrans': 'Vindicator', # 110 corbtrans.lua
        'corcan': 'Jack', # 111 corcan.lua
        'corch': 'Quill', # 112 corch.lua
        'corclog': 'Dirtbag', # 113 corclog.lua
        'corcom1': 'Battle Commander', # 114 corcom1.lua
        'corcrash': 'Vandal', # 115 corcrash.lua
        'corcrw': 'Krow', # 116 corcrw.lua
        'corcs': 'Mariner', # 117 corcs.lua
        'cordoom': 'Doomsday Machine', # 118 cordoom.lua
        'core_spectre': 'Aspis', # 119 core_spectre.lua
        'coresupp': 'Typhoon', # 120 coresupp.lua
        'corfast': 'Freaker', # 121 corfast.lua
        'corfav': 'Dart', # 122 corfav.lua
        'corflak': 'Cobra', # 123 corflak.lua
        'corgarp': 'Wolverine', # 124 corgarp.lua
        'corgator': 'Scorcher', # 125 corgator.lua
        'corgol': 'Goliath', # 126 corgol.lua
        'corgrav': 'Newton', # 127 corgrav.lua
        'corhlt': 'Stinger', # 128 corhlt.lua
        'corhurc2': 'Phoenix', # 129 corhurc2.lua
        'corjamt': 'Aegis', # 130 corjamt.lua
        'corlevlr': 'Leveler', # 131 corlevlr.lua
        'corllt': 'Lotus', # 132 corllt.lua
        'cormak': 'Outlaw', # 133 cormak.lua
        'cormart': 'Pillager', # 134 cormart.lua
        'cormex': 'Metal Extractor', # 135 cormex.lua
        'cormist': 'Slasher', # 136 cormist.lua
        'cornecro': 'Convict', # 137 cornecro.lua
        'corned': 'Mason', # 138 corned.lua
        'cornukesub': 'Leviathan', # 139 cornukesub.lua
        'corpre': 'Scorcher', # 140 corpre.lua
        'corpyro': 'Pyro', # 141 corpyro.lua
        'corpyro2': 'Pyro', # 142 corpyro2.lua
        'corrad': 'Radar Tower', # 143 corrad.lua
        'corraid': 'Ravager', # 144 corraid.lua
        'corrazor': 'Razor\'s Kiss', # 145 corrazor.lua
        'correap': 'Reaper', # 146 correap.lua
        'corrl': 'Defender', # 147 corrl.lua
        'corroach': 'Roach', # 148 corroach.lua
        'corroy': 'Enforcer', # 149 corroy.lua
        'corsent': 'Copperhead', # 150 corsent.lua
        'corsh': 'Scrubber', # 151 corsh.lua
        'corshad': 'Shadow', # 152 corshad.lua
        'corsilo': 'Silencer', # 153 corsilo.lua
        'corsktl': 'Skuttle', # 154 corsktl.lua
        'corstorm': 'Rogue', # 155 corstorm.lua
        'corsub': 'Snake', # 156 corsub.lua
        'corsumo': 'Sumo', # 157 corsumo.lua
        'corsy': 'Shipyard', # 158 corsy.lua
        'corthud': 'Thug', # 159 corthud.lua
        'cortl': 'Urchin', # 160 cortl.lua
        'corvalk': 'Valkyrie', # 161 corvalk.lua
        'corvamp': 'Vamp', # 162 corvamp.lua
        'corvrad': 'Informant', # 163 corvrad.lua
        'cremcom1': 'Strike Commander', # 164 cremcom1.lua
        'dante': 'Dante', # 165 dante.lua
        'dclship': 'Hunter', # 166 dclship.lua
        'destroyer': 'Daimyo', # 167 destroyer.lua
        'empmissile': 'Shockley', # 168 empmissile.lua
        'factoryamph': 'Amphibious Operations Plant', # 169 factoryamph.lua
        'factorycloak': 'Cloaky Bot Factory', # 170 factorycloak.lua
        'factorygunship': 'Gunship Plant', # 171 factorygunship.lua
        'factoryhover': 'Hovercraft Platform', # 172 factoryhover.lua
        'factoryjump': 'Jumpjet/Specialist Plant', # 173 factoryjump.lua
        'factoryplane': 'Airplane Plant', # 174 factoryplane.lua
        'factoryshield': 'Shield Bot Factory', # 175 factoryshield.lua
        'factoryspider': 'Spider Factory', # 176 factoryspider.lua
        'factorytank': 'Heavy Tank Factory', # 177 factorytank.lua
        'factoryveh': 'Light Vehicle Factory', # 178 factoryveh.lua
        'fakeunit': 'Fake radar signal', # 179 fakeunit.lua
        'fakeunit_aatarget': 'Fake AA target', # 180 fakeunit_aatarget.lua
        'fighter': 'Avenger', # 181 fighter.lua
        'firebug': 'firebug', # 182 firebug.lua
        'firewalker': 'Firewalker', # 183 firewalker.lua
        'funnelweb': 'Funnelweb', # 184 funnelweb.lua
        'geo': 'Geothermal Powerplant', # 185 geo.lua
        'gorg': 'Jugglenaut', # 186 gorg.lua
        'hoveraa': 'Flail', # 187 hoveraa.lua
        'hoverassault': 'Halberd', # 188 hoverassault.lua
        'hoverminer': 'Dampener', # 189 hoverminer.lua
        'hoverriot': 'Mace', # 190 hoverriot.lua
        'hovershotgun': 'Punisher', # 191 hovershotgun.lua
        'hoverskirm': 'Blischpt', # 192 hoverskirm.lua
        'logkoda': 'Kodachi', # 193 logkoda.lua
        'mahlazer': 'Starlight', # 194 mahlazer.lua
        'missilesilo': 'Missile Silo', # 195 missilesilo.lua
        'missiletower': 'Hacksaw', # 196 missiletower.lua
        'napalmmissile': 'Inferno', # 197 napalmmissile.lua
        'neebcomm': 'Neeb Comm', # 198 neebcomm.lua
        'nest': 'Nest', # 199 nest.lua
        'nsaclash': 'Scalpel', # 200 nsaclash.lua
        'panther': 'Panther', # 201 panther.lua
        'puppy': 'Puppy', # 202 puppy.lua
        'pw_generic': 'Generic Neutral Structure', # 203 pw_generic.lua
        'railgunturret': 'Splinter', # 204 railgunturret.lua
        'raveparty': 'Disco Rave Party', # 205 raveparty.lua
        'roost': 'Roost', # 206 roost.lua
        'roostfac': 'Roost', # 207 roostfac.lua
        'scorpion': 'Scorpion', # 208 scorpion.lua
        'screamer': 'Screamer', # 209 screamer.lua
        'seismic': 'Quake', # 210 seismic.lua
        'serpent': 'Serpent', # 211 serpent.lua
        'shieldarty': 'Racketeer', # 212 shieldarty.lua
        'shieldfelon': 'Felon', # 213 shieldfelon.lua
        'slowmort': 'Moderator', # 214 slowmort.lua
        'spherecloaker': 'Eraser', # 215 spherecloaker.lua
        'spherepole': 'Scythe', # 216 spherepole.lua
        'spideraa': 'Tarantula', # 217 spideraa.lua
        'spiderassault': 'Hermit', # 218 spiderassault.lua
        'striderhub': 'Strider Hub', # 219 striderhub.lua
        'subscout': 'Lancelet', # 220 subscout.lua
        'tacnuke': 'Eos', # 221 tacnuke.lua
        'tawf114': 'Banisher', # 222 tawf114.lua
        'tele_beacon': 'Lighthouse', # 223 tele_beacon.lua
        'terraunit': 'Terraform', # 224 terraunit.lua
        'thicket': 'Thicket', # 225 thicket.lua
        'tiptest': 'TIP test unit', # 226 tiptest.lua
        'trem': 'Tremor', # 227 trem.lua
        'wolverine_mine': 'Claw', # 228 wolverine_mine.lua
        'zenith': 'Zenith' # 229 zenith.lua
        }
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
        # file version 5 changed the definition, it is now a list
        self.winningteamchunksize = 0
        self.winningteam = list()
        
        # things we can infer from the header
        self.incomplete = True
        self.exited = False
        self.crashed = False
        
        # the raw startscript
        self.startscript = None
        # real player details inferred from the start script
        # the data structure is a list of tuples, with each tuple:
        # 1. the player name
        # 2. the actual team (allyteam) the player belongs to or -1 for spectators
        # 3. the team to which the player is mapped or -1 for spectators
        # 4. the key in the start script dictionary mapping to the player
        self.players = None
        # dictionary mapping player numbers to player names
        self.playernames = None
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
        if values[1] != 4 and values[1] != 5:
            self._lasterror = 'File ' + self.filename + ' contains a version ' + str(values[1]) + ' other than 4'
            return False
        self.version = values[1]
        # size of the header or minor file version
        self.headersize = values[2]
        if self.version == 5:
            size = struct.calcsize('256s')
        else:
            # version 4
            size = struct.calcsize('16s')
        nsize = len(buffer) 
        buffer = self.file.read(size)
        if len(buffer) != size:
            self._lasterror = 'Unable to read engine version from ' + self.filename
            return False
        if self.version == 5:
            values = struct.unpack('256s', buffer)
        else:
            # version 4
            values = struct.unpack('16s', buffer)
        # store the engine version in self.engine_version
        position = values[0].find('\0')
        if position == -1:
            self.engine_version = values[0]
        elif position == 0:
            self.engine_version = '' 
        else:
            self.engine_version = values[0][0:position]
        nsize += len(buffer)
        # the next part concerns game ID and various chunk sizes
        size = struct.calcsize('=16sQ12i')
        if size + nsize != self.headersize:
            self._lasterror = 'File ' + self.filename + ' has header length ' + str(self.headersize) + ', expected ' + str(size + len(buffer))
            return False
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
        if self.version == 4:
            if values[13] != -1:
                self.winningteam.append(values[13])
        else:
            self.winningteamchunksize = values[13]
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
        self.playernames = dict()
        while playerseq < 128:
            if 'player' + str(playerseq) not in self.settings['game']:
                playerseq = playerseq + 1
                continue
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
                self.players.append((playername, realteam, team, dictname, playerseq, False))
            else:
                # this person is *not* playing, so we make a default entry in the list
                self.players.append((playername, -1, -1, dictname, playerseq, False))
            self.playernames[playerseq] = playername
                
            playerseq = playerseq + 1
        
        # find out if there are AI's
        aiseq = 0
        self.ais = list()
        while aiseq < 128:
            if 'ai' + str(aiseq) not in self.settings['game']:
                aiseq = aiseq + 1
                continue
            dictname = 'ai' + str(aiseq)
            playerdict = self.settings['game'][dictname]
            if type(playerdict) != type(dict()):
                self._lasterror = 'Entry for ' + dictname + ' is not a dictionary'
                return None
            if ('shortname' not in playerdict and 'name' not in playerdict) or 'team' not in playerdict:
                self._lasterror = 'Game settings incomplete for ' + dictname
                return None
            if 'name' not in playerdict:
                playername = playerdict['shortname']
            else:
                playername = playerdict['name']
            team = int(playerdict['team'])
            if 'team' + str(team) not in self.settings['game']:
                self._lasterror = 'Unable to find team for ' + dictname + ', AI player ' + playername
                return None
            teamdict = self.settings['game']['team' + str(team)]
            if type(teamdict) != type(dict()):
                self._lasterror = 'Team entry for active player ' + dictname + ' is not a dictionary'
                return None
            if 'allyteam' not in teamdict:
                self._lasterror = 'Unable to find the real team for ' + dictname + ', active player ' + playername
                return None
            realteam = int(teamdict['allyteam'])
            self.ais.append((playername, realteam, team, dictname, aiseq, True))
            # self.playernames[playerseq] = playername
                
            aiseq = aiseq + 1
        
        
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
            if teamleader not in self.playernames:
                self._lasterror = 'Invalid teamleader for team ' + dictname
                return None
            # locate player
            found = False
            for p in self.players:
                if teamleader != p[4]:
                    continue
                if p[1] == -1:
                    self._lasterror = 'Teamleader of team ' + dictname + ' is spectating?'
                    return None
                if p[2] != teamseq:
                    # find out which AI is controlling this team
                    found = False
                    for ai in self.ais:
                        if ai[2] == teamseq:
                            found = True
                            self.teams.append((ai[0], realteam, dictname, False))
                            break
                    if not found:
                        self._lasterror = 'AI controlling team ' + dictname + ' not found?'
                        return None
                else:
                    self.teams.append((p[0], realteam, dictname, True))
                    found = True
                break
            if not found:
                self._lasterror = 'Player controlling team ' + dictname + ' not found?'
                return None
                
            teamseq = teamseq + 1
        if not self.incomplete:
            if len(self.teams) != self.numteams:
                self._lasterror = 'Number of teams in header does not correspond with number of teams in start script'
                return None
                
        return self.startscript
        
    def demostream(self):
        '''
        Read the demo chunks from the file. These are stored in an internal structure for access after reading
        
        Returns the number of demo chunks found or None if they cannot be read
        '''
        if self.file == None:
            self._lasterror = 'File ' + self.filename + ' not open.'
            return None
        if self.headersize == 0:
            self._lasterror = 'Cannot read demo stream, read the header first'
            return None
        if self.players == None:
            self._lasterror = 'Cannot comprehend demo stream, read the start script first'
            return None
        if self.demostreamsize == 0:
            self._lasterror = 'Cannot read demo stream, it is empty'
            return None
        where = self.headersize + self.scriptsize
        self.file.seek(where,0)
        self.demorecords = list()
        n = 0
        chunkheader = struct.Struct('fL')
        while n < self.demostreamsize:
            # read header of one record
            if n + chunkheader.size > self.demostreamsize:
                self._lasterror = 'Demo stream truncated: incomplete chunk header'
                return len(self.demorecords)
            buffer = self.file.read(chunkheader.size)
            if len(buffer) != chunkheader.size:
                self._lasterror = 'File ' + self.filename + ', demo chunk header truncated'
                return len(self.demorecords)
            values = chunkheader.unpack_from(buffer,0)
            n += chunkheader.size
            # print 'Read chunk header #' + str(len(self.demorecords)) + ': at ' + str(values[0]) + ' l= ' + str(values[1]) + ' starting at ' + str(n)
            # stuff it in a new chunk
            chunk = DemoRecord()
            chunk.gametime = values[0]
            # read data portion of record
            if n + values[1] > self.demostreamsize:
                self._lasterror = 'Demo stream truncated: incomplete chunk record'
                return len(self.demorecords)
            if values[1] != 0:
                buffer = self.file.read(values[1])
                if len(buffer) != values[1]:
                    self._lasterror = 'File ' + self.filename + ', demo chunk record truncated'
                    return len(self.demorecords)
                chunk.data = buffer
            # add record to list and repeat
            t = chunk.type()
            if t != chunk.KEYFRAME and t != chunk.NEWFRAME:
                # do not add keyframe or newframe records, there are too many and we do not need the info, really
                # @todo: treat ZK_DAMAGE, ZK_UNIT and ZK_AWARD differently, they are duplicated
                self.demorecords.append(chunk)
            if t == chunk.PLAYERNAME:
                if chunk.player() not in self.playernames:
                    # add players (spectators, mostly) to the named player dictionary
                    self.playernames[chunk.player()] = chunk.text()
            if t == chunk.CREATE_NEWPLAYER:
                # add new players to the player list
                if chunk.spectator() == 0:
                    # uh ... adding a new 'real' player, untested and uncharted waters here
                    self.players.append(((chunk.text(), -1, chunk.team(), None)))
                else:
                    self.players.append((chunk.text(), -1, -1, None))

            n += values[1]
        # all demo records read
        return len(self.demorecords)
    def chatlog(self):
        '''
        Returns a data structure containing the 'chat' log of the game.
        
        The data structure is a list of tuples where each tuple is formatted as follows:
        1. The game time (float, in seconds)
        2. The type of message (by number, see the DemoRecord for the constants)
        3. The originating player (by name). This is None for system messages.
        4. The destination player or player group (by name).
        5. The text of the message. This is forged in the case of some messages.
        
        The method returns None if the data cannot be read. At least the header, the script and demostream methods
        must have been called prior to calling this method.
        '''
        if self.headersize == 0:
            self._lasterror = 'Cannot read chat log, read the header first'
            return None
        if self.players == None:
            self._lasterror = 'Cannot comprehend demo stream, read the start script first'
            return None
        if self.demorecords == None or len(self.demorecords) == 0:
            self._lasterror = 'Demo stream not available, read the demostream first'
            return None
        result = list()
        for rec in self.demorecords:
            if rec.type() == DemoRecord.CHAT:
                t = rec.gametime
                p = rec.player()
                if p in self.playernames:
                    src = self.playernames[p]
                elif p == DemoRecord.CHAT_ALLIES:
                    src = 'Allies'
                elif p == DemoRecord.CHAT_SPECTATORS:
                    src = 'Spectators'
                elif p == DemoRecord.CHAT_EVERYONE:
                    src = 'Everyone'
                elif p == DemoRecord.CHAT_HOST:
                    src = 'Host'
                else:
                    src = None
                p = rec.destination()
                if p in self.playernames:
                    dst = self.playernames[p]
                elif p == DemoRecord.CHAT_ALLIES:
                    dst = 'Allies'
                elif p == DemoRecord.CHAT_SPECTATORS:
                    dst = 'Spectators'
                elif p == DemoRecord.CHAT_EVERYONE:
                    dst = 'Everyone'
                elif p == DemoRecord.CHAT_HOST:
                    dst = 'Host'
                else:
                    dst = None
                s = rec.text()
            elif rec.type() == DemoRecord.MAPDRAW and rec.text() != None:
                # only if there is non-zero text in it
                t = rec.gametime
                p = rec.player()
                if p in self.playernames:
                    src = self.playernames[p]
                elif p == DemoRecord.CHAT_ALLIES:
                    src = 'Allies'
                elif p == DemoRecord.CHAT_SPECTATORS:
                    src = 'Spectators'
                elif p == DemoRecord.CHAT_EVERYONE:
                    src = 'Everyone'
                elif p == DemoRecord.CHAT_HOST:
                    src = 'Host'
                else:
                    src = None
                dst = None
                s = rec.text()
            elif rec.type() == DemoRecord.SYSTEMMSG:
                t = rec.gametime
                src = None
                dst = None
                s = rec.text()
            elif rec.type() == DemoRecord.QUIT:
                t = rec.gametime
                src = None
                dst = None
                s = rec.text()
            elif rec.type() == DemoRecord.PAUSE:
                t = rec.gametime
                p = rec.player()
                if p in self.playernames:
                    src = self.playernames[p]
                elif p == DemoRecord.CHAT_ALLIES:
                    src = 'Allies'
                elif p == DemoRecord.CHAT_SPECTATORS:
                    src = 'Spectators'
                elif p == DemoRecord.CHAT_EVERYONE:
                    src = 'Everyone'
                elif p == DemoRecord.CHAT_HOST:
                    src = 'Host'
                else:
                    src = None
                dst = None
                if rec.reason() == 0:
                    if src != None:
                        s = src + ' resumed the game.'
                    else:
                        s = 'Someone resumed the game'
                else:
                    if src != None:
                        s = src + ' paused the game.'
                    else:
                        s = 'Someone paused the game'
            elif rec.type() == DemoRecord.PLAYERLEFT:
                t = rec.gametime
                p = rec.player()
                if p in self.playernames:
                    src = self.playernames[p]
                elif p == DemoRecord.CHAT_ALLIES:
                    src = 'Allies'
                elif p == DemoRecord.CHAT_SPECTATORS:
                    src = 'Spectators'
                elif p == DemoRecord.CHAT_EVERYONE:
                    src = 'Everyone'
                elif p == DemoRecord.CHAT_HOST:
                    src = 'Host'
                else:
                    src = None
                dst = None
                if rec.reason() == 0:
                    st = ' lost connection.'
                elif rec.reason() == 1:
                    st = ' left the game.'
                else:
                    st = ' was kicked out of the game.'
                if src != None:
                    s = src + st
                else:
                    s = 'Someone' + st
            else:
                continue
            result.append((t, rec.type(), src, dst, s))
                
        return result
    def awards(self):
        '''
        Determine what ZK awards were handed out.
        
        Returns a list of handed out awards. As each award is uniquely awarded to a player, this makes the removal of any duplicates easy.
        
        The list is a list of 4-tuples, which each tuple player name, award abbreviation, award title, award reason
        '''
        awarddict = dict()
        for rec in self.demorecords:
            if rec.type() == rec.ZK_AWARD:
                # parse the award text
                raw = rec.text()
                pos = raw.find(' ')
                if pos == -1:
                    self._lasterror = 'Cannot find player in award text'
                    continue
                else:
                    p = raw[0:pos]
                # print 'pos=' + str(pos) + ' in:' + raw + '/' + p 
                npos = raw[pos + 1:].find(' ')
                if npos == -1:
                    self._lasterror = 'Cannot find award type in award text'
                    continue
                else:
                    t = raw[pos + 1:pos + npos + 1]
                # print 'npos=' + str(npos) + ' in:' + raw[pos+1:] + '/' + t
                # reason is separated by a comma and a space
                rpos =  raw[pos + npos + 2:].find(', ')
                if rpos == -1:
                    self._lasterror = 'Cannot find award title in award text'
                    continue
                else:
                    fullt = raw[pos + npos + 2: pos + npos + rpos + 2]
                # print 'rpos=' + str(rpos) + ' in:' + raw[pos + npos + 2:] + '/' + fullt
                r = raw[pos + npos + rpos + 4:]
                if t in awarddict:
                    if p != awarddict[t][0]:
                        self._lasterror = 'Discrepancy in player award ' + t + ', assigned to ' + p + ' and to ' + awarddict[t][0]
                    if r != awarddict[t][3]:
                        self._lasterror = 'Discrepancy in player award ' + t + ', reason #1=' + r + ' and reason #2= ' + awarddict[t][3]
                    continue
                else:
                    awarddict[t] = ( p, t, fullt, r)
        result = list()
        for t in awarddict:
            result.append(awarddict[t])
        # sort on player name, then award abbreviation
        result.sort()
        return result
    
    def similar(self, a, b, accuracy=1e-9):
        '''
        Method returns true if the two floating point values a and b are similar
        '''
        q = abs(a) + abs(b)
        d = abs(a - b)
        if q == 0.0:
            # special case
            if d != 0.0:
                return False
            else:
                return True
        if d / q < accuracy:
            return True
        else:
            return False
    
    def zkunitname(self, abbrev):
        '''
        Given a zk unit name, return the full name
        '''
        if abbrev in self.zkunitnames:
            return self.zkunitnames[abbrev]
        else:
            return abbrev
        
    def damagestats(self):
        '''
        Determine what ZK damage stats were recorded.
        
        Returns a (sorted) list of damage items, where each damage item is
        a tuple of:
        1. attacking unit name
        2. damaged unit name
        3. regular damage done (total)
        4. EMP damage done (total)
        '''
        damagedict = dict()
        for rec in self.demorecords:
            if rec.type() == rec.ZK_DAMAGE:
                # parse the award text
                raw = rec.text()
                pos = raw.find(',')
                if pos == -1:
                    self._lasterror = 'Cannot find damaging unit in damage text'
                    continue
                else:
                    dmgby = raw[0:pos]
                # print 'pos=' + str(pos) + ' in:' + raw + '/' + p 
                npos = raw[pos + 1:].find(',')
                if npos == -1:
                    self._lasterror = 'Cannot find damaged unit in damage text'
                    continue
                else:
                    dmgto = raw[pos + 1:pos + npos + 1]
                # print 'npos=' + str(npos) + ' in:' + raw[pos+1:] + '/' + t
                # reason is separated by a comma and a space
                rpos =  raw[pos + npos + 2:].find(',')
                if rpos == -1:
                    self._lasterror = 'Cannot find real damage amount in damage text'
                    continue
                else:
                    realdmg = raw[pos + npos + 2: pos + npos + rpos + 2]
                # print 'rpos=' + str(rpos) + ' in:' + raw[pos + npos + 2:] + '/' + fullt
                empdmg = raw[pos + npos + rpos + 3:]
                if dmgby not in damagedict:
                    damagedict[dmgby] = dict()
                if dmgto not in damagedict[dmgby]:
                    damagedict[dmgby][dmgto] = list()
                frealdmg = float(realdmg)
                fempdmg = float(empdmg)
                if len(damagedict[dmgby][dmgto]) == 0:
                    damagedict[dmgby][dmgto].append(( rec.player(), float(realdmg) ,  float(empdmg)))
                else:
                    if (not self.similar(frealdmg, damagedict[dmgby][dmgto][0][1]) or 
                        not self.similar(fempdmg, damagedict[dmgby][dmgto][0][2])):
                        print 'Mismatch in damage record for unit ' + dmgby + ' to ' + dmgto
                        damagedict[dmgby][dmgto].append(( rec.player(), float(realdmg) ,  float(empdmg)))
                         
        damagelist = list()
        for dmgby in damagedict:
            for dmgto in damagedict[dmgby]:
                damages = list()
                damages.append(self.zkunitname(dmgby))
                damages.append(self.zkunitname(dmgto))
                damages.append(damagedict[dmgby][dmgto][0][1])
                damages.append(damagedict[dmgby][dmgto][0][2])
                damagelist.append(damages)
        damagelist.sort()
        return damagelist
        
    def unitstats(self):
        '''
        Determine what ZK unit stats were recorded.
        
        Returns a (sorted) list of units, where each unit is a list of 5 elements:
        1. unit name
        2. unit metal cost
        3. unit health
        4. units produced
        5. units killed
        
        '''
        unitdict = dict()
        for rec in self.demorecords:
            if rec.type() == rec.ZK_UNIT:
                # parse the award text
                raw = rec.text()
                pos = raw.find(',')
                if pos == -1:
                    self._lasterror = 'Cannot find unit type in unit text'
                    continue
                else:
                    unit = raw[0:pos]
                # print 'pos=' + str(pos) + ' in:' + raw + '/' + p 
                npos = raw[pos + 1:].find(',')
                if npos == -1:
                    self._lasterror = 'Cannot find metal cost in unit text'
                    continue
                else:
                    metal = raw[pos + 1:pos + npos + 1]
                # print 'npos=' + str(npos) + ' in:' + raw[pos+1:] + '/' + t
                # reason is separated by a comma and a space
                rpos =  raw[pos + npos + 2:].find(',')
                if rpos == -1:
                    self._lasterror = 'Cannot find units produced amount in unit text'
                    continue
                else:
                    produced = raw[pos + npos + 2: pos + npos + rpos + 2]
                xpos =  raw[pos + npos + rpos + 3:].find(',')
                if xpos == -1:
                    self._lasterror = 'Cannot find units killed amount in unit text'
                    continue
                else:
                    killed = raw[pos + npos + rpos + 3: pos + npos + rpos + xpos + 3]
                # print 'rpos=' + str(rpos) + ' in:' + raw[pos + npos + 2:] + '/' + fullt
                health = raw[pos + npos + rpos + xpos + 4:]
                if unit not in unitdict:
                    unitdict[unit] = list()
                fmetal = float(metal)
                fhealth = float(health)
                iproduced = int(produced)
                ikilled = int(killed)
                if len(unitdict[unit]) == 0:
                    unitdict[unit].append((rec.player(), unit, fmetal, fhealth, iproduced, ikilled))
                else:
                    if (not self.similar(fmetal, unitdict[unit][0][2]) or 
                        not self.similar(fhealth, unitdict[unit][0][3]) or
                        iproduced != unitdict[unit][0][4] or 
                        ikilled != unitdict[unit][0][5]):
                        print 'Mismatch in unit record for unit ' + unit
                        unitdict[unit].append((rec.player(), unit, fmetal, fhealth, iproduced, ikilled))
                         
        unitlist = list()
        for unit in unitdict:
            stats = list()
            stats.append(self.zkunitname(unit))
            stats.append(unitdict[unit][0][2])
            stats.append(unitdict[unit][0][3])
            stats.append(unitdict[unit][0][4])
            stats.append(unitdict[unit][0][5])
            unitlist.append(stats)
        unitlist.sort()
        return unitlist
        
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
        # get the team numbers of the winning ally teams
        self.winners()
        where = self.headersize + self.scriptsize + self.demostreamsize + self.winningteamchunksize
        self.file.seek(where,0)
        buffer = self.file.read(self.playerstatchunksize)
        if len(buffer) != self.playerstatchunksize:
            self._lasterror = 'File ' + self.filename + ', player statistics truncated'
            return None
        offset = 0
        self.playerstatistics = dict()
        for x in self.players:
            # the statistics for spectators are immaterial, we just skip over them
            if x[1] != -1:
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
        where = self.headersize + self.scriptsize + self.demostreamsize + self.winningteamchunksize + self.playerstatchunksize 
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
            fmt = '=i'
            size = struct.calcsize(fmt)
            values = struct.unpack(fmt, buffer[offset:offset + size])
            sizes.append(values[0])
            # print x[0] + ' has ' + str(values[0]) + ' statistic records from ' + repr(buffer[offset:offset + size])
            offset = offset + size
            xsize = xsize + size + values[0] * self.teamstatelemsize
        # check for consistency
        if xsize != self.teamstatchunksize:
            self._lasterror = 'Calculated (' + str(xsize) + ') and real (' + str(self.teamstatchunksize) + ') team statistic chunk size differ'
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
                t.unitsKilled = values[19]
                teamstat.append(t)
                offset = offset + self.teamstatelemsize
            self.teamstatistics[x[0]] = teamstat
        return self.teamstatistics
    
    def winners(self):
        '''
        Retrieve the team numbers of the winning teams if we did not already do so
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
            self._lasterror = 'File ' + self.filename + ' is an incomplete demo, cannot read winners'
            return None
        if self.version <= 4:
            # no need to do anything
            return len(self.winningteam)
        if self.winningteamchunksize == 0:
            self._lasterror = 'File ' + self.filename + ' does not contain winning team vector'
            return None
        where = self.headersize + self.scriptsize + self.demostreamsize 
        self.file.seek(where,0)
        buffer = self.file.read(self.winningteamchunksize)
        if len(buffer) != self.winningteamchunksize:
            self._lasterror = 'File ' + self.filename + ', winning team vector truncated'
            return None
        for c in buffer:
            self.winningteam.append(ord(c))
        return len(self.winningteam)

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

        
        
