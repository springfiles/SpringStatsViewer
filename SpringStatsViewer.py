#!/usr/bin/python
#
# SpringStatsViewer - Tix application to display the statistics collected in the Spring Demo File
#
# To run on windows: pythonw SpringStatsViewer.py (or python SpringStatsViewer)
#        on linux: chmod +x SpringStatsViewer.py; ./SpringStatsViewer.py (untested)
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
import Tix
import tkFileDialog
import tkMessageBox
import SpringDemoFile
import sys

__author__ = 'rene'
__version__ = '0.1.0'

#
# The viewer application is contained in a single top level window
#
class Application(Tix.Frame):
    def openfile(self, filename):
        '''
        loads a file
        '''
        if self.demofile != None:
            self.demofile = None
            self.teams = dict()
            self.playerorder = list()
            self.playerbykey = dict()
            self.cleargraph(self.canvas)
            self.menuFile.entryconfigure(1, state=Tix.DISABLED)
            self.menuView.entryconfigure(1, state=Tix.DISABLED)
            self.menuView.entryconfigure(2, state=Tix.DISABLED)
        
        self.demofile = SpringDemoFile.DemoFileReader(filename,dirname=None)
        # read the header
        if self.demofile.header():
            # okay, read the header
            tmp = self.demofile.script()
            if tmp != None and not self.demofile.incomplete and not self.demofile.crashed:
                # okay, if the game is not incomplete or crashed, then read the player and team stats
                tmp = self.demofile.playerstats()
                if tmp != None:
                    self.menuView.entryconfigure(1, state=Tix.NORMAL)
                    tmp = self.demofile.teamstats()
                    if tmp != None:
                        self.menuView.entryconfigure(2, state=Tix.NORMAL)
        self.demofile.close()
        self.currentview = 0
        self.assembleteamstructure()
        self.drawgameinfo(self.canvas)
        self.menuFile.entryconfigure(1, state=Tix.NORMAL)
    def __open(self):
        '''
        Callback handler for File|Open
        
        Prompts the user for a spring demo file and open it, causing the statistics if available
        to be displayed.
        '''
        # let the user select a Spring Demo File and attempt to open it
        file = tkFileDialog.askopenfile(
            filetypes=[('Spring Demo File', '*.sdf'), ('All files', '*.*')],
            defaultextension='.sdf',
            title='Select a Spring Demo File')
        # in contrast to the documentation, askopenfile returns an open file instead of
        # a string with the filename so we just get the name of that and reopen it
        # in the demo file reader.
        if file == None:
            return
        filename = file.name
        file.close()
        self.openfile(filename)
        
    def __close(self):
        '''
        Callback handler for the File|Close menu entry.
        
        Closes the  demofile and resets the GUI state to the default view
        '''
        # print 'Close currently open SDF file'
        self.demofile = None
        self.teams = dict()
        self.playerorder = list()
        self.playerbykey = dict()
        self.cleargraph(self.canvas)
        self.currentview = 0
        self.menuFile.entryconfigure(1, state=Tix.DISABLED)
        self.menuView.entryconfigure(1, state=Tix.DISABLED)
        self.menuView.entryconfigure(2, state=Tix.DISABLED)
        self.drawgameinfo(self.canvas)
        
    def __exit(self):
        '''
        Callback handler for the File|Exit menu entry.
        
        Causes the application to quit
        '''
        # print 'Exit the application'
        self.quit()
        
    def pickcolor(self, teamno, teamplayer, nteams):
        '''
        Returns an RGB triplet in Tk format giving a 'color' to a player depending on which team he is in
        '''
        huestep = 360 / nteams
        huerange = huestep / 3
        n = teamplayer % 5
        basehue = huestep * teamno
        h = ( basehue, basehue + huerange, basehue - huerange, basehue + huerange / 2, basehue - huerange / 2 )[n]
        if h < 0:
            h += 360
        n = ( teamplayer / 5 ) % 5
        s = ( 1.0, 0.5, 0.75, 0.5, 0.75 )[n]
        v = ( 1.0, 0.75, 1.0, 1.0, 0.5)[n]
        c = v * s
        hprime = float(h) / 60.0
        x = c * (1 - abs((divmod(hprime, 2))[1] - 1))
        if hprime < 1:
            r = c
            g = x
            b = 0
        elif hprime < 2:
            r = x
            g = c
            b = 0
        elif hprime < 3:
            r = 0
            g = c
            b = x
        elif hprime < 4:
            r = 0
            g = x
            b = c
        elif hprime < 5:
            r = x
            g = 0
            b = c
        else:
            r = c
            g = 0
            b = x
        r += v - c
        g += v - c
        b += v - c
        ir = int(255.0 * r + 0.49999)
        ig = int(255.0 * g + 0.49999)
        ib = int(255.0 * b + 0.49999)
        result =  '#%02X%02X%02X' % ( ir, ig, ib )
        # print str(teamno) + ':' + str(teamplayer) + 'HSV: ' + str(h) +', ' + str(s) + ', ' + str(v) + ' RGB: ' + result
        return result
    
    def assembleteamstructure(self):
        '''
        Fills the self.teams dictionary, the self.playerorder list and the self.playerbykey structures
        '''
        self.teams = dict()
        self.playerorder = list()
        self.playerbykey = dict()
        if self.demofile == None:
            return
        if self.demofile.teams == None or len(self.demofile.teams) == 0:
            return
        for t in self.demofile.teams:
            if t[1] in self.teams:
                self.teams[t[1]].append(t[0])
            else:
                self.teams[t[1]] = list()
                self.teams[t[1]].append(t[0])
        teamno = 1
        playerno = 0
        nteams = len(self.teams)
        for t in self.teams:
            self.teams[t].sort()
            teamplayerno = 0
            for p in self.teams[t]:
                self.playerorder.append(p)
                self.playerbykey[p] = [ self.pickcolor(teamno-1, teamplayerno, nteams), teamno, teamplayerno, playerno, p]
                teamplayerno = teamplayerno + 1
                playerno = playerno + 1
            teamno = teamno + 1
        
    def drawgameinfo(self, canvas):
        '''
        Draw on the game info canvas to display meta-information about the loaded game
        '''
        # clear canvas
        for tag in canvas.find_all():
            canvas.delete(tag)
            
        # print 'Canvas w=' + str(canvas['width']) + ' h=' + str(canvas['height'])
        # print 'Current size: w=' + str(self.canvas.winfo_width()) + ' h=' + str(self.canvas.winfo_height())
        # print 'Requested size: w=' + str(self.canvas.winfo_reqwidth()) + ' h=' + str(self.canvas.winfo_reqheight())
      
        if self.demofile == None:
            # No game loaded
            canvas.create_text(400, 300, text = 'No demo file loaded',
                state=Tix.DISABLED,
                disabledfill='#EEE',
                fill='#FFF')
        else:
            if self.demofile.incomplete:
                id = canvas.create_text(10, 10, anchor=Tix.NW, text='The game is incomplete',
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
            elif self.demofile.crashed:
                id = canvas.create_text(10, 10, anchor=Tix.NW,  text='The game crashed before it could complete',
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
            elif self.demofile.exited:
                id = canvas.create_text(10, 10, anchor=Tix.NW,  text='The game was exited before game over',
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
            else:
                id = canvas.create_text(10, 10, anchor=Tix.NW,  text='The game completed normally',
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
            # get the bbox of the text to determine the vertical offset
            # print 'ID of box = ' + str(id)
            box = canvas.bbox(id)
            # print 'Box dimensions ' + str(box[0]) + ', ' + str(box[1]) + ' --> ' + str(box[2]) + ', ' + str(box[3])
            # print 'Next line offset = ' + str(1.5 * (box[3] - box[1]))
            offset = 1.5 * ( box[3] - box[1] )
            n = 1
            if self.demofile.errormessage() != None:
                id = canvas.create_text(10, 10 + n * offset, anchor=Tix.NW,  text='Error: ' + self.demofile.errormessage(),
                    state=Tix.DISABLED,
                    disabledfill='#E11',
                    fill='#F00')
                n = n + 1
            if self.demofile.gametype != None:
                id = canvas.create_text(10, 10 + n * offset, anchor=Tix.NW,  text='Game: ' + self.demofile.gametype,
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                n = n + 1
            if self.demofile.map != None:
                id = canvas.create_text(10, 10 + n * offset, anchor=Tix.NW,  text='Map: ' + self.demofile.map,
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                n = n + 1
            if not self.demofile.incomplete:
                s1 = ''
                s2 = ''
                hrs = self.demofile.totalgametime / 3600
                if hrs > 0:
                    s1 = s1 + str(hrs) + 'h'
                min = ( self.demofile.totalgametime / 60 ) % 60
                if hrs > 0 or min > 0:
                    s1 = s1 + str(min) + 'm'
                sec = self.demofile.totalgametime % 60
                if sec != 0:
                    s1 = s1 + str(sec) + 's'
                hrs = self.demofile.elapsedrealtime / 3600
                if hrs > 0:
                    s2 = s2 + str(hrs) + 'h'
                min = ( self.demofile.elapsedrealtime / 60 ) % 60
                if hrs > 0 or min > 0:
                    s2 = s2 + str(min) + 'm'
                sec = self.demofile.elapsedrealtime % 60
                if sec != 0:
                    s2 = s2 + str(sec) + 's'
                id = canvas.create_text(10, 10 + n * offset, anchor=Tix.NW,  text='Duration: ' + s1 + ' (Total: ' + s2 + ')',
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                n = n + 1
            # display the members of the teams
            teamno = 1
            for t in self.teams:
                id = canvas.create_text(10, 10 + n * offset, anchor=Tix.NW,  text='Team #' + str(teamno) + ':',
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                box = canvas.bbox(id)
                taboffset = offset + box[2]
                xoffset = taboffset
                for p in self.teams[t]:
                    id = canvas.create_text(taboffset, 10 + n * offset, anchor=Tix.NW,  text=p,
                        state=Tix.DISABLED,
                        disabledfill=self.playerbykey[p][0],
                        fill=self.playerbykey[p][0])
                    box = canvas.bbox(id)
                    if box[2] - box[0] + xoffset >= int(canvas['width']):
                        # print 'Player '+ p + ' with width ' + str(box[2]-box[0]) + ' no longer fits at ' + str(xoffset)
                        canvas.move(id, 0, offset)
                        n = n + 1
                        xoffset = taboffset + box[2] - box[0] + offset
                    else:
                        # print 'Player '+ p + ' with width ' + str(box[2]-box[0]) + ' fits at ' + str(xoffset)
                        canvas.move(id, xoffset - taboffset, 0)
                        xoffset = xoffset + box[2] - box[0] + offset
                    
                n = n + 1
                teamno = teamno + 1
                
                
    def drawplayerstats(self, canvas):
        '''
        Draw on the player stats canvas to statistics about player interaction
        
        Player stats are displayed as a table with the top heading row
        Player KP/m MP/m MC/m CMD/m Units/CMD
        
        Each player gets a row, unless all values are zero in which case we say that the player quit before the game was over
        '''
        # clear canvas
        for tag in canvas.find_all():
            canvas.delete(tag)
        if ( self.demofile == None or
            self.demofile.incomplete or self.demofile.crashed or
            self.demofile.playerstatistics == None):
            return
        # create the heading row
        hrow = list()
        id = canvas.create_text(10, 10, anchor=Tix.NW, text='Player',
            state=Tix.DISABLED,
            disabledfill='#EEE',
            fill='#FFF')
        hrow.append(id)
        box = canvas.bbox(id)
        offset = box[3] - box[1]

        id = canvas.create_text(310, 10, anchor=Tix.NE, text='KP/m',
            state=Tix.DISABLED,
            disabledfill='#EEE',
            fill='#FFF')
        hrow.append(id)

        id = canvas.create_text(430, 10, anchor=Tix.NE, text='MP/m',
            state=Tix.DISABLED,
            disabledfill='#EEE',
            fill='#FFF')
        hrow.append(id)

        id = canvas.create_text(550, 10, anchor=Tix.NE, text='MC/m',
            state=Tix.DISABLED,
            disabledfill='#EEE',
            fill='#FFF')
        hrow.append(id)
            
        id = canvas.create_text(670, 10, anchor=Tix.NE, text='CMD/m',
            state=Tix.DISABLED,
            disabledfill='#EEE',
            fill='#FFF')
        hrow.append(id)

        id = canvas.create_text(790, 10, anchor=Tix.NE, text='Units/CMD',
            state=Tix.DISABLED,
            disabledfill='#EEE',
            fill='#FFF')
        hrow.append(id)
            
            
        # count the number of players and sort their names
        ids = list()
        n = 1
        offset = 1.5 * offset
        for p in self.playerorder:
            rowids = list()
            id = canvas.create_text(10, 10 + n * offset, anchor=Tix.NW, text=p,
                state=Tix.DISABLED,
                disabledfill=self.playerbykey[p][0],
                fill=self.playerbykey[p][0])
            rowids.append(id)
         
            stats = self.demofile.playerstatistics[p]
            if ( stats.mousePixels == 0 and
                stats.mouseClicks == 0 and
                stats.keyPresses == 0 and
                stats.numCommands == 0 and
                stats.unitCommands == 0 ):
                id = canvas.create_text(300, 10 + n * offset, anchor=Tix.NW, text='Player left before game over',
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                rowids.append(id)
            else:
                s = "%.1f" % ( float(stats.keyPresses) / 60.0 )
                id = canvas.create_text(310, 10 + n * offset, anchor=Tix.NE, text=s,
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                rowids.append(id)
                s = "%.1f" % ( float(stats.mousePixels) / 60.0 )
                id = canvas.create_text(430, 10 + n * offset, anchor=Tix.NE, text=s,
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                rowids.append(id)
                s = "%.1f" % ( float(stats.mouseClicks) / 60.0 )
                id = canvas.create_text(550, 10 + n * offset, anchor=Tix.NE, text=s,
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                rowids.append(id)
                s = "%.1f" % ( float(stats.numCommands) / 60.0 )
                id = canvas.create_text(670, 10 + n * offset, anchor=Tix.NE, text=s,
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                rowids.append(id)
                if stats.numCommands == 0:
                    s = '-'
                else:
                    s = "%.1f" % ( float(stats.unitCommands) / float(stats.numCommands) )
                id = canvas.create_text(790, 10 + n * offset, anchor=Tix.NE, text=s,
                    state=Tix.DISABLED,
                    disabledfill='#EEE',
                    fill='#FFF')
                rowids.append(id)
            n = n + 1
            ids.append(rowids)
            
        # print ids
        # get maximum width of column n to adjust offset of column n + 1
        n = 0
        while n < len(hrow) - 1:
            box = canvas.bbox(hrow[n])
            width = box[2]
            for row in ids:
                if len(row) > 2 or n < 1:
                    box = canvas.bbox(row[n])
                    if box[2] > width:
                        width = box[2]
            xcolumn = width + offset
            box = canvas.bbox(hrow[n+1])
            x1 = box[0]
            for row in ids:
                if len(row) > 2 or n < 1:
                    box = canvas.bbox(row[n+1])
                    if box[0] < x1:
                        x1 = box[0]
            xdelta = xcolumn - x1
            canvas.move(hrow[n+1], xdelta, 0)
            for row in ids:
                if len(row) > 2 or n < 1:
                    canvas.move(row[n+1], xdelta, 0)
            n = n + 1
    
    def __categorybuttonselected(self, event, button, canvas):
        '''
        Event handler that is called whenever the user releases the (left) mouse button on a category button
        '''
        # print 'category button #' + str(button) + ' selected'
        if button not in self.graphcategorybuttons:
            return
        n = self.graphcategorybuttons[button][0]
        if n == self.selectedgraphcategory:
            # selecting a radio button that is already selected does nothing
            return
        # make the old category have the normal appearance
        for b in self.graphcategorybuttons:
            zb = self.graphcategorybuttons[b]
            if zb[0] == self.selectedgraphcategory:
                canvas.itemconfigure(zb[2], 
                    fill='#444',
                    outline='#444',
                    activeoutline='#888',
                    activefill='#888')
                canvas.itemconfigure(zb[1], 
                    disabledfill='#EEE',
                    fill='#EEE')
                for ib in self.graphitembuttons:
                    zi = self.graphitembuttons[ib]
                    if zi[0] == self.selectedgraphcategory and zi[1] == self.selectedgraphitem:
                        # make the currently selected item button appear normal
                        canvas.itemconfigure(zi[3], 
                            fill='#444',
                            outline='#444',
                            activeoutline='#888',
                            activefill='#888')
                        canvas.itemconfigure(zi[2], 
                            disabledfill='#EEE',
                            fill='#EEE')
                    if zi[0] == self.selectedgraphcategory:
                        # hide the item buttons associated with the category
                        canvas.itemconfigure(zi[3], state=Tix.HIDDEN)
                        canvas.itemconfigure(zi[2], state=Tix.HIDDEN)
                        
        self.selectedgraphcategory = n
        self.selectedgraphitem = 0
        zb = self.graphcategorybuttons[button]
        canvas.itemconfigure(zb[2], 
            fill='#CCC',
            outline='#CCC',
            activeoutline='#EEE',
            activefill='#EEE')
        canvas.itemconfigure(zb[1], 
            disabledfill='#111',
            fill='#111')
        for ib in self.graphitembuttons:
            zi = self.graphitembuttons[ib]
            if zi[0] == self.selectedgraphcategory and zi[1] == self.selectedgraphitem:
                # make the currently selected item button appear active
                canvas.itemconfigure(zi[3], 
                    fill='#CCC',
                    outline='#CCC',
                    activeoutline='#EEE',
                    activefill='#EEE')
                canvas.itemconfigure(zi[2], 
                    disabledfill='#111',
                    fill='#111')
            if zi[0] == self.selectedgraphcategory:
                # unhide the item buttons associated with the category
                canvas.itemconfigure(zi[3], state=Tix.NORMAL)
                canvas.itemconfigure(zi[2], state=Tix.DISABLED)
        self.cleargraph(canvas)
        self.drawgraph(canvas)
            
        
    def __itembuttonselected(self, event, button, canvas):
        '''
        Event handler that is called whenever the user releases the (left) mouse button on a graph button
        '''
        # print 'item button #' + str(button) + ' selected'
        if button not in self.graphitembuttons:
            return
        m = self.graphitembuttons[button][1]
        if m == self.selectedgraphitem:
            # selecting a radio button that is already selected does nothing
            return
        # make the old item have the normal appearance
        for b in self.graphitembuttons:
            zb = self.graphitembuttons[b]
            if zb[0] == self.selectedgraphcategory and zb[1] == self.selectedgraphitem:
                canvas.itemconfigure(zb[3], 
                    fill='#444',
                    outline='#444',
                    activeoutline='#888',
                    activefill='#888')
                canvas.itemconfigure(zb[2], 
                    disabledfill='#EEE',
                    fill='#EEE')
                break
        self.selectedgraphitem = m
        zb = self.graphitembuttons[button]
        canvas.itemconfigure(zb[3], 
            fill='#CCC',
            outline='#CCC',
            activeoutline='#EEE',
            activefill='#EEE')
        canvas.itemconfigure(zb[2], 
            disabledfill='#111',
            fill='#111')
        self.cleargraph(canvas)
        self.drawgraph(canvas)
            
        
    def __playerbuttonselected(self, event, button, canvas):
        '''
        Event handler that is called whenever the user releases the (left) mouse button on a player button
        '''
        # print 'player button #' + str(button) + ' selected'
        if button not in self.playerbuttons:
            return
        m = self.playerbuttons[button]
        if m[3]:
            canvas.itemconfigure(m[2],
                fill='#000',
                outline='#000',
                activeoutline='#444',
                activefill='#444')
            m[3] = False
            canvas.itemconfigure(self.graphlines[m[4]],
                state=Tix.HIDDEN)
        else:
            canvas.itemconfigure(m[2],
                fill='#222',
                outline='#222',
                activeoutline='#444',
                activefill='#444')
            m[3] = True
            canvas.itemconfigure(self.graphlines[m[4]],
                state=Tix.NORMAL)
            
        
    def setupgraphselectionbuttons(self, canvas, width=200):
        '''
        This method draws the graph selection 'buttons' on the specified canvas and binds events to the them
        '''
        
        y = 10
        # category buttons, ie. Metal, Energy, Damage, Units
        self.graphcategorybuttons = dict()
        n = 0
        for masters in self.graphbuttonlabels:
            if masters[0] == self.graphbuttonlabels[self.selectedgraphcategory][0]:
                clrt = '#111'
                clrbtn = '#CCC'
                clra = '#EEE'
            else:
                clrt = '#EEE'
                clrbtn = '#444'
                clra = '#888'
            id = canvas.create_text(width / 2, y, anchor=Tix.N, text=masters[0],
                state=Tix.DISABLED,
                disabledfill=clrt,
                fill=clrt)
            box = canvas.bbox(id)
            id2 = canvas.create_rectangle(10, box[1] - 2, width - 10, box[3] + 2,
                fill=clrbtn,
                outline=clrbtn,
                activeoutline=clra,
                activefill=clra,
                state=Tix.NORMAL
                )
            self.graphcategorybuttons[id2] = ( n, id, id2 )
            def handler(event, self=self, button=id2, canvas=canvas):
                self.__categorybuttonselected(event, button, canvas)
            tag = 'categorybtn_' + str(id2)
            canvas.addtag_withtag(tag, id2)
            canvas.tag_bind(tag, sequence='<ButtonRelease-1>', func=handler)
            y = box[3] + 6
            canvas.tag_lower(id2,id)
            n = n + 1
        y = y + 10
        self.graphitembuttons = dict()
        ytop = y
        n = 0
        # draw all item buttons at once, but hide the texts and buttons from other categories
        # than the current one.
        for masters in self.graphbuttonlabels:
            y = ytop 
            m = 0
            for item in masters[1]:
                if n == self.selectedgraphcategory:
                    sb = Tix.NORMAL
                    st = Tix.DISABLED
                else:
                    sb = Tix.HIDDEN
                    st = Tix.HIDDEN
                    
                if m == self.selectedgraphitem:
                    clrt = '#111'
                    clrbtn = '#CCC'
                    clra = '#EEE'
                else:
                    clrt = '#EEE'
                    clrbtn = '#444'
                    clra = '#888'
                id = canvas.create_text(width / 2, y, anchor=Tix.N, text=item[0],
                    state=Tix.DISABLED,
                    disabledfill=clrt,
                    fill=clrt)
                box = canvas.bbox(id)
                id2 = canvas.create_rectangle(10, box[1] - 2, width - 10, box[3] + 2,
                    fill=clrbtn,
                    outline=clrbtn,
                    activeoutline=clra,
                    activefill=clra,
                    state=sb
                    )
                canvas.itemconfigure(id, state=st)
                self.graphitembuttons[id2] = (n, m, id, id2)
                def handler(event, self=self, button=id2, canvas=canvas):
                    self.__itembuttonselected(event, button, canvas)
                tag = 'itembtn_' + str(id2)
                canvas.addtag_withtag(tag, id2)
                canvas.tag_bind(tag,sequence='<ButtonRelease-1>',func=handler)
                y = box[3] + 6
                canvas.tag_lower(id2,id)
                m = m + 1
            n = n + 1
            
    def cleargraphselectionbuttons(self, canvas):
        '''
        This method unbinds the graph selection buttons from any event handlers and
        deletes them
        '''
        for b in self.graphitembuttons:
            zb = self.graphitembuttons[b]
            tag = 'itembtn_' + str(zb[3])
            canvas.tag_unbind(tag, '<ButtonRelease-1>')
            canvas.delete(zb[2])
            canvas.delete(zb[3])
        for b in self.graphcategorybuttons:
            zb = self.graphcategorybuttons[b]
            tag = 'categorybtn_' + str(zb[2])
            canvas.tag_unbind(tag, '<ButtonRelease-1>')
            canvas.delete(zb[1])
            canvas.delete(zb[2])
        self.graphitembuttons = dict()
        self.graphcategorybuttons = dict()

    def setupplayerselectionbuttons(self, canvas, width=200):
        '''
        This method draws the player selection 'buttons' on the specified canvas and binds events to the them
        '''
        
        y = 10
        idplayers = list()
        # put labels for each player in the same place for now
        largest = 0
        lineoffset = 0
        n = 0
        for p in self.playerorder:
            id = canvas.create_text(width + 14, 14, anchor=Tix.NW, text=p,
                state=Tix.DISABLED,
                disabledfill=self.playerbykey[p][0],
                fill=self.playerbykey[p][0])
            idplayers.append(id)
            box = canvas.bbox(id)
            offset = box[2] - box[0]
            
            if offset > largest:
                largest = offset
            if lineoffset < box[3] - box[1]:
                lineoffset = box[3] - box[1]
            n = n + 1
        # uses the largest player name as a basis for placing the legend labels
        lineoffset = lineoffset + 10
        if largest > 0:
            onerowfits = ( int(canvas['width']) - width ) / ( largest + 10 )
        else:
            onerowfits = 1
        # print 'Largest: ' + str(largest) + ' space: ' + str(lineoffset) + ' -> Fits: ' + str(onerowfits)
        line = 0
        column = 0
        n = 0
        # move all player labels to the right place and add a rectangle to serve as 'button'
        low = 0
        self.playerbuttons = dict()
        for p in self.playerorder:
            id = idplayers[n]
            box = canvas.bbox(id)
            x = width + column * ( largest + 10 )
            y = 10 + line * lineoffset
            # print 'Moving player name #'  + str(id) + ' at ' + str(line) + ', ' + str(column) + ' to (' + str(x) + ', ' + str(y) + ')'
            canvas.move(id,x - box[0], y - box[1])
            box = canvas.bbox(id)
            boxid = canvas.create_rectangle(box[0] - 4, box[1] - 4, box[0] + largest + 4, box[1] + lineoffset - 6,
                activefill='#444',
                activeoutline = '#444',
                fill='#222',
                outline='#222',
                state=Tix.NORMAL)
                
            def handler(event, self=self, button=boxid, canvas=canvas):
                self.__playerbuttonselected(event, button, canvas)
            tag = 'playerbtn_' + str(boxid)
            canvas.addtag_withtag(tag, boxid)
            canvas.tag_bind(tag, sequence='<ButtonRelease-1>', func=handler)
            canvas.tag_lower(boxid,id)
            
            self.playerbuttons[boxid] = [ p, id, boxid, True, n ]

            if box[1] + lineoffset - 5 > low:
                low = box[1] + lineoffset - 5
            n = n + 1
            column = column + 1
            if column >= onerowfits:
                line = line + 1
                column = 0
        return low

    def clearplayerselectionbuttons(self, canvas):
        '''
        This method unbinds the graph selection buttons from any event handlers and
        deletes them
        '''
        for b in self.playerbuttons:
            zb = self.playerbuttons[b]
            tag = 'playerbtn_' + str(zb[3])
            canvas.tag_unbind(tag, '<ButtonRelease-1>')
            canvas.delete(zb[1])
            canvas.delete(zb[2])
        self.playerbuttons = dict()

    def setupverticalaxis(self, canvas, left, top, right, bottom):
        '''
        This method draws the vertical axis of the graph, including tick marks.
        
        Note that the graph area itself extends from (left, top) to (right, bottom), but the graph marks extend
        to left - 4. It is up to the caller to ensure that the graphing area will not overlap
        
        The method returns the scaling factor to use on the vertical axis
        '''
        # determine minimum / maximum displayable value
        attr = self.graphbuttonlabels[self.selectedgraphcategory][1][self.selectedgraphitem][1]
        minval = getattr(self.demofile.teamstatistics[self.playerorder[0]][0], attr)
        maxval = minval
        for p in self.playerorder:
            for seq in self.demofile.teamstatistics[p]:
                v = getattr(seq, attr)
                if v > maxval:
                    maxval = v
                if v < minval:
                    minval = v

        # vertical axis
        id = canvas.create_line(left, top, 
            left, bottom,
            fill='#FFF',
            disabledfill='#EEE',
            state=Tix.DISABLED)
        self.verticalaxis.append(id)
        # first power of ten larger than maxval
        scale = 1.0
        power = 0
        while scale <= maxval:
            scale = scale * 10
            power = power + 1
        if maxval <= 0.9 * scale:
            power = power - 1
            ticks = 0.1 * scale
            digit = 0.1
            # print 'Max = ' + str(maxval) + ' Scale = ' + str(scale)
            while digit * scale < maxval:
                # print 'Max = ' + str(maxval) + ' Scale = ' + str(digit * scale)
                digit = digit + 0.1
            scale = digit * scale
            if digit <= 0.3:
                ticks = 0.5 * ticks
        else:
            ticks = 0.1 * scale
        if power >= 9:
            s = '%.0fG' % ( scale / 1e9 )
        elif power >= 6:
            s = '%.0fM' % ( scale / 1e6 )
        elif power >= 3:
            s = '%.0fk' % ( scale / 1e3 )
        else:
            s = '%.0f' % scale
        # print 'Scale = ' + str(scale) + ', power: ' + str(power) + ', ticks = ' + str(ticks) + ' minmax: ' + str(minval) + '-' + str(maxval)
        id = canvas.create_text(left + 2, top,
            anchor=Tix.NW, text=s,
            state=Tix.DISABLED,
            disabledfill='#EEE',
            fill='#FFF')
        self.verticalaxis.append(id)
        offset = ticks
        while offset <= scale:
            voffset = offset * ( top - bottom ) / scale
            # print 'Offset = ' + str(offset) + ' in units ' + str(voffset)
            id = canvas.create_line(left, bottom + offset *( top - bottom ) / scale,
                left - 4, bottom + offset * ( top - bottom ) / scale,
                fill='#FFF',
                disabledfill='#EEE',
                state=Tix.DISABLED)
            self.verticalaxis.append(id)
            id = canvas.create_line(left + 1, bottom + offset *( top - bottom ) / scale,
                right, bottom + offset * ( top - bottom ) / scale,
                fill='#444',
                disabledfill='#333',
                state=Tix.DISABLED)
            self.verticalaxis.append(id)
            offset = offset + ticks
        return scale
    
    def setuphorizontalaxis(self, canvas, left, top, right, bottom):
        '''
        Set up the horizontal axis of the graph, including tick marks.
        
        Note that the graph area itself extends from (left, top) to (right, bottom), but the graph marks extend
        to bottom + 5 + the height of a text string. It is up to the caller to ensure that the graphing area will not overlap
        
        The method returns the scaling factor to use on the horizontal axis
        '''
        id = canvas.create_line(left, bottom, 
            right, bottom,
            fill='#FFF',
            disabledfill='#EEE',
            state=Tix.DISABLED)
        self.horizontalaxis.append(id)

        # determine how to place tick marks on the horizontal axis.
        vlength = 0
        for p in self.playerorder:
            if len(self.demofile.teamstatistics[p]) > vlength:
                vlength = len(self.demofile.teamstatistics[p])
        vlength = vlength * self.demofile.teamstatperiod
        if vlength / 60 < 10:
            # one tick mark per minute
            tticks = 60
            l = '1m'
        elif vlength / 300 < 10:
            # one tick mark per 5 minutes
            tticks = 300
            l = '5m'
        elif vlength / 600 < 10:
            # one tick mark per 10 minutes
            tticks = 600
            l = '10m'
        elif vlength / 1800 < 10:
            # one tick mark per half hour (rare)
            tticks = 1800
            l = '30m'
        elif vlength / 3600 < 10:
            # one tick mark per hour (very rare)
            tticks = 3600
            l = '1h'
        elif vlength / 10800 < 10:
            # one tick mark per 3 hours (exceedingly rare)
            tticks = 10800
            l = '3h'
        else:
            # one tick mark per day if this all fails
            tticks = 86400
            l = '1d'
        offset = 0
        n = 1
        offset = tticks
        while offset <= vlength:
            voffset = offset * ( right - left ) / vlength
            # tick mark on the axis
            id = canvas.create_line(left + voffset, bottom,
                left + voffset, bottom + 4,
                fill='#FFF',
                disabledfill='#EEE',
                state=Tix.DISABLED)
            self.horizontalaxis.append(id)
            # grid line
            id = canvas.create_line(left + voffset, bottom - 1,
                left + voffset, top,
                fill='#444',
                disabledfill='#333',
                state=Tix.DISABLED)
            self.horizontalaxis.append(id)
            offset = offset + tticks
            if n == 1:
                id = canvas.create_text(left + voffset, bottom + 5, text=l, anchor=Tix.N,
                    fill='#FFF',
                    disabledfill='#EEE',
                    state=Tix.DISABLED)
                self.horizontalaxis.append(id)
            n = n + 1
        return vlength
    def drawgraph(self, canvas):
        '''
        Draws the graph itself
        '''
        xscale = self.setuphorizontalaxis(canvas, self.graphboxleft, self.graphboxtop, self.graphboxright, self.graphboxbottom)
        yscale = self.setupverticalaxis(canvas, self.graphboxleft, self.graphboxtop, self.graphboxright, self.graphboxbottom)
        attr = self.graphbuttonlabels[self.selectedgraphcategory][1][self.selectedgraphitem][1]
        # draw the graph for each player
        n = 0
        for p in self.playerorder:
            points = list()
            t = 0
            for values in self.demofile.teamstatistics[p]:
                v = getattr(values, attr)
                points.append(self.graphboxleft + t * ( self.graphboxright - self.graphboxleft ) / xscale)
                points.append(self.graphboxbottom + v * ( self.graphboxtop - self.graphboxbottom ) / yscale)
                t = t + self.demofile.teamstatperiod
            st = Tix.NORMAL
            for btn in self.playerbuttons:
                if self.playerbuttons[btn][0] == p:
                    if self.playerbuttons[btn][3] == False:
                        st = Tix.HIDDEN
                    break
            id = canvas.create_line(*points,
                state=st,
                disabledfill=self.playerbykey[p][0],
                fill=self.playerbykey[p][0])
            self.graphlines.append(id)
            n = n + 1
    
    def setupgraph(self, canvas, left, top, right, bottom):
        '''
        Dimensions and creates the graph
        '''
        # create a temporary text for dimensioning the graph axis and labelling
        id = canvas.create_text((left + right) / 2, (top + bottom)/2, text='Dpg', anchor=Tix.CENTER,
            fill='#FFF',
            disabledfill='#EEE',
            state=Tix.DISABLED)
        box = canvas.bbox(id)
        canvas.delete(id)
        self.graphboxleft = left + 6
        self.graphboxright = right - 2
        self.graphboxtop = top + 4
        self.graphboxbottom = bottom - 8 - ( box[3] - box[1] )
        self.drawgraph(canvas)
    
    def cleargraph(self, canvas):
        '''
        Clears the graph
        '''
        for id in self.graphlines:
            canvas.delete(id)
        for id in self.horizontalaxis:
            canvas.delete(id)
        for id in self.verticalaxis:
            canvas.delete(id)
        self.graphlines = list()
        self.horizontalaxis = list()
        self.verticalaxis = list()
            
    def drawteamstats(self, canvas):
        '''
        Draw on the teams stats canvas to display various graphs of performance

        The graph legend, consisting of the player names is displayed above the graph
        
        To the left of the graph, there is a series of buttons for selecting the graph to display
        
        The graph itself consists of two axes, horizontal for time, vertical for the element graphed
        
        Only the vertical axis is labelled with the quantity of the element graphed.
        
        
        '''
        # clear canvas
        self.cleargraphselectionbuttons(canvas)
        self.cleargraph(canvas)
        self.clearplayerselectionbuttons(canvas)
        for tag in canvas.find_all():
            canvas.delete(tag)
        if ( self.demofile == None or
            self.demofile.incomplete or self.demofile.crashed or
            self.demofile.teamstatistics == None):
            return
        # player selection buttons
        low = self.setupplayerselectionbuttons(canvas)
        # graph selection buttons
        self.setupgraphselectionbuttons(canvas)
        # the graph itself
        self.setupgraph(canvas, 200, low, int(self.canvas['width']), int(self.canvas['height']))
        
    def __showinfo(self):
        '''
        This method is invoked by the 'View|Game Information' menu option
        '''
        if self.currentview == 0:
            # do nothing
            return
        elif self.currentview == 2:
            self.cleargraph(self.canvas)
        self.currentview = 0
        self.drawgameinfo(self.canvas)
        
    def __showtable(self):
        '''
        This method is invoked by the 'View|Player Statistics' menu option
        '''
        if self.currentview == 1:
            # do nothing
            return
        elif self.currentview == 2:
            self.cleargraph(self.canvas)
        self.currentview = 1
        self.drawplayerstats(self.canvas)
        
        
    def __showgraph(self):
        '''
        This method is invoked by the 'View|Team Graph' menu option
        '''
        if self.currentview == 2:
            # do nothing
            return
        self.currentview = 2
        self.cleargraph(self.canvas)
        self.drawteamstats(self.canvas)
        
    def __showabout(self):
        '''
        This method is invoked by the 'Help|About' menu option
        '''
        text = 'Spring Stats Viewer\n\n'
        text += "Copyright (C) 2011  Rene van 't Veen\n\n"
        text += 'This program comes with ABSOLUTELY NO WARRANTY.\n'
        text += 'This is free software, and you are welcome to redistribute it\n'
        text += 'and/or modify it under the terms of the\n'
        text += 'GNU General Public License as published by\n'
        text += 'the Free Software Foundation, either version 3 of\n'
        text += 'the License, or (at your option) any later version.\n\n'
        text += 'Spring engine statistics are known to deviate substantially from\n'
        text += 'the information on which Zero-K bases its awards.\n\n'
        text += 'Version: ' + __version__ + '\n'
        text += 'Demo file reader version: ' + SpringDemoFile.__version__ + '\n'
        
        tkMessageBox.showinfo('About Spring Stats Viewer', text)
        
    def __redrawcanvas(self):
        '''
        This callback method is invoked after a resizing of the canvas and draws whatever
        is on it again, using the new dimensions.
        '''
        self.redrawscheduled = False
        if self.currentview == 0:
            self.drawgameinfo(self.canvas)
        elif self.currentview == 1:
            self.drawplayerstats(self.canvas)
        else:
            self.cleargraph(self.canvas)
            self.drawteamstats(self.canvas)
        
    def __canvasresized(self, event):
        '''
        Callback method that is invoked when the canvas is resized
        
        Resize the canvas and schedule a redraw in case the canvas is larger
        than the minimum area of 800 x 600
        '''
        cw = int(self.canvas['width'])
        ch = int(self.canvas['height'])
        if self.canvas.winfo_width() <= 800:
            # okay, canvas is clipped
            if cw == 800:
                w = None
            else:
                w = 800
        elif self.canvas.winfo_width() < self.canvas.winfo_reqwidth():
            # canvas is becoming smaller
            w = self.canvas.winfo_width() - ( self.canvas.winfo_reqwidth() - cw )
        elif self.canvas.winfo_width() > self.canvas.winfo_reqwidth():
            # canvas is becoming larger (wider)
            w = self.canvas.winfo_width() - ( self.canvas.winfo_reqwidth() - cw )
        else:
            # no size change horizontal
            w = None
        if self.canvas.winfo_height() <= 600:
            # okay, canvas is clipped
            if ch == 600:
                h = None
            else:
                h = 600
        elif self.canvas.winfo_height() < self.canvas.winfo_reqheight():
            # canvas is becoming smaller
            h = self.canvas.winfo_height() - ( self.canvas.winfo_reqheight() - ch )
        elif self.canvas.winfo_height() > self.canvas.winfo_reqheight():
            # canvas is becoming larger (taller)
            h = self.canvas.winfo_height() - ( self.canvas.winfo_reqheight() - ch )
        else:
            # no size change vertical
            h = None
            
        if w != None and h != None:
            # print 'Resizing canvas: w=' + str(event.width) + ' h=' + str(event.height)
            # print 'New canvas size: w=' + str(w) + ' h=' + str(h)
            self.canvas.configure(height=h, width=w)
            redraw = True
        elif w != None:
            # print 'Resizing canvas: w=' + str(event.width) + ' h=' + str(event.height)
            # print 'New canvas width: w=' + str(w)
            self.canvas.configure(width=w)
            redraw = True
        elif h != None:
            # print 'Resizing canvas: w=' + str(event.width) + ' h=' + str(event.height)
            # print 'New canvas height: h=' + str(h)
            self.canvas.configure(width=w)
            redraw = True
        else:
            # print 'Not resizing canvas: w=' + str(event.width) + ' h=' + str(event.height)
            # print 'Current canvas size: w=' + str(self.canvas['width']) + ' h=' + str(self.canvas['height'])
            redraw = False
        if redraw:
            if not self.redrawscheduled:
                self.canvas.after_idle(self.__redrawcanvas)
                self.redrawscheduled = True

    def __destroying(self, event):
        '''
        Callback method that is invoked when the user destroys the main window through the close
        button.
        
        The method just sets a flag that can be tested before the calling code attempts to destroy
        the main window (which it already is, if the user hits the close button)
        '''
        self.destroyed = True
        
    def isdestroyed(self):
        '''
        Returns true if the main window is already destroyed
        '''
        return self.destroyed
        
    def createWidgets(self):
        '''
        Create all the widgets in the apps main window
        '''
        
        # create the menubar
        top = self.winfo_toplevel()
        self.menuBar = Tix.Menu(top, tearoff=0)
        top["menu"] = self.menuBar
        # do some setup for resizing the window
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        self.rowconfigure(0, minsize=600, weight=1)
        self.columnconfigure(0, minsize=800, weight=1)
        # fill the menu bar
        self.menuFile = Tix.Menu(self.menuBar, tearoff=0)
        # index 0
        self.menuFile.add_command(label='Open', command=self.__open)
        # index 1
        self.menuFile.add_command(label='Close', command=self.__close)
        # index 2
        self.menuFile.add_command(label='Exit', command=self.__exit)
        self.menuBar.add_cascade(label='File',menu=self.menuFile)
        self.menuFile.entryconfigure(1, state=Tix.DISABLED)
        self.menuView = Tix.Menu(self.menuBar, tearoff=0)
        # index 0
        self.menuView.add_command(label='Game Info', command=self.__showinfo)
        # index 1
        self.menuView.add_command(label='Player Stats', command=self.__showtable)
        # index 2
        self.menuView.add_command(label='Team Graph', command=self.__showgraph)
        self.menuBar.add_cascade(label='View',menu=self.menuView)
        self.menuView.entryconfigure(1, state=Tix.DISABLED)
        self.menuView.entryconfigure(2, state=Tix.DISABLED)
        
        self.menuHelp = Tix.Menu(self.menuBar, tearoff=0)
        # index 0
        self.menuHelp.add_command(label='About', command=self.__showabout)
        self.menuBar.add_cascade(label='Help',menu=self.menuHelp)

        # create one canvas on which we draw everything
        self.canvas = Tix.Canvas(self,
            height=600, width=800, background='#000')
        self.canvas.grid(row=0, column=0, sticky=Tix.N + Tix.S + Tix.E + Tix.W)
        self.canvas.bind(sequence='<Configure>',func=self.__canvasresized)
        self.drawgameinfo(self.canvas)
        
        
    def __init__(self, master=None):
        '''
        Constructor for the main application demo
        '''
        
        self.demofile = None
        self.teams = dict()
        self.playerorder = list()
        self.playerbykey = dict()

        self.graphbuttonlabels = ( ( 'Metal', (
            ( 'Produced', 'metalProduced'),
            ( 'Used', 'metalUsed'),
            ( 'Excess', 'metalExcess'),
            ( 'Sent', 'metalSent'),
            ( 'Received', 'metalReceived'))), ( 'Energy', (
            ( 'Produced', 'energyProduced'),
            ( 'Used', 'energyUsed'),
            ( 'Excess', 'energyExcess'),
            ( 'Sent', 'energySent'),
            ( 'Received', 'energyReceived'))), ( 'Damage', (
            ( 'Dealt', 'damageDealt'),
            ( 'Received', 'damageReceived'))), ( 'Units', (
            ( 'Produced', 'unitsProduced'),
            ( 'Died', 'unitsDied'),
            ( 'Received', 'unitsReceived'),
            ( 'Sent', 'unitsSent'),
            ( 'Captured', 'unitsCaptured'),
            ( 'Stolen', 'unitsOutCaptured'))))
        
        self.selectedgraphcategory = 2
        self.selectedgraphitem = 0
        self.selectedgraphattribute = 'damageDealt'
        
        # view 0 is the game info
        # view 1 is the player stats
        # view 2 is the team graph
        self.currentview = 0
        
        self.redrawscheduled = False
            
        self.graphitembuttons = dict()
        self.graphcategorybuttons = dict()
        self.playerbuttons = dict()
        self.verticalaxis = list()
        self.horizontalaxis = list()
        self.graphlines = list()
            
        Tix.Frame.__init__(self, master)
        self.destroyed = False
        self.bind(sequence='<Destroy>',func=self.__destroying)
        self.grid(sticky=Tix.N + Tix.S + Tix.W + Tix.E)
        self.master.title('Spring Demo File Statistics Viewer')
        self.createWidgets()

if __name__ == '__main__':
    root = Tix.Tk()
    app = Application(master=root)
    if len(sys.argv)>0:
        app.openfile(sys.argv[1])
    app.mainloop()
    if not app.isdestroyed():
        root.destroy()

